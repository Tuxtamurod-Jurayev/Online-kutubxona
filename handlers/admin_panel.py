from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud import (
    check_and_link_admin_by_phone,
    get_users_count,
    get_new_users_count_24h,
    get_books_count,
    get_total_downloads,
    get_top_downloaded_books
)
from keyboards.admin_kb import (
    get_admin_main_kb
)
from keyboards.user_kb import (
    get_phone_auth_kb,
    get_start_kb
)

router = Router(name="admin_panel_router")


@router.message(Command("admin"))
async def cmd_admin(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    is_admin: bool = False
) -> None:
    """
    /admin buyrug'i:
    1. Agar foydalanuvchi ID yoki username orqali tanilgan bo'lsa -> to'g'ridan-to'g'ri admin panel ochiladi.
    2. Agar tanilmagan bo'lsa -> telefon raqami orqali autentifikatsiya so'raladi.
    """
    await state.clear()

    if is_admin:
        await message.answer(
            text=(
                "👨‍💻 <b>Administrator boshqaruv paneli</b>\n\n"
                "Quyidagi bo'limlardan birini tanlang:"
            ),
            parse_mode="HTML",
            reply_markup=get_admin_main_kb()
        )
        return

    # Foydalanuvchi admin sifatida tanilmagan bo'lsa - telefon raqamini so'raymiz
    auth_prompt = (
        "🔒 <b>Admin autentifikatsiyasi</b>\n\n"
        "Sizning Telegram ID yoki username'ingiz adminlar ro'yxatidan topilmadi.\n\n"
        "Agar telefon raqamingiz orqali admin qilib kiritilgan bo'lsangiz, "
        "pastdagi <b>[ 📱 Raqamni tasdiqlash ]</b> tugmasini bosing:"
    )
    await message.answer(
        text=auth_prompt,
        parse_mode="HTML",
        reply_markup=get_phone_auth_kb()
    )


@router.message(F.contact)
async def process_admin_contact(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """
    Admin bo'lish uchun yuborilgan kontaktni tekshirish (3-usul: phone_number)
    """
    contact = message.contact

    # Xavfsizlik tekshiruvi: yuborilgan kontakt foydalanuvchining o'ziniki bo'lishi shart
    if contact.user_id != message.from_user.id:
        await message.answer(
            text="⚠️ Iltimos, faqat o'zingizning telefon raqamingizni pastdagi tugma orqali yuboring!",
            reply_markup=get_phone_auth_kb()
        )
        return

    admin = await check_and_link_admin_by_phone(
        session=session,
        telegram_id=message.from_user.id,
        phone_number=contact.phone_number
    )

    if admin:
        await message.answer(
            text="✅ <b>Telefon raqamingiz tasdiqlandi!</b>\nTelegram hisobingiz adminlar safiga muvaffaqiyatli bog'landi.",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()
        )
        await message.answer(
            text=(
                "👨‍💻 <b>Administrator boshqaruv paneli</b>\n\n"
                "Quyidagi bo'limlardan birini tanlang:"
            ),
            parse_mode="HTML",
            reply_markup=get_admin_main_kb()
        )
    else:
        await message.answer(
            text=(
                f"❌ Kechirasiz, <code>+{contact.phone_number}</code> raqami adminlar ro'yxatida mavjud emas.\n"
                "Bosh admin bilan bog'laning."
            ),
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()
        )


@router.message(F.text == "❌ Bekor qilish")
async def cancel_contact_auth(message: Message, state: FSMContext) -> None:
    """Kontakt yuborishni bekor qilish"""
    await state.clear()
    await message.answer(
        text="Bekor qilindi.",
        reply_markup=ReplyKeyboardRemove()
    )
    await message.answer(
        text="Assalomu alaykum! Bu yerda o'zingizga kerakli kitobning elektron holatini topishingiz mumkin.",
        reply_markup=get_start_kb()
    )


@router.callback_query(F.data == "admin_back_to_menu")
async def back_to_admin_menu(callback: CallbackQuery, state: FSMContext, is_admin: bool = False) -> None:
    """Admin bosh menyusiga qaytish"""
    await state.clear()
    if not is_admin:
        await callback.answer("Kirish huquqi yo'q!", show_alert=True)
        return

    text = (
        "👨‍💻 <b>Administrator boshqaruv paneli</b>\n\n"
        "Quyidagi bo'limlardan birini tanlang:"
    )
    try:
        await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=get_admin_main_kb())
    except Exception:
        await callback.message.answer(text=text, parse_mode="HTML", reply_markup=get_admin_main_kb())
    await callback.answer()


