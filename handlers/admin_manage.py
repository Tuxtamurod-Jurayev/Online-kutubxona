from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from states.states import AdminManageStates
from database.crud import (
    get_all_admins,
    add_new_admin,
    delete_admin,
    clean_username,
    clean_phone
)
from keyboards.admin_kb import (
    get_admin_manage_kb,
    get_admins_list_kb,
    get_cancel_kb,
    get_admin_main_kb
)

router = Router(name="admin_manage_router")


@router.callback_query(F.data == "admin_manage_admins")
async def show_admin_manage_menu(callback: CallbackQuery, state: FSMContext, is_admin: bool = False) -> None:
    """Adminlarni boshqarish menyusi"""
    await state.clear()
    if not is_admin:
        await callback.answer("⚠️ Kirish huquqi yo'q!", show_alert=True)
        return

    text = (
        "👥 <b>ADMINISTRATORLARNI BOSHQARISH</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Ushbu bo'lim orqali siz:\n"
        "• Yangi adminlarni qo'shishingiz (ID, @username yoki telefon raqam orqali)\n"
        "• Mavjud barcha adminlar ro'yxatini ko'rishingiz\n"
        "• Keraksiz adminlarni tizimdan o'chirishingiz mumkin.\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Kerakli bo'limni tanlang:"
    )
    try:
        await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=get_admin_manage_kb())
    except Exception:
        await callback.message.answer(text=text, parse_mode="HTML", reply_markup=get_admin_manage_kb())
    await callback.answer()


@router.callback_query(F.data == "list_admins")
async def show_admins_list(callback: CallbackQuery, session: AsyncSession, is_admin: bool = False) -> None:
    """Mavjud barcha adminlar ro'yxati"""
    if not is_admin:
        await callback.answer("⚠️ Kirish huquqi yo'q!", show_alert=True)
        return

    admins = await get_all_admins(session)
    text = (
        "📋 <b>BARCHA ADMINISTRATORLAR RO'YXATI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 Jami adminlar: <b>{len(admins)} nafar</b>\n\n"
        "O'chirmoqchi bo'lsangiz yonidagi 'O'chirish' tugmasini bosing:"
    )

    try:
        await callback.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=get_admins_list_kb(admins=admins, current_user_id=callback.from_user.id)
        )
    except Exception:
        await callback.message.answer(
            text=text,
            parse_mode="HTML",
            reply_markup=get_admins_list_kb(admins=admins, current_user_id=callback.from_user.id)
        )
    await callback.answer()


@router.callback_query(F.data == "add_admin_prompt")
async def prompt_add_admin(callback: CallbackQuery, state: FSMContext, is_admin: bool = False) -> None:
    """Yangi admin kiritish so'rovi"""
    if not is_admin:
        await callback.answer("⚠️ Kirish huquqi yo'q!", show_alert=True)
        return

    await state.set_state(AdminManageStates.waiting_for_admin_input)
    prompt_text = (
        "➕ <b>YANGI ADMIN QO'SHISH</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Quyidagi 3 ta usuldan birida ma'lumot yuboring:\n\n"
        "1️⃣ <b>Telegram ID:</b> masalan <code>123456789</code>\n"
        "2️⃣ <b>Username:</b> masalan <code>@foydalanuvchi_nik</code>\n"
        "3️⃣ <b>Telefon raqami:</b> masalan <code>+998901234567</code>\n\n"
        "💡 <i>Eslatma: Agar @username yoki telefon raqam kiritsangiz, "
        "admin botga birinchi marta murojaat qilganida uning Telegram ID raqami avtomatik bog'lanadi.</i>"
    )
    try:
        await callback.message.edit_text(text=prompt_text, parse_mode="HTML", reply_markup=get_cancel_kb())
    except Exception:
        await callback.message.answer(text=prompt_text, parse_mode="HTML", reply_markup=get_cancel_kb())
    await callback.answer()


@router.message(AdminManageStates.waiting_for_admin_input, F.text)
async def process_add_admin_input(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """Kiritilgan ma'lumotni aniqlab, admin sifatida saqlash"""
    val = message.text.strip()

    telegram_id = None
    username = None
    phone_number = None

    if val.startswith("@"):
        username = clean_username(val)
    elif val.startswith("+") or (val.startswith("998") and len(val) == 12):
        phone_number = clean_phone(val)
    elif val.isdigit():
        if len(val) == 12 and val.startswith("998"):
            phone_number = val
        else:
            telegram_id = int(val)
    else:
        username = clean_username(val)

    try:
        admin = await add_new_admin(
            session=session,
            telegram_id=telegram_id,
            username=username,
            phone_number=phone_number
        )
        await state.clear()

        info = []
        if admin.telegram_id:
            info.append(f"🆔 Telegram ID: <code>{admin.telegram_id}</code>")
        if admin.username:
            info.append(f"🌐 Username: @{admin.username}")
        if admin.phone_number:
            info.append(f"📱 Telefon: +{admin.phone_number}")

        await message.answer(
            text=(
                "🎉 <b>Yangi admin muvaffaqiyatli biriktirildi!</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                + "\n".join(info)
            ),
            parse_mode="HTML",
            reply_markup=get_admin_main_kb()
        )
    except Exception as e:
        await message.answer(
            text=f"⚠️ Admin qo'shishda xatolik yuz berdi:\n{str(e)}",
            reply_markup=get_cancel_kb()
        )


@router.callback_query(F.data.startswith("delete_admin:"))
async def process_delete_admin(callback: CallbackQuery, session: AsyncSession, is_admin: bool = False) -> None:
    """Adminni o'chirish"""
    if not is_admin:
        await callback.answer("⚠️ Kirish huquqi yo'q!", show_alert=True)
        return

    admin_id = int(callback.data.split(":")[1])
    success = await delete_admin(session, admin_id)

    if success:
        await callback.answer("✅ Admin muvaffaqiyatli o'chirildi!", show_alert=True)
    else:
        await callback.answer("⚠️ Admin topilmadi yoki o'chirilmadi.", show_alert=True)

    admins = await get_all_admins(session)
    text = (
        "📋 <b>BARCHA ADMINISTRATORLAR RO'YXATI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 Jami adminlar: <b>{len(admins)} nafar</b>\n\n"
        "O'chirmoqchi bo'lsangiz yonidagi 'O'chirish' tugmasini bosing:"
    )

    try:
        await callback.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=get_admins_list_kb(admins=admins, current_user_id=callback.from_user.id)
        )
    except Exception:
        pass
