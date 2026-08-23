from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, FSInputFile

from app.ai.openrouter import OpenRouter
from app.bot.keyboards import confirm, search_mode
from app.db import repository as repo
from app.export.obsidian import export_user
from app.config import settings

router = Router()
_ai: OpenRouter | None = None
_waiting: dict[int, str] = {}
_pending: dict[int, dict] = {}


def setup_ai(ai: OpenRouter):
    global _ai
    _ai = ai


def ai() -> OpenRouter:
    if _ai is None:
        raise RuntimeError("AI is not initialized")
    return _ai


@router.message(CommandStart())
async def start(message: Message):
    await repo.upsert_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    await message.answer(
        "<b>Personal Knowledge Bot</b>\n\n"
        "Пересылай полезные сообщения или отправляй текст. Я предложу сохранить их, а затем AI автоматически добавит тему, теги, summary и вектор для поиска.\n\n"
        "<b>Команды</b>\n/search — поиск\n/ask — вопрос к базе\n/categories — темы\n/stats — статистика\n/export — Markdown для Obsidian\n/help — помощь",
        reply_markup=search_mode(),
    )


@router.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer(
        "Перешли сообщение → «✅ Сохранить».\n\n"
        "/search → семантический поиск.\n"
        "/ask → AI отвечает на вопрос по сохранённым материалам.\n"
        "/categories → распределение по темам.\n"
        "/stats → статистика.\n"
        "/export → ZIP с .md-файлами для Obsidian."
    )


@router.message(Command("search"))
async def search_cmd(message: Message):
    _waiting[message.from_user.id] = "search"
    await message.answer("🔎 Напиши поисковый запрос.")


@router.message(Command("ask"))
async def ask_cmd(message: Message):
    _waiting[message.from_user.id] = "ask"
    await message.answer("🧠 Напиши вопрос к своей базе знаний.")


@router.message(Command("categories"))
async def categories(message: Message):
    rows = await repo.list_category_counts(message.from_user.id)
    if not rows:
        await message.answer("Пока нет сохранений.")
        return
    text = "📚 <b>Темы</b>\n\n" + "\n".join(
        f"• {r['category'] or 'other'} — {r['count']}" for r in rows
    )
    await message.answer(text)


@router.message(Command("stats"))
async def stats(message: Message):
    count = await repo.count_notes(message.from_user.id)
    await message.answer(f"📚 Сохранений: <b>{count}</b>")


@router.message(Command("export"))
async def export_cmd(message: Message):
    await message.answer("📦 Собираю экспорт…")
    archive = await export_user(message.from_user.id)
    await message.answer_document(FSInputFile(archive), caption="Obsidian export")


@router.callback_query(F.data == "search")
async def search_button(call: CallbackQuery):
    await call.answer()
    _waiting[call.from_user.id] = "search"
    await call.message.answer("🔎 Напиши поисковый запрос.")


@router.callback_query(F.data == "export")
async def export_button(call: CallbackQuery):
    await call.answer("Готовлю экспорт…")
    archive = await export_user(call.from_user.id)
    await call.message.answer_document(FSInputFile(archive), caption="Obsidian export")


@router.callback_query(F.data.startswith("save:"))
async def confirm_save(call: CallbackQuery):
    user_id = call.from_user.id
    note_key = int(call.data.split(":")[1])
    pending = _pending.pop(note_key, None)
    if not pending or pending["user_id"] != user_id:
        await call.answer("Сохранение устарело", show_alert=True)
        return

    note_id = await repo.create_note(
        user_id,
        pending["content"],
        pending["source_chat_id"],
        pending["source_message_id"],
        pending["source_url"],
    )
    await call.answer("Сохранено")
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer(f"✅ Сохранено как #{note_id}. Обрабатываю AI…")
    try:
        await process_note(note_id, pending["content"])
        await call.message.answer(f"✅ #{note_id}: готово к поиску.")
    except Exception:
        await call.message.answer(f"⚠️ #{note_id}: текст сохранён, но AI-обработка не завершилась. Можно обработать позже.")


@router.callback_query(F.data.startswith("drop:"))
async def confirm_drop(call: CallbackQuery):
    note_key = int(call.data.split(":")[1])
    pending = _pending.pop(note_key, None)
    if pending and pending["user_id"] == call.from_user.id:
        await call.answer("Не сохраняю")
        await call.message.edit_reply_markup(reply_markup=None)
        await call.message.answer("❌ Не сохранено.")
    else:
        await call.answer("Сохранение устарело", show_alert=True)


async def process_note(note_id: int, content: str):
    import asyncio
    analysis, embedding = await asyncio.gather(ai().analyze(content), ai().embed(content))
    await repo.update_note_ai(
        note_id,
        str(analysis.get("title") or "Без названия")[:200],
        str(analysis.get("summary") or "")[:2000],
        str(analysis.get("category") or "other")[:50],
        str(analysis.get("note_type") or "other")[:50],
        [str(x).lower()[:50] for x in (analysis.get("tags") or [])][:8],
        embedding,
    )


@router.message()
async def catch_all(message: Message):
    user_id = message.from_user.id
    await repo.upsert_user(user_id, message.from_user.username, message.from_user.first_name)
    mode = _waiting.pop(user_id, None)
    text = message.text or message.caption or ""

    if mode in {"search", "ask"}:
        if not text.strip():
            await message.answer("Нужен текстовый запрос.")
            return
        try:
            embedding = await ai().embed(text)
            rows = await repo.search_notes(user_id, text, embedding, settings.max_search_results)
            if not rows:
                await message.answer("Ничего не найдено.")
                return
            if mode == "search":
                parts = []
                for n in rows:
                    title = n["title"] or f"Заметка #{n['id']}"
                    score = float(n["score"] or 0)
                    parts.append(f"<b>#{n['id']} · {title}</b>  <i>{score:.0%}</i>\n{n['summary'] or n['content'][:350]}")
                await message.answer("\n\n".join(parts))
            else:
                await message.answer(await ai().answer(text, [dict(r) for r in rows[:6]]))
        except Exception as exc:
            await message.answer(f"⚠️ AI/search error: {type(exc).__name__}")
        return

    if not text.strip():
        await message.answer("Пока что я сохраняю текст и подпись к медиа.")
        return

    pending_key = message.message_id
    source_url = None
    if message.chat.type in {"group", "supergroup", "channel"} and message.chat.username:
        source_url = f"https://t.me/{message.chat.username}/{message.message_id}"
    _pending[pending_key] = {
        "user_id": user_id,
        "content": text.strip(),
        "source_chat_id": message.chat.id,
        "source_message_id": message.message_id,
        "source_url": source_url,
    }
    await message.answer("Сохранить?", reply_markup=confirm(pending_key))
