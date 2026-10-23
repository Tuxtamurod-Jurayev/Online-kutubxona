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
    get_top_downloaded_books,
    clean_phone
)
from keyboards.admin_kb import (
    get_admin_main_kb
)
from keyboards.user_kb import (
    get_phone_auth_kb,
    get_start_kb
)

router = Router(name="admin_panel_router")


def get_admin_dashboard_text(user) -> str:
    username_str = f"@{user.username}" if user.username else "<i>Mavjud emas</i>"
    return (
        "⚡️ <b>ADMINISTRATOR BOSHQARUV PANELI</b> 👑\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Admin:</b> {user.full_name}\n"
        f"🆔 <b>Telegram ID:</b> <code>{user.id}</code>\n"
        f"🌐 <b>Username:</b> {username_str}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Quyidagi boshqaruv bo'limlaridan birini tanlang:"
    )


@router.message(Command("admin", "panel"))
@router.message(F.text.lower().in_(["admin", "panel", "/admin", "/panel"]))
async def cmd_admin(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    is_admin: bool = False
) -> None:
    """
    /admin yoki 'admin' xabari kelganda:
    1. Agar admin bo'lsa -> Darhol boshqaruv paneli ochiladi.
    2. Agar admin bo'lmasa -> Telefon raqamini tasdiqlash taklif etiladi.
    """
    await state.clear()

    if is_admin:
        await message.answer(
            text=get_admin_dashboard_text(message.from_user),
            parse_mode="HTML",
            reply_markup=get_admin_main_kb()
        )
        return

    # Foydalanuvchi hozircha tanilmagan bo'lsa
    auth_prompt = (
        "🔒 <b>ADMINISTRATORLIKNI TASDIQLASH</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Sizning Telegram ID raqamingiz (<code>{message.from_user.id}</code>) ro'yxatdan topilmadi.\n\n"
        "Agar siz <b>telefon raqamingiz</b> orqali admin qilib kiritilgan bo'lsangiz:\n"
        "1️⃣ Pastdagi <b>[ 📱 Telefon raqamni yuborish ]</b> tugmasini bosing\n"
        "2️⃣ Yoki raqamingizni shu yerga yozib yuboring (masalan: <code>+998930406364</code>)"
    )
    await message.answer(
        text=auth_prompt,
        parse_mode="HTML",
        reply_markup=get_phone_auth_kb()
    )


