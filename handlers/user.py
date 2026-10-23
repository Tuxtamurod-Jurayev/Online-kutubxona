from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud import (
    upsert_user,
    search_books,
    get_book_by_id,
    increment_downloads,
    get_top_downloaded_books,
    get_books_count,
    get_users_count
)
from states.states import BookSearchStates
from keyboards.user_kb import (
    get_start_kb,
    get_retry_search_kb,
    get_single_book_kb,
    get_search_results_kb,
    get_top_books_kb
)
from keyboards.admin_kb import get_admin_main_kb

router = Router(name="user_router")


def get_welcome_text(full_name: str) -> str:
    """Interaktiv qutlov matni"""
    return (
        f"👋 <b>Assalomu alaykum, {full_name}!</b>\n\n"
        "📚 <b>Elektron kutubxona botimizga xush kelibsiz!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Bu yerda siz o'zingizga kerakli o'zbek va jahon adabiyoti durdonalari, "
        "ilmiy, biznes hamda badiiy kitoblarning <b>elektron (PDF)</b> holatini bir zumda topishingiz mumkin.\n\n"
        "⚡️ <b>Imkoniyatlar:</b>\n"
        "• 🔍 Kitob nomi yoki muallif bo'yicha tezkor qidiruv\n"
        "• 📖 Kitob haqida qisqacha ma'lumot va muqovasi\n"
        "• 📥 To'liq PDF variantini 1 soniyada yuklab olish\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👇 <i>Kerakli bo'limni tanlang:</i>"
    )


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession, state: FSMContext, is_admin: bool = False) -> None:
    """
    /start buyrug'i:
    1. Foydalanuvchi ma'lumotlari bazaga saqlanadi.
    2. Chiroyli interaktiv qutlov matni va tugmalar taqdim etiladi.
    """
    await state.clear()

    await upsert_user(
        session=session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name
    )

    text = get_welcome_text(message.from_user.full_name)
    await message.answer(text=text, parse_mode="HTML", reply_markup=get_start_kb(is_admin=is_admin))


@router.callback_query(F.data == "back_to_home")
async def back_to_home(callback: CallbackQuery, state: FSMContext, is_admin: bool = False) -> None:
    """Bosh menyuga qaytish"""
    await state.clear()
    text = get_welcome_text(callback.from_user.full_name)
    try:
        await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=get_start_kb(is_admin=is_admin))
    except Exception:
        await callback.message.answer(text=text, parse_mode="HTML", reply_markup=get_start_kb(is_admin=is_admin))
    await callback.answer()


@router.callback_query(F.data == "admin_open_from_start")
async def admin_open_from_start(callback: CallbackQuery, state: FSMContext, is_admin: bool = False) -> None:
    """Bosh menyudagi admin tugmasi orqali admin panelga o'tish"""
    await state.clear()
    if not is_admin:
        await callback.answer("⚠️ Kechirasiz, sizda admin huquqi yo'q!", show_alert=True)
        return

    admin_text = (
        "⚡️ <b>ADMINISTRATOR BOSHQARUV PANELI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Admin:</b> {callback.from_user.full_name}\n"
        f"🆔 <b>Telegram ID:</b> <code>{callback.from_user.id}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Kerakli bo'limni tanlang:"
    )
    try:
        await callback.message.edit_text(text=admin_text, parse_mode="HTML", reply_markup=get_admin_main_kb())
    except Exception:
        await callback.message.answer(text=admin_text, parse_mode="HTML", reply_markup=get_admin_main_kb())
    await callback.answer()


@router.callback_query(F.data == "search_book")
async def start_search(callback: CallbackQuery, state: FSMContext) -> None:
    """Qidiruv rejimini boshlash (FSM)"""
    await state.set_state(BookSearchStates.waiting_for_query)
    text = (
        "🔍 <b>Kitob qidirish</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Iltimos, qidirayotgan kitobingiz <b>nomini</b> yoki <b>muallif ism-sharifini</b> yozib yuboring:\n\n"
        "💡 <i>Masalan: <code>O'tkan kunlar</code> yoki <code>Abdulla Qodiriy</code></i>"
    )
    try:
        await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=get_retry_search_kb())
    except Exception:
        await callback.message.answer(text=text, parse_mode="HTML", reply_markup=get_retry_search_kb())
    await callback.answer()


