from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from states.states import AddBookStates, EditBookStates
from database.crud import (
    add_book,
    get_all_books,
    get_book_by_id,
    update_book,
    delete_book
)
from keyboards.admin_kb import (
    get_admin_main_kb,
    get_book_confirm_kb,
    get_cancel_kb,
    get_admin_books_list_kb,
    get_book_management_actions_kb,
    get_delete_confirm_kb
)

router = Router(name="admin_books_router")


# ==============================================================
# 1. ➕ KITOB QO'SHISH (FSM)
# ==============================================================

@router.callback_query(F.data == "admin_add_book")
async def start_add_book(callback: CallbackQuery, state: FSMContext, is_admin: bool = False) -> None:
    """1-qadam: Kitob nomini so'rash"""
    if not is_admin:
        await callback.answer("Kirish huquqi yo'q!", show_alert=True)
        return

    await state.set_state(AddBookStates.title)
    text = (
        "➕ <b>Yangi kitob qo'shish</b>\n\n"
        "<b>1-qadam:</b> Kitob nomini kiriting (masalan: <i>O'tkan kunlar</i>):"
    )
    try:
        await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=get_cancel_kb())
    except Exception:
        await callback.message.answer(text=text, parse_mode="HTML", reply_markup=get_cancel_kb())
    await callback.answer()


@router.message(AddBookStates.title, F.text)
async def process_book_title(message: Message, state: FSMContext) -> None:
    """2-qadam: Muallif ismini so'rash"""
    title = message.text.strip()
    if len(title) > 255:
        await message.answer("⚠️ Kitob nomi juda uzun (maksimal 255 belgi). Qisqaroq qilib qayta kiriting:")
        return

    await state.update_data(book_title=title)
    await state.set_state(AddBookStates.author)
    await message.answer(
        text=f"Kitob nomi: <b>{title}</b> qabul qilindi.\n\n<b>2-qadam:</b> Muallifning ism-sharifini kiriting:",
        parse_mode="HTML",
        reply_markup=get_cancel_kb()
    )


@router.message(AddBookStates.author, F.text)
async def process_book_author(message: Message, state: FSMContext) -> None:
    """3-qadam: Kitob muqovasi (rasm) so'rash"""
    author = message.text.strip()
    if len(author) > 255:
        await message.answer("⚠️ Muallif ismi juda uzun (maksimal 255 belgi). Qayta kiriting:")
        return

    await state.update_data(book_author=author)
    await state.set_state(AddBookStates.photo)
    await message.answer(
        text=(
            f"Muallif: <b>{author}</b> qabul qilindi.\n\n"
            "<b>3-qadam:</b> Kitob muqovasi (rasmini) yuboring:"
        ),
        parse_mode="HTML",
        reply_markup=get_cancel_kb()
    )


@router.message(AddBookStates.photo, F.photo)
async def process_book_photo(message: Message, state: FSMContext) -> None:
    """4-qadam: Kitob tavsifini (annotatsiyasini) so'rash"""
    # Telegramdagi eng yuqori sifatli rasm file_id sini olamiz
    photo_file_id = message.photo[-1].file_id
    await state.update_data(photo_file_id=photo_file_id)

    await state.set_state(AddBookStates.description)
    await message.answer(
        text=(
            "Muqova rasmi qabul qilindi! ✅\n\n"
            "<b>4-qadam:</b> Kitobning qisqacha mazmunini (annotatsiyasini) yozing:\n"
            "<i>(Diqqat: Telegram caption chegarasi sababli matn 950 belgidan oshmasligi kerak!)</i>"
        ),
        parse_mode="HTML",
        reply_markup=get_cancel_kb()
    )


@router.message(AddBookStates.photo)
async def invalid_book_photo(message: Message) -> None:
    """Noto'g'ri fayl yuborilganda ogohlantirish"""
    await message.answer("⚠️ Iltimos, kitob muqovasining rasmini (foto) yuboring!", reply_markup=get_cancel_kb())


