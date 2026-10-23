import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter, TelegramAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from states.states import BroadcastStates
from database.crud import get_all_user_ids
from keyboards.admin_kb import (
    get_broadcast_confirm_kb,
    get_cancel_kb,
    get_admin_main_kb
)

router = Router(name="admin_broadcast_router")


@router.callback_query(F.data == "admin_broadcast")
async def start_broadcast(callback: CallbackQuery, state: FSMContext, is_admin: bool = False) -> None:
    """Ommaviy xabar yuborish jarayonini boshlash"""
    if not is_admin:
        await callback.answer("Kirish huquqi yo'q!", show_alert=True)
        return

    await state.set_state(BroadcastStates.waiting_for_message)
    text = (
        "📢 <b>Ommaviy xabar yuborish (Broadcast)</b>\n\n"
        "Barcha bot foydalanuvchilariga yubormoqchi bo'lgan xabaringizni yozib yoki "
        "media (rasm, fayl, video) ko'rinishida yuboring:\n\n"
        "<i>(Xabarni to'g'ridan-to'g'ri forward qilishingiz ham mumkin)</i>"
    )
    try:
        await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=get_cancel_kb())
    except Exception:
        await callback.message.answer(text=text, parse_mode="HTML", reply_markup=get_cancel_kb())
    await callback.answer()


@router.message(BroadcastStates.waiting_for_message)
async def process_broadcast_message(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """Yuboriladigan xabarni saqlash va ko'rib chiqish (preview)"""
    user_ids = await get_all_user_ids(session)

    await state.update_data(
        from_chat_id=message.chat.id,
        broadcast_message_id=message.message_id,
        recipients_count=len(user_ids)
    )
    await state.set_state(BroadcastStates.confirm)

    preview_text = (
        "📋 <b>Xabar ko'rinishi yuqorida qabul qilindi.</b>\n\n"
        f"👥 <b>Yuboriladigan foydalanuvchilar soni:</b> {len(user_ids)} nafar\n\n"
        "Haqiqatan ham ushbu xabarni barcha foydalanuvchilarga yuborishni tasdiqlaysizmi?"
    )
    await message.reply(
        text=preview_text,
        parse_mode="HTML",
        reply_markup=get_broadcast_confirm_kb()
    )


@router.callback_query(BroadcastStates.confirm, F.data == "broadcast_send_confirm")
async def confirm_and_send_broadcast(
    callback: CallbackQuery,
    bot: Bot,
    session: AsyncSession,
    state: FSMContext,
    is_admin: bool = False
) -> None:
    """Xabarni barcha foydalanuvchilarga xavfsiz va tezkor yuborish"""
    if not is_admin:
        await callback.answer("Kirish huquqi yo'q!", show_alert=True)
        return

    data = await state.get_data()
    from_chat_id = data.get("from_chat_id")
    message_id = data.get("broadcast_message_id")

    if not from_chat_id or not message_id:
        await state.clear()
        await callback.message.answer("Xatolik: xabar topilmadi.", reply_markup=get_admin_main_kb())
        return

    user_ids = await get_all_user_ids(session)
    total_users = len(user_ids)

    await state.clear()
    await callback.message.edit_text(
        f"⏳ <b>Xabar yuborish boshlandi...</b>\nJami: {total_users} ta foydalanuvchi.",
        parse_mode="HTML"
    )

    success_count = 0
    blocked_count = 0
    error_count = 0

    for user_id in user_ids:
        try:
            await bot.copy_message(
                chat_id=user_id,
                from_chat_id=from_chat_id,
                message_id=message_id
            )
            success_count += 1
            # Telegram flood limitsdan himoyalanish (sekundiga ~25 xabar)
            await asyncio.sleep(0.04)
        except TelegramForbiddenError:
            # Foydalanuvchi botni bloklagan
            blocked_count += 1
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            try:
                await bot.copy_message(
                    chat_id=user_id,
                    from_chat_id=from_chat_id,
                    message_id=message_id
                )
                success_count += 1
            except Exception:
                error_count += 1
        except TelegramAPIError:
            error_count += 1
        except Exception:
            error_count += 1

    report_text = (
        "✅ <b>Ommaviy xabar yuborish yakunlandi!</b>\n\n"
        f"📊 <b>Natijalar:</b>\n"
        f"• Yetkazildi: <b>{success_count}</b> ta\n"
        f"• Botni bloklaganlar: <b>{blocked_count}</b> ta\n"
        f"• Xatoliklar: <b>{error_count}</b> ta\n"
        f"• Jami qamrov: <b>{total_users}</b> ta"
    )
    await callback.message.answer(
        text=report_text,
        parse_mode="HTML",
        reply_markup=get_admin_main_kb()
    )
    await callback.answer()