@router.message(BookSearchStates.waiting_for_query, F.text)
async def process_search_query(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """Foydalanuvchi kiritgan so'rov bo'yicha kitoblarni qidirish"""
    query = message.text.strip()
    if not query:
        await message.answer("⚠️ Iltimos, kitob nomi yoki muallif ismini matn ko'rinishida yozing.")
        return

    await state.update_data(search_query=query, current_page=1)
    books, total_count = await search_books(session=session, query=query, limit=5, offset=0)

    # 1. Agar kitob topilmasa
    if total_count == 0:
        await state.clear()
        not_found_text = (
            "😕 <b>Afsuski, so'rovingiz bo'yicha kitob topilmadi!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔎 So'rov: <i>«{query}»</i>\n\n"
            "💡 <b>Tavsiyalar:</b>\n"
            "• So'zlarni imlo xatolarisiz yozishga harakat qiling.\n"
            "• Faqat kitob nomining asosiy qismini yozib ko'ring.\n"
            "• Yoki faqat muallif familiyasini kiriting."
        )
        await message.answer(text=not_found_text, parse_mode="HTML", reply_markup=get_retry_search_kb())
        return

    # 2. Agar aynan 1 ta kitob topilsa
    if total_count == 1:
        await state.clear()
        book = books[0]
        caption = (
            f"📖 <b>{book.title}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✍️ <b>Muallif:</b> {book.author}\n"
            f"📥 <b>Yuklab olingan:</b> {book.downloads_count} marta\n\n"
            f"📝 <b>Qisqacha mazmuni:</b>\n{book.description}\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "👇 <i>Kitobni yuklab olish uchun tugmani bosing:</i>"
        )
        try:
            await message.answer_photo(
                photo=book.photo_file_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=get_single_book_kb(book.id)
            )
        except Exception:
            await message.answer(
                text=caption,
                parse_mode="HTML",
                reply_markup=get_single_book_kb(book.id)
            )
        return

    # 3. Agar bir nechta kitob topilsa
    results_text = (
        "📚 <b>Qidiruv natijalari:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔎 So'rov: <i>«{query}»</i>\n"
        f"📊 Jami topildi: <b>{total_count} ta kitob</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Kerakli kitobni tanlang:"
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
        await callback.answer("Qidiruv muddati o'tgan. Iltimos, qaytadan qidiring.", show_alert=True)
        return

    per_page = 5
    offset = (page - 1) * per_page
    books, total_count = await search_books(session=session, query=query, limit=per_page, offset=offset)

    await state.update_data(current_page=page)

    results_text = (
        "📚 <b>Qidiruv natijalari:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔎 So'rov: <i>«{query}»</i>\n"
        f"📊 Jami topildi: <b>{total_count} ta kitob</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Kerakli kitobni tanlang:"
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
    """Tanlangan kitob haqida to'liq kartochkani chiqarish"""
    book_id = int(callback.data.split(":")[1])
    book = await get_book_by_id(session, book_id)

    if not book:
        await callback.answer("Kechirasiz, ushbu kitob bazadan topilmadi.", show_alert=True)
        return

    caption = (
        f"📖 <b>{book.title}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✍️ <b>Muallif:</b> {book.author}\n"
        f"📥 <b>Yuklab olingan:</b> {book.downloads_count} marta\n\n"
        f"📝 <b>Qisqacha mazmuni:</b>\n{book.description}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👇 <i>Kitobni yuklab olish uchun tugmani bosing:</i>"
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
    """Kitobning PDF faylini foydalanuvchiga yuborish"""
    book_id = int(callback.data.split(":")[1])
    book = await get_book_by_id(session, book_id)

    if not book:
        await callback.answer("⚠️ Kechirasiz, kitob fayli topilmadi.", show_alert=True)
        return

    # Yuklab olishlar sonini 1 taga oshiramiz
    downloads = await increment_downloads(session, book_id)

    await callback.answer("📥 Kitob yuborilmoqda, kuting...", show_alert=False)

    doc_caption = (
        f"📖 <b>{book.title}</b>\n"
        f"✍️ <i>{book.author}</i>\n"
        f"📥 Jami yuklashlar: <b>{downloads} marta</b>\n\n"
        "✨ <i>Foydali va maroqli mutolaa tilaymiz!</i>\n"
        "🤖 @online_libraries_bot"
    )
    try:
        await callback.message.answer_document(
            document=book.pdf_file_id,
            caption=doc_caption,
            parse_mode="HTML"
        )
    except Exception as e:
        await callback.message.answer(f"⚠️ Kitob faylini yuborishda xatolik yuz berdi: {str(e)}")


@router.callback_query(F.data == "top_books")
async def show_top_books(callback: CallbackQuery, session: AsyncSession) -> None:
    """Eng ko'p yuklangan top kitoblarni chiqarish"""
    top_books = await get_top_downloaded_books(session, limit=5)

    if not top_books:
        text = (
            "🔥 <b>Eng ommabop kitoblar</b>\n\n"
            "Hozircha bazada yuklab olingan kitoblar mavjud emas.\n"
            "Birinchi bo'lib kitob qidiring va mutolaa qiling!"
        )
        try:
            await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=get_retry_search_kb())
        except Exception:
            await callback.message.answer(text=text, parse_mode="HTML", reply_markup=get_retry_search_kb())
        await callback.answer()
        return

    text = (
        "🔥 <b>ENG KO'P O'QILGAN TOP KITOBLAR</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Kitobxonlarimiz tomonidan eng ko'p yuklab olingan sara asarlar:\n\n"
        "Batafsil ma'lumot va yuklab olish uchun kitobni tanlang:"
    )
    try:
        await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=get_top_books_kb(top_books))
    except Exception:
        await callback.message.answer(text=text, parse_mode="HTML", reply_markup=get_top_books_kb(top_books))
    await callback.answer()


@router.callback_query(F.data == "about_bot")
async def show_about_bot(callback: CallbackQuery, session: AsyncSession, is_admin: bool = False) -> None:
    """Bot haqida batafsil ma'lumot"""
    b_count = await get_books_count(session)
    u_count = await get_users_count(session)

    about_text = (
        "ℹ️ <b>BOT HAQIDA MA'LUMOT</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>Elektron Kutubxona Boti</b> — kitobxonlar uchun tezkor va bepul kitob qidiruv xizmati.\n\n"
        f"📊 <b>Statistika:</b>\n"
        f"• 📚 Bazadagi kitoblar: <b>{b_count} ta</b>\n"
        f"• 👥 Faol kitobxonlar: <b>{u_count} nafar</b>\n"
        "• ⚡️ Qidiruv tezligi: <b>0.1 soniya</b>\n\n"
        "✨ <i>Kitob — insonning eng yaqin do'sti va ma'naviy boyligidir.</i>\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    )
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Kitob qidirish", callback_data="search_book")],
            [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="back_to_home")]
        ]
    )
    try:
        await callback.message.edit_text(text=about_text, parse_mode="HTML", reply_markup=kb)
    except Exception:
        await callback.message.answer(text=about_text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "noop")
async def process_noop(callback: CallbackQuery) -> None:
    """Statik tugmalar bosilganda hech narsa qilmaslik"""
    await callback.answer()