@router.message(AddBookStates.description, F.text)
async def process_book_description(message: Message, state: FSMContext) -> None:
    """5-qadam: Kitob PDF faylini so'rash (950 belgi cheklovi bilan)"""
    desc = message.text.strip()

    # TZ xavfsizlik talabi: caption 1024 belgi bo'lgani sababli tavsif 950 belgidan oshmasligi shart
    if len(desc) > 950:
        await message.answer(
            text=(
                f"⚠️ Tavsif juda uzun ({len(desc)} belgi)!\n"
                "Telegram chegarasi buzilmasligi uchun tavsif <b>950 belgidan oshmasligi kerak</b>.\n"
                "Iltimos, matnni qisqartirib qayta yuboring:"
            ),
            parse_mode="HTML",
            reply_markup=get_cancel_kb()
        )
        return

    await state.update_data(book_description=desc)
    await state.set_state(AddBookStates.pdf)
    await message.answer(
        text=(
            "Tavsif qabul qilindi! ✅\n\n"
            "<b>5-qadam:</b> Kitobning <b>PDF faylini</b> (hujjat sifatida) yuboring:"
        ),
        parse_mode="HTML",
        reply_markup=get_cancel_kb()
    )


@router.message(AddBookStates.pdf, F.document)
async def process_book_pdf(message: Message, state: FSMContext) -> None:
    """Yakuniy qadam: PDF faylni qabul qilish va ma'lumotlarni ko'rsatib tasdiqlashni so'rash"""
    doc = message.document

    # Fayl turi tekshiruvi (.pdf yoki application/pdf)
    is_pdf = False
    if doc.mime_type and "pdf" in doc.mime_type.lower():
        is_pdf = True
    elif doc.file_name and doc.file_name.lower().endswith(".pdf"):
        is_pdf = True

    if not is_pdf:
        await message.answer("⚠️ Iltimos, faqat <b>PDF formatidagi</b> fayl yuboring!", parse_mode="HTML", reply_markup=get_cancel_kb())
        return

    pdf_file_id = doc.file_id
    await state.update_data(pdf_file_id=pdf_file_id)

    data = await state.get_data()
    title = data["book_title"]
    author = data["book_author"]
    photo_file_id = data["photo_file_id"]
    description = data["book_description"]

    await state.set_state(AddBookStates.confirm)

    preview_caption = (
        "📋 <b>Kitob ma'lumotlarini tekshiring:</b>\n\n"
        f"📖 <b>Kitob nomi:</b> {title}\n"
        f"✍️ <b>Muallif:</b> {author}\n\n"
        f"📝 <b>Qisqacha mazmuni:</b>\n{description}\n\n"
        f"📁 <b>Fayl:</b> {doc.file_name or 'kitob.pdf'}\n\n"
        "Ma'lumotlar to'g'ri bo'lsa, 'Saqlash' tugmasini bosing:"
    )

    try:
        await message.answer_photo(
            photo=photo_file_id,
            caption=preview_caption,
            parse_mode="HTML",
            reply_markup=get_book_confirm_kb()
        )
    except Exception:
        await message.answer(
            text=preview_caption,
            parse_mode="HTML",
            reply_markup=get_book_confirm_kb()
        )


@router.message(AddBookStates.pdf)
async def invalid_book_pdf(message: Message) -> None:
    await message.answer("⚠️ Iltimos, kitobning <b>PDF faylini</b> yuboring!", parse_mode="HTML", reply_markup=get_cancel_kb())


@router.callback_query(AddBookStates.confirm, F.data == "confirm_save_book")
async def save_book_to_db(callback: CallbackQuery, session: AsyncSession, state: FSMContext, is_admin: bool = False) -> None:
    """Kitobni ma'lumotlar bazasiga saqlash"""
    if not is_admin:
        await callback.answer("Kirish huquqi yo'q!", show_alert=True)
        return

    data = await state.get_data()
    title = data["book_title"]
    author = data["book_author"]
    description = data["book_description"]
    photo_file_id = data["photo_file_id"]
    pdf_file_id = data["pdf_file_id"]

    book = await add_book(
        session=session,
        title=title,
        author=author,
        description=description,
        photo_file_id=photo_file_id,
        pdf_file_id=pdf_file_id
    )

    await state.clear()
    await callback.message.answer(
        text=f"🎉 <b>Kitob muvaffaqiyatli saqlandi!</b>\n\nID: <code>{book.id}</code>\nNomi: <b>{book.title}</b>",
        parse_mode="HTML",
        reply_markup=get_admin_main_kb()
    )
    await callback.answer()


# ==============================================================
# 2. ✏️ KITOBLARNI BOSHQARISH VA O'CHIRISH
# ==============================================================

