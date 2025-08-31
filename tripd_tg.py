"""Telegram interface for the TRIPD model."""

from __future__ import annotations

from pathlib import Path
import argparse
import os
import logging
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
    from .tripd import TripDModel, start_verb_stream
except ImportError:  # pragma: no cover - fallback for running as scripts
    from tripd import TripDModel, start_verb_stream

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model and dictionary setup
_model = TripDModel()
_sections: List[str] = sorted(_model.sections)

# Preload README and split into logical sections
_README = Path(__file__).resolve().parent / "README.md"
_text = _README.read_text(encoding="utf-8")

# Split by major sections for better parsing
sections = _text.split("## ")
_readme_parts = []
current_part = ""
chars_per_part = 3500  # Telegram message limit consideration

for i, section in enumerate(sections):
    if i == 0:  # First part before any ##
        current_part = section
    else:
        section_text = "## " + section
        if len(current_part + section_text) > chars_per_part and current_part:
            _readme_parts.append(current_part.strip())
            current_part = section_text
        else:
            current_part += "\n\n" + section_text

if current_part:
    _readme_parts.append(current_part.strip())

# Ensure we have at least 3 parts
while len(_readme_parts) < 3:
    if _readme_parts:
        # Split the longest part
        longest_idx = max(range(len(_readme_parts)), key=lambda i: len(_readme_parts[i]))
        longest = _readme_parts[longest_idx]
        mid = len(longest) // 2
        _readme_parts[longest_idx] = longest[:mid]
        _readme_parts.insert(longest_idx + 1, longest[mid:])
    else:
        _readme_parts = [_text[:len(_text)//3], _text[len(_text)//3:2*len(_text)//3], _text[2*len(_text)//3:]]

# ---------------------------------------------------------------------------
# Menu helpers

def _menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(name, callback_data=f"section:{name}")]
               for name in _sections]
    buttons.append([InlineKeyboardButton("TRIPD Documentation", callback_data="theory:0")])
    return InlineKeyboardMarkup(buttons)


async def _show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = "True Recursive Intelligent Python Dialect"
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            message, reply_markup=_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            message, reply_markup=_menu_keyboard()
        )
    logger.info("Menu displayed")


# ---------------------------------------------------------------------------
# Section handling
async def _send_section(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    section = query.data.split(":", 1)[1]
    logger.info("Section requested: %s", section)
    script = _model.generate_from_section(section)
    await query.message.reply_text(
        f"```TRIPD\n{script}\n```", parse_mode="Markdown"
    )


# ---------------------------------------------------------------------------
# Theory navigation
async def _send_theory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    index = int(query.data.split(":", 1)[1])
    logger.info("Theory section %d requested", index)
    
    # Проверяем границы индекса
    if index >= len(_readme_parts):
        index = 0
    
    text = _readme_parts[index]
    max_index = len(_readme_parts) - 1
    
    # Создаем кнопки навигации как в книге
    nav_buttons = []
    if index > 0:
        nav_buttons.append(InlineKeyboardButton("◀️", callback_data=f"theory:{index - 1}"))
    else:
        nav_buttons.append(InlineKeyboardButton("◀️", callback_data=f"theory:{max_index}"))  # Зацикливаем
    
    nav_buttons.append(InlineKeyboardButton("📚", callback_data="menu"))
    
    if index < max_index:
        nav_buttons.append(InlineKeyboardButton("▶️", callback_data=f"theory:{index + 1}"))
    else:
        nav_buttons.append(InlineKeyboardButton("▶️", callback_data="theory:0"))  # Зацикливаем
    
    await query.edit_message_text(
        text, reply_markup=InlineKeyboardMarkup([nav_buttons])
    )


# ---------------------------------------------------------------------------
# Message handling delegated to the TRIPD model
async def _handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.message
    text = update.message.text or ""
    logger.info("Received message: %s", text)
    script, metrics_text = _model.generate_response(text)
    await update.message.reply_text(
        f"```TRIPD\n{script}\n```", parse_mode="Markdown"
    )
    await update.message.reply_text(metrics_text)


# ---------------------------------------------------------------------------
async def _post_init(app: Application) -> None:
    await app.bot.set_my_commands([BotCommand("tripd", "Meet TRIPD 👉")])


def main() -> None:
    parser = argparse.ArgumentParser(description="Run TRIPD Telegram bot")
    parser.add_argument(
        "--verb-stream",
        metavar="ADDR",
        help="Enable live verb streaming via TCP port or UNIX socket path",
    )
    parser.add_argument(
        "--token",
        help=(
            "Telegram bot token. Overrides TELEGRAM_TOKEN environment "
            "variable if provided."
        ),
    )
    args = parser.parse_args()

    if args.verb_stream:
        addr = args.verb_stream
        if addr.isdigit():
            start_verb_stream(_model, port=int(addr))
        else:
            start_verb_stream(_model, unix_socket=addr)

    token = args.token or os.environ.get("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError(
            "Telegram token required via --token or TELEGRAM_TOKEN environment variable"
        )
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
    logger.info("Starting Telegram polling")
    application.run_polling()


__all__ = ["main"]


if __name__ == "__main__":
    main()
