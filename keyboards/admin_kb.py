from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import Admin, Book


def get_admin_main_kb() -> InlineKeyboardMarkup:
    """Admin boshqaruv panelining asosiy menyusi"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Kitob qo'shish", callback_data="admin_add_book"),
                InlineKeyboardButton(text="✏️ Kitoblarni boshqarish", callback_data="admin_books_list")
            ],
            [
                InlineKeyboardButton(text="👥 Adminlar boshqaruvi", callback_data="admin_manage_admins"),
                InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")
            ],
            [
                InlineKeyboardButton(text="📢 Xabar yuborish (Broadcast)", callback_data="admin_broadcast")
            ],
            [
                InlineKeyboardButton(text="🔙 Foydalanuvchi rejimi", callback_data="admin_close")
            ]
        ]
    )


def get_book_confirm_kb() -> InlineKeyboardMarkup:
    """Kitob ma'lumotlari kiritilgach tasdiqlash tugmalari"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Saqlash", callback_data="confirm_save_book"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_admin_action")
            ]
        ]
    )


def get_cancel_kb() -> InlineKeyboardMarkup:
    """Har qanday jarayonni bekor qilish tugmasi"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_admin_action")
            ]
        ]
    )


def get_book_management_actions_kb(book_id: int) -> InlineKeyboardMarkup:
    """Tanlangan kitob ustida amallar (Tahrirlash / O'chirish)"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Nomi", callback_data=f"edit_field:{book_id}:title"),
                InlineKeyboardButton(text="✍️ Muallif", callback_data=f"edit_field:{book_id}:author")
            ],
            [
                InlineKeyboardButton(text="📝 Tavsif", callback_data=f"edit_field:{book_id}:description"),
                InlineKeyboardButton(text="🖼 Rasm", callback_data=f"edit_field:{book_id}:photo")
            ],
            [
                InlineKeyboardButton(text="📄 PDF fayl", callback_data=f"edit_field:{book_id}:pdf")
            ],
            [
                InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"delete_book_prompt:{book_id}")
            ],
            [
                InlineKeyboardButton(text="🔙 Kitoblar ro'yxatiga", callback_data="admin_books_list")
            ]
        ]
    )


def get_delete_confirm_kb(book_id: int) -> InlineKeyboardMarkup:
    """Kitobni o'chirishni tasdiqlash"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🗑 Ha, o'chirilsin", callback_data=f"delete_book_confirm:{book_id}"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"view_admin_book:{book_id}")
            ]
        ]
    )


def get_admin_books_list_kb(books: List[Book], page: int, total_count: int, per_page: int = 6) -> InlineKeyboardMarkup:
    """Admin uchun kitoblar ro'yxati va paginatsiya"""
    buttons = []
    start_index = (page - 1) * per_page

    for i, book in enumerate(books, start=start_index + 1):
        btn_text = f"📖 {book.title} ({book.author})"
        if len(btn_text) > 60:
            btn_text = btn_text[:57] + "..."
        buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"view_admin_book:{book.id}")])

    total_pages = (total_count + per_page - 1) // per_page
    nav_buttons = []
    if total_pages > 1:
        if page > 1:
            nav_buttons.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"admin_books_page:{page-1}"))
        nav_buttons.append(InlineKeyboardButton(text=f"📄 {page}/{total_pages}", callback_data="noop"))
        if page < total_pages:
            nav_buttons.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"admin_books_page:{page+1}"))
        buttons.append(nav_buttons)

    buttons.append([
        InlineKeyboardButton(text="➕ Yangi kitob qo'shish", callback_data="admin_add_book"),
        InlineKeyboardButton(text="🔙 Admin menyu", callback_data="admin_back_to_menu")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_manage_kb() -> InlineKeyboardMarkup:
    """Adminlarni boshqarish bosh menyusi"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Yangi admin qo'shish", callback_data="add_admin_prompt")
            ],
            [
                InlineKeyboardButton(text="📋 Adminlar ro'yxati", callback_data="list_admins")
            ],
            [
                InlineKeyboardButton(text="🔙 Admin menyu", callback_data="admin_back_to_menu")
            ]
        ]
    )


def get_admins_list_kb(admins: List[Admin], current_user_id: int) -> InlineKeyboardMarkup:
    """Adminlar ro'yxati va ularni o'chirish tugmalari"""
    buttons = []
    for admin in admins:
        label = ""
        if admin.username:
            label += f"@{admin.username} "
        if admin.telegram_id:
            label += f"ID: {admin.telegram_id} "
        if admin.phone_number:
            label += f"Tel: +{admin.phone_number}"

        if not label.strip():
            label = f"Admin #{admin.id}"

        # O'zini o'zi o'chirib qo'ymaslik tekshiruvi
        if admin.telegram_id == current_user_id:
            buttons.append([
                InlineKeyboardButton(text=f"👑 {label} (Siz)", callback_data="noop")
            ])
        else:
            buttons.append([
                InlineKeyboardButton(text=f"👤 {label}", callback_data="noop"),
                InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"delete_admin:{admin.id}")
            ])

    buttons.append([
        InlineKeyboardButton(text="➕ Yangi admin", callback_data="add_admin_prompt"),
        InlineKeyboardButton(text="🔙 Ortga", callback_data="admin_manage_admins")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_broadcast_confirm_kb() -> InlineKeyboardMarkup:
    """Ommaviy xabarni tasdiqlash tugmalari"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🚀 Yuborish", callback_data="broadcast_send_confirm"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_admin_action")
            ]
        ]
    )