@router.callback_query(F.data == "cancel_admin_action")
async def cancel_admin_action(callback: CallbackQuery, state: FSMContext) -> None:
    """Joriy admin amalini bekor qilish va bosh menyuga qaytish"""
    await state.clear()
    text = (
        "❌ Amal bekor qilindi.\n\n"
        "👨‍💻 <b>Administrator boshqaruv paneli:</b>"
    )
    try:
        await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=get_admin_main_kb())
    except Exception:
        await callback.message.answer(text=text, parse_mode="HTML", reply_markup=get_admin_main_kb())
    await callback.answer()


@router.callback_query(F.data == "admin_close")
async def close_admin_panel(callback: CallbackQuery, state: FSMContext) -> None:
    """Admin panelini yopish va foydalanuvchi holatiga qaytish"""
    await state.clear()
    text = "Assalomu alaykum! Bu yerda o'zingizga kerakli kitobning elektron holatini topishingiz mumkin."
    try:
        await callback.message.edit_text(text=text, reply_markup=get_start_kb())
    except Exception:
        await callback.message.answer(text=text, reply_markup=get_start_kb())
    await callback.answer()


@router.callback_query(F.data == "admin_stats")
async def show_statistics(callback: CallbackQuery, session: AsyncSession, is_admin: bool = False) -> None:
    """
    2.2 (4-band) Statistika bo'limi:
    - Jami foydalanuvchilar soni
    - So'nggi 24 soatdagi yangi foydalanuvchilar
    - Bazadagi jami kitoblar soni
    - Jami yuklab olishlar soni
    - Eng ko'p yuklangan top kitoblar
    """
    if not is_admin:
        await callback.answer("Kirish huquqi yo'q!", show_alert=True)
        return

    users_count = await get_users_count(session)
    new_users_24h = await get_new_users_count_24h(session)
    books_count = await get_books_count(session)
    total_downloads = await get_total_downloads(session)
    top_books = await get_top_downloaded_books(session, limit=5)

    stats_text = (
        "📊 <b>BOT STATISTIKASI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 <b>Jami foydalanuvchilar:</b> {users_count} nafar\n"
        f"🆕 <b>So'nggi 24 soatda qo'shilganlar:</b> {new_users_24h} nafar\n"
        f"📚 <b>Bazadagi jami kitoblar:</b> {books_count} ta\n"
        f"📥 <b>Jami yuklab olishlar:</b> {total_downloads} marta\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔥 <b>Eng ko'p yuklab olingan Top-5 kitob:</b>\n"
    )

    if top_books:
        for i, b in enumerate(top_books, start=1):
            stats_text += f"{i}. <b>{b.title}</b> ({b.author}) — <i>{b.downloads_count} marta</i>\n"
    else:
        stats_text += "<i>Hozircha kitoblar yuklab olinmagan.</i>\n"

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Admin menyu", callback_data="admin_back_to_menu")]
        ]
    )

    try:
        await callback.message.edit_text(text=stats_text, parse_mode="HTML", reply_markup=kb)
    except Exception:
        await callback.message.answer(text=stats_text, parse_mode="HTML", reply_markup=kb)

    await callback.answer()