@router.message(F.contact)
async def process_admin_contact(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """
    Kontakt tugmasi orqali yuborilgan telefon raqamini tekshirish
    """
    contact = message.contact

    admin = await check_and_link_admin_by_phone(
        session=session,
        telegram_id=message.from_user.id,
        phone_number=contact.phone_number,
        username=message.from_user.username
    )

    if admin:
        await message.answer(
            text=(
                "✅ <b>Telefon raqamingiz muvaffaqiyatli tasdiqlandi!</b>\n"
                "Sizning Telegram hisobingiz adminlar safiga biriktirildi. 🎉"
            ),
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()
        )
        await message.answer(
            text=get_admin_dashboard_text(message.from_user),
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


@router.message(F.text.regexp(r"^\+?[0-9\s\-\(\)]{9,15}$"))
async def process_admin_text_phone(message: Message, session: AsyncSession, state: FSMContext, is_admin: bool = False) -> None:
    """
    Foydalanuvchi telefon raqamini matn sifatida yozib yuborganida tekshirish
    """
    if is_admin:
        # Agar allaqachon admin bo'lsa boshqa xabarlar uchun xalaqit bermaydi
        return

    phone_input = message.text.strip()
    admin = await check_and_link_admin_by_phone(
        session=session,
        telegram_id=message.from_user.id,
        phone_number=phone_input,
        username=message.from_user.username
    )

    if admin:
        await message.answer(
            text=(
                f"✅ <b>Telefon raqam ({phone_input}) tasdiqlandi!</b>\n"
                "Siz administrator sifatida tanildingiz! 🎉"
            ),
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()
        )
        await message.answer(
            text=get_admin_dashboard_text(message.from_user),
            parse_mode="HTML",
            reply_markup=get_admin_main_kb()
        )
    else:
        # Agar oddiy foydalanuvchi bo'lsa
        pass


@router.message(F.text == "❌ Bekor qilish")
async def cancel_contact_auth(message: Message, state: FSMContext, is_admin: bool = False) -> None:
    """Kontakt yuborishni bekor qilish"""
    await state.clear()
    await message.answer(
        text="❌ Bekor qilindi.",
        reply_markup=ReplyKeyboardRemove()
    )
    from handlers.user import get_welcome_text
    await message.answer(
        text=get_welcome_text(message.from_user.full_name),
        parse_mode="HTML",
        reply_markup=get_start_kb(is_admin=is_admin)
    )


@router.callback_query(F.data == "admin_back_to_menu")
async def back_to_admin_menu(callback: CallbackQuery, state: FSMContext, is_admin: bool = False) -> None:
    """Admin bosh menyusiga qaytish"""
    await state.clear()
    if not is_admin:
        await callback.answer("⚠️ Kirish huquqi yo'q!", show_alert=True)
        return

    text = get_admin_dashboard_text(callback.from_user)
    try:
        await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=get_admin_main_kb())
    except Exception:
        await callback.message.answer(text=text, parse_mode="HTML", reply_markup=get_admin_main_kb())
    await callback.answer()


@router.callback_query(F.data == "cancel_admin_action")
async def cancel_admin_action(callback: CallbackQuery, state: FSMContext) -> None:
    """Joriy admin amalini bekor qilish"""
    await state.clear()
    text = (
        "❌ <b>Jarayon bekor qilindi.</b>\n\n"
        + get_admin_dashboard_text(callback.from_user)
    )
    try:
        await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=get_admin_main_kb())
    except Exception:
        await callback.message.answer(text=text, parse_mode="HTML", reply_markup=get_admin_main_kb())
    await callback.answer()


@router.callback_query(F.data == "admin_close")
async def close_admin_panel(callback: CallbackQuery, state: FSMContext, is_admin: bool = False) -> None:
    """Admin panelini yopish va foydalanuvchi holatiga qaytish"""
    await state.clear()
    from handlers.user import get_welcome_text
    text = get_welcome_text(callback.from_user.full_name)
    try:
        await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=get_start_kb(is_admin=is_admin))
    except Exception:
        await callback.message.answer(text=text, parse_mode="HTML", reply_markup=get_start_kb(is_admin=is_admin))
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
        await callback.answer("⚠️ Kirish huquqi yo'q!", show_alert=True)
        return

    users_count = await get_users_count(session)
    new_users_24h = await get_new_users_count_24h(session)
    books_count = await get_books_count(session)
    total_downloads = await get_total_downloads(session)
    top_books = await get_top_downloaded_books(session, limit=5)

    stats_text = (
        "📊 <b>BOTNING TO'LIQ STATISTIKASI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 <b>Jami kitobxonlar:</b> <code>{users_count:,}</code> nafar\n"
        f"🆕 <b>Oxirgi 24 soatda qo'shilganlar:</b> <code>{new_users_24h}</code> nafar\n"
        f"📚 <b>Bazadagi jami kitoblar:</b> <code>{books_count}</code> ta\n"
        f"📥 <b>Jami yuklab olishlar:</b> <code>{total_downloads:,}</code> marta\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔥 <b>Eng ko'p yuklab olingan Top-5 kitob:</b>\n\n"
    )

    if top_books:
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        for i, b in enumerate(top_books):
            m = medals[i] if i < len(medals) else "📖"
            stats_text += f"{m} <b>{b.title}</b> ({b.author})\n    ↳ 📥 <i>{b.downloads_count} marta yuklangan</i>\n"
    else:
        stats_text += "<i>Hozircha kitoblar yuklab olinmagan.</i>\n"

    stats_text += "━━━━━━━━━━━━━━━━━━━━━━"

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚡️ Admin bosh menyu", callback_data="admin_back_to_menu")]
        ]
    )

    try:
        await callback.message.edit_text(text=stats_text, parse_mode="HTML", reply_markup=kb)
    except Exception:
        await callback.message.answer(text=stats_text, parse_mode="HTML", reply_markup=kb)

    await callback.answer()
