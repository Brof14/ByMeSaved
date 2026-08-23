from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def confirm(note_id: int):
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="✅ Сохранить", callback_data=f"save:{note_id}"),
        InlineKeyboardButton(text="❌ Не сохранять", callback_data=f"drop:{note_id}"),
    )
    return b.as_markup()

def search_mode():
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="🔎 Искать", callback_data="search"))
    b.row(InlineKeyboardButton(text="📦 Экспорт Obsidian", callback_data="export"))
    return b.as_markup()
