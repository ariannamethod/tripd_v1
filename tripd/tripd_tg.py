"""Telegram interface for the TRIPD model."""

from __future__ import annotations

from pathlib import Path
import argparse
import os
from typing import List

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    BotCommand,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

try:  # pragma: no cover - support package and script execution
    from . import TripDModel
    from .verb_stream import start_verb_stream
except ImportError:  # pragma: no cover - fallback for running as scripts
    from tripd import TripDModel
    from tripd.verb_stream import start_verb_stream

# ---------------------------------------------------------------------------
# Model and dictionary setup
_model = TripDModel()
_sections: List[str] = sorted(_model.sections)

# Preload README and split into three equal parts
_README = Path(__file__).resolve().parent.parent / "README.md"
_text = _README.read_text(encoding="utf-8")
_chunk = len(_text) // 3
_readme_parts = [
    _text[i * _chunk : (i + 1) * _chunk] for i in range(3)
]
_readme_parts[2] += _text[3 * _chunk :]

# ---------------------------------------------------------------------------
# Menu helpers

def _menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(name, callback_data=f"section:{name}")]
               for name in _sections]
    buttons.append([InlineKeyboardButton("THEORY", callback_data="theory:0")])
    return InlineKeyboardMarkup(buttons)


async def _show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "Select a topic:", reply_markup=_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            "Select a topic:", reply_markup=_menu_keyboard()
        )


# ---------------------------------------------------------------------------
# Section handling
async def _send_section(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    section = query.data.split(":", 1)[1]
    script = _model.generate_from_section(section)
    await query.edit_message_text(
        f"```python\n{script}\n```", parse_mode="Markdown"
    )


# ---------------------------------------------------------------------------
# Theory navigation
async def _send_theory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    index = int(query.data.split(":", 1)[1])
    text = _readme_parts[index]
    buttons = []
    if index > 0:
        buttons.append(
            InlineKeyboardButton("Back", callback_data=f"theory:{index - 1}")
        )
    else:
        buttons.append(InlineKeyboardButton("Back", callback_data="menu"))
    if index < 2:
        buttons.append(
            InlineKeyboardButton("Forward", callback_data=f"theory:{index + 1}")
        )
    else:
        buttons.append(InlineKeyboardButton("Forward", callback_data="menu"))
    await query.edit_message_text(
        text, reply_markup=InlineKeyboardMarkup([buttons])
    )


# ---------------------------------------------------------------------------
# Message echo with metric-based font selection
async def _handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.message
    text = update.message.text or ""
    metrics = _model.metrics(text)
    if metrics["entropy"] > 4.5:
        formatted = f"<b>{text}</b>"
    elif metrics["perplexity"] > 10:
        formatted = f"<i>{text}</i>"
    else:
        formatted = f"<code>{text}</code>"
    await update.message.reply_text(formatted, parse_mode="HTML")


# ---------------------------------------------------------------------------
async def _post_init(app: Application) -> None:
    await app.bot.set_my_commands([BotCommand("tripd", "Open TRIPD menu")])


def main() -> None:
    parser = argparse.ArgumentParser(description="Run TRIPD Telegram bot")
    parser.add_argument(
        "--verb-stream",
        metavar="ADDR",
        help="Enable live verb streaming via TCP port or UNIX socket path",
    )
    args = parser.parse_args()
    if args.verb_stream:
        addr = args.verb_stream
        if addr.isdigit():
            start_verb_stream(_model, port=int(addr))
        else:
            start_verb_stream(_model, unix_socket=addr)

    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_TOKEN environment variable is required")
    application = (
        Application.builder()
        .token(token)
        .post_init(_post_init)
        .build()
    )
    application.add_handler(CommandHandler("tripd", _show_menu))
    application.add_handler(CallbackQueryHandler(_show_menu, pattern="^menu$"))
    application.add_handler(
        CallbackQueryHandler(_send_section, pattern="^section:")
    )
    application.add_handler(
        CallbackQueryHandler(_send_theory, pattern="^theory:")
    )
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, _handle_message)
    )
    application.run_polling()


__all__ = ["main"]