@router.callback_query(F.data == "admin_books_list")
async def list_admin_books(callback: CallbackQuery, session: AsyncSession, state: FSMContext, is_admin: bool = False) -> None:
    """Admin uchun barcha kitoblar ro'yxatini chiqarish"""
    await state.clear()
    if not is_admin:
        await callback.answer("Kirish huquqi yo'q!", show_alert=True)
        return

    page = 1
    per_page = 6
    books, total_count = await get_all_books(session=session, limit=per_page, offset=0)

    if total_count == 0:
        text = "📚 Hozircha bazada kitoblar mavjud emas."
        try:
            await callback.message.edit_text(text=text, reply_markup=get_admin_books_list_kb([], 1, 0))
        except Exception:
            await callback.message.answer(text=text, reply_markup=get_admin_books_list_kb([], 1, 0))
        await callback.answer()
        return

    text = f"📚 <b>Baza kitoblari ro'yxati</b> (Jami: {total_count} ta):"
    try:
        await callback.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=get_admin_books_list_kb(books=books, page=page, total_count=total_count, per_page=per_page)
        )
    except Exception:
        await callback.message.answer(
            text=text,
            parse_mode="HTML",
            reply_markup=get_admin_books_list_kb(books=books, page=page, total_count=total_count, per_page=per_page)
        )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_books_page:"))
async def page_admin_books(callback: CallbackQuery, session: AsyncSession, is_admin: bool = False) -> None:
    """Kitoblar ro'yxatida sahifalash"""
    if not is_admin:
        await callback.answer("Kirish huquqi yo'q!", show_alert=True)
        return

    page = int(callback.data.split(":")[1])
    per_page = 6
    offset = (page - 1) * per_page
    books, total_count = await get_all_books(session=session, limit=per_page, offset=offset)

    text = f"📚 <b>Baza kitoblari ro'yxati</b> (Jami: {total_count} ta):"
    try:
        await callback.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=get_admin_books_list_kb(books=books, page=page, total_count=total_count, per_page=per_page)
        )
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data.startswith("view_admin_book:"))
async def view_admin_book_actions(callback: CallbackQuery, session: AsyncSession, is_admin: bool = False) -> None:
    """Tanlangan kitob ma'lumotlari va tahrirlash/o'chirish tugmalari"""
    if not is_admin:
        await callback.answer("Kirish huquqi yo'q!", show_alert=True)
        return

    book_id = int(callback.data.split(":")[1])
    book = await get_book_by_id(session, book_id)

    if not book:
        await callback.answer("Kitob topilmadi!", show_alert=True)
        return

    text = (
        f"📖 <b>Kitob ma'lumotlari:</b>\n"
        f"ID: <code>{book.id}</code>\n"
        f"Nomi: <b>{book.title}</b>\n"
        f"Muallif: <b>{book.author}</b>\n"
        f"Yuklab olingan: <b>{book.downloads_count} marta</b>\n\n"
        f"📝 <b>Tavsif:</b>\n{book.description}\n\n"
        "Tahrirlash uchun tegishli tugmani tanlang:"
    )

    try:
        await callback.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=get_book_management_actions_kb(book.id)
        )
    except Exception:
        await callback.message.answer(
            text=text,
            parse_mode="HTML",
            reply_markup=get_book_management_actions_kb(book.id)
        )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_field:"))
async def prompt_edit_field(callback: CallbackQuery, state: FSMContext, is_admin: bool = False) -> None:
    """Tahrirlash uchun yangi qiymat so'rash"""
    if not is_admin:
        await callback.answer("Kirish huquqi yo'q!", show_alert=True)
        return

    parts = callback.data.split(":")
    book_id = int(parts[1])
    field = parts[2]

    await state.set_state(EditBookStates.waiting_new_value)
    await state.update_data(edit_book_id=book_id, edit_field=field)

    field_names = {
        "title": "yangi nomini",
        "author": "yangi muallifini",
        "description": "yangi tavsifini (950 belgidan oshmasin)",
        "photo": "yangi muqova rasmini (foto)",
        "pdf": "yangi PDF faylini"
    }

    prompt = f"Iltimos, kitobning {field_names.get(field, field)} yuboring:"
    try:
        await callback.message.edit_text(text=prompt, reply_markup=get_cancel_kb())
    except Exception:
        await callback.message.answer(text=prompt, reply_markup=get_cancel_kb())
    await callback.answer()


