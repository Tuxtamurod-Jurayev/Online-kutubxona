from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud import (
    upsert_user,
    search_books,
    get_book_by_id,
    increment_downloads
)
from states.states import BookSearchStates
from keyboards.user_kb import (
    get_start_kb,
    get_retry_search_kb,
    get_single_book_kb,
    get_search_results_kb
)

router = Router(name="user_router")


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """
    /start buyrug'i:
    1. Foydalanuvchi ma'lumotlari bazaga saqlanadi.
    2. Qutlov matni va 'Kitobni izlash' inline tugmasi yuboriladi.
    """
    await state.clear()

    # Foydalanuvchini bazaga yozish / yangilash
    await upsert_user(
        session=session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name
    )

    text = "Assalomu alaykum! Bu yerda o'zingizga kerakli kitobning elektron holatini topishingiz mumkin."
    await message.answer(text=text, reply_markup=get_start_kb())


@router.callback_query(F.data == "search_book")
async def start_search(callback: CallbackQuery, state: FSMContext) -> None:
    """Qidiruv rejimini boshlash (FSM holatini o'rnatish)"""
    await state.set_state(BookSearchStates.waiting_for_query)
    text = "Iltimos, qidirayotgan kitobingiz nomini yoki muallifning ism-sharifini yozib yuboring:"
    await callback.message.answer(text=text)
    await callback.answer()


@router.message(BookSearchStates.waiting_for_query, F.text)
async def process_search_query(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """Foydalanuvchi kiritgan so'rov bo'yicha kitoblarni qidirish"""
    query = message.text.strip()
    if not query:
        await message.answer("Iltimos, qidiruv uchun kitob nomi yoki muallif ismini yozing.")
        return

    # Qidiruv parametrlarini saqlash
    await state.update_data(search_query=query, current_page=1)

    books, total_count = await search_books(session=session, query=query, limit=5, offset=0)

    # 1. Agar kitob topilmasa
    if total_count == 0:
        await state.clear()
        not_found_text = "Kechirasiz, so'rovingiz bo'yicha kitob topilmadi. Imlo xatolarisiz qayta yozib ko'ring."
        await message.answer(text=not_found_text, reply_markup=get_retry_search_kb())
        return

    # 2. Agar aynan 1 ta kitob topilsa
    if total_count == 1:
        await state.clear()
        book = books[0]
        caption = (
            f"📖 <b>Kitob nomi:</b> {book.title}\n"
            f"✍️ <b>Muallif:</b> {book.author}\n\n"
            f"📝 <b>Qisqacha mazmuni:</b>\n{book.description}"
        )
        try:
            await message.answer_photo(
                photo=book.photo_file_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=get_single_book_kb(book.id)
            )
        except Exception:
            # Agar rasm yuborishda muammo bo'lsa matn ko'rinishida yuboriladi
            await message.answer(
                text=caption,
                parse_mode="HTML",
                reply_markup=get_single_book_kb(book.id)
            )
        return

    # 3. Agar bir nechta kitob topilsa
    results_text = (
        f"🔍 <b>Qidiruv natijalari</b> (so'rov: <i>{query}</i>):\n"
        f"Jami topildi: <b>{total_count} ta</b> kitob.\n\n"
        f"Kerakli kitobni tanlang:"
    )
    await message.answer(
        text=results_text,
        parse_mode="HTML",
        reply_markup=get_search_results_kb(books=books, total_count=total_count, page=1, per_page=5, query=query)
    )


@router.callback_query(F.data.startswith("page:"))
async def process_pagination(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    """Qidiruv natijalarida sahifalash (Paginatsiya)"""
    page = int(callback.data.split(":")[1])
    data = await state.get_data()
    query = data.get("search_query")

    if not query:
        await callback.answer("Qidiruv muddati tugagan. Qaytadan qidiring.", show_alert=True)
        return

    per_page = 5
    offset = (page - 1) * per_page
    books, total_count = await search_books(session=session, query=query, limit=per_page, offset=offset)

    await state.update_data(current_page=page)

    results_text = (
        f"🔍 <b>Qidiruv natijalari</b> (so'rov: <i>{query}</i>):\n"
        f"Jami topildi: <b>{total_count} ta</b> kitob.\n\n"
        f"Kerakli kitobni tanlang:"
    )

    try:
        await callback.message.edit_text(
            text=results_text,
            parse_mode="HTML",
            reply_markup=get_search_results_kb(books=books, total_count=total_count, page=page, per_page=per_page, query=query)
        )
    except Exception:
        pass

    await callback.answer()


@router.callback_query(F.data.startswith("view_book:"))
async def view_book_details(callback: CallbackQuery, session: AsyncSession) -> None:
    """Tanlangan bitta kitob haqida to'liq ma'lumot va PDF yuklab olish tugmasini chiqarish"""
    book_id = int(callback.data.split(":")[1])
    book = await get_book_by_id(session, book_id)

    if not book:
        await callback.answer("Kechirasiz, bu kitob bazadan topilmadi.", show_alert=True)
        return

    caption = (
        f"📖 <b>Kitob nomi:</b> {book.title}\n"
        f"✍️ <b>Muallif:</b> {book.author}\n\n"
        f"📝 <b>Qisqacha mazmuni:</b>\n{book.description}"
    )

    try:
        await callback.message.answer_photo(
            photo=book.photo_file_id,
            caption=caption,
            parse_mode="HTML",
            reply_markup=get_single_book_kb(book.id)
        )
    except Exception:
        await callback.message.answer(
            text=caption,
            parse_mode="HTML",
            reply_markup=get_single_book_kb(book.id)
        )

    await callback.answer()


@router.callback_query(F.data.startswith("download_pdf:"))
async def download_book_pdf(callback: CallbackQuery, session: AsyncSession) -> None:
    """Kitobning PDF faylini foydalanuvchiga yuborish va yuklashlar sonini oshirish"""
    book_id = int(callback.data.split(":")[1])
    book = await get_book_by_id(session, book_id)

    if not book:
        await callback.answer("Kechirasiz, ushbu kitob fayli topilmadi.", show_alert=True)
        return

    # Yuklab olishlar sonini 1 taga oshiramiz
    await increment_downloads(session, book_id)

    await callback.answer("📥 Kitob yuborilmoqda, kuting...")

    doc_caption = f"📖 <b>{book.title}</b>\n✍️ <i>{book.author}</i>\n\nMutolaa muborak bo'lsin!"
    try:
        await callback.message.answer_document(
            document=book.pdf_file_id,
            caption=doc_caption,
            parse_mode="HTML"
        )
    except Exception as e:
        await callback.message.answer(f"⚠️ Kitob faylini yuborishda xatolik yuz berdi: {str(e)}")


@router.callback_query(F.data == "noop")
async def process_noop(callback: CallbackQuery) -> None:
    """Statik tugmalar bosilganda hech narsa qilmaslik"""
    await callback.answer()