@router.message(EditBookStates.waiting_new_value)
async def process_field_edit(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """Tahrirlangan qiymatni qabul qilib saqlash"""
    data = await state.get_data()
    book_id = data.get("edit_book_id")
    field = data.get("edit_field")

    if not book_id or not field:
        await state.clear()
        await message.answer("Xatolik yuz berdi. Qaytadan urinib ko'ring.", reply_markup=get_admin_main_kb())
        return

    update_kwargs = {}

    if field in ["title", "author"]:
        if not message.text:
            await message.answer("⚠️ Iltimos, matn yuboring!", reply_markup=get_cancel_kb())
            return
        update_kwargs[field] = message.text.strip()

    elif field == "description":
        if not message.text:
            await message.answer("⚠️ Iltimos, tavsif matnini yuboring!", reply_markup=get_cancel_kb())
            return
        desc = message.text.strip()
        if len(desc) > 950:
            await message.answer(
                f"⚠️ Tavsif 950 belgidan oshmasligi kerak (hozir {len(desc)} belgi). Qayta yuboring:",
                reply_markup=get_cancel_kb()
            )
            return
        update_kwargs["description"] = desc

    elif field == "photo":
        if not message.photo:
            await message.answer("⚠️ Iltimos, rasm yuboring!", reply_markup=get_cancel_kb())
            return
        update_kwargs["photo_file_id"] = message.photo[-1].file_id

    elif field == "pdf":
        if not message.document:
            await message.answer("⚠️ Iltimos, PDF hujjat yuboring!", reply_markup=get_cancel_kb())
            return
        doc = message.document
        is_pdf = (doc.mime_type and "pdf" in doc.mime_type.lower()) or (doc.file_name and doc.file_name.lower().endswith(".pdf"))
        if not is_pdf:
            await message.answer("⚠️ Faqat PDF formatdagi fayl qabul qilinadi!", reply_markup=get_cancel_kb())
            return
        update_kwargs["pdf_file_id"] = doc.file_id

    await update_book(session, book_id, **update_kwargs)
    await state.clear()

    await message.answer(
        text=f"✅ Kitobning <b>{field}</b> maydoni muvaffaqiyatli yangilandi!",
        parse_mode="HTML",
        reply_markup=get_admin_main_kb()
    )


@router.callback_query(F.data.startswith("delete_book_prompt:"))
async def prompt_delete_book(callback: CallbackQuery, session: AsyncSession, is_admin: bool = False) -> None:
    """Kitobni o'chirishdan oldin tasdiqlash so'rash"""
    if not is_admin:
        await callback.answer("Kirish huquqi yo'q!", show_alert=True)
        return

    book_id = int(callback.data.split(":")[1])
    book = await get_book_by_id(session, book_id)

    if not book:
        await callback.answer("Kitob topilmadi!", show_alert=True)
        return

    text = (
        f"⚠️ <b>Haqiqatan ham ushbu kitobni o'chirmoqchimisiz?</b>\n\n"
        f"📖 <b>{book.title}</b> ({book.author})\n"
        "Bu amalni ortga qaytarib bo'lmaydi!"
    )
    try:
        await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=get_delete_confirm_kb(book.id))
    except Exception:
        await callback.message.answer(text=text, parse_mode="HTML", reply_markup=get_delete_confirm_kb(book.id))
    await callback.answer()


@router.callback_query(F.data.startswith("delete_book_confirm:"))
async def confirm_delete_book(callback: CallbackQuery, session: AsyncSession, is_admin: bool = False) -> None:
    """Kitobni bazadan butunlay o'chirish"""
    if not is_admin:
        await callback.answer("Kirish huquqi yo'q!", show_alert=True)
        return

    book_id = int(callback.data.split(":")[1])
    success = await delete_book(session, book_id)

    if success:
        text = "🗑 <b>Kitob muvaffaqiyatli o'chirildi!</b>"
    else:
        text = "⚠️ Kitobni o'chirishda xatolik yuz berdi yoki kitob topilmadi."

    try:
        await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=get_admin_main_kb())
    except Exception:
        await callback.message.answer(text=text, parse_mode="HTML", reply_markup=get_admin_main_kb())
    await callback.answer()
