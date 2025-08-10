#!/usr/bin/env python3
"""
Telegram Integration for AI-CRM System
Allows interaction with the PM Agent via Telegram.
"""

import asyncio
import logging
import os
import sys

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Add project root to path to allow sibling imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from our_crm_ai.agents.pm_agent import handle_command
except ImportError as e:
    print(f"Failed to import pm_agent. Error: {e}")
    print(f"Current sys.path: {sys.path}")
    sys.exit(1)

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Environment Variables ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


def check_env_variables():
    """Checks if all required environment variables are set."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("FATAL: TELEGRAM_BOT_TOKEN environment variable not set.")
        sys.exit(1)
    return True


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the /start command is issued."""
    await update.message.reply_text(
        "Welcome to the AI-CRM PM Agent Bot! "
        "Send me a command and I'll process it."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a help message when the /help command is issued."""
    await update.message.reply_text(
        "I am the AI-CRM PM Agent bot. I can help you with:\n\n"
        "- `list tasks`: Show all tasks on the board.\n"
        "- `view task <task_id>`: Show details for a specific task.\n"
        "- `what is <topic>`: Ask a question to the knowledge base.\n\n"
        "Just send me a message with your command!"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles incoming text messages and passes them to the PM agent."""
    user_message = update.message.text
    chat_id = update.message.chat_id
    logger.info(f"Received message from chat_id {chat_id}: '{user_message}'")

    try:
        # Show a "typing..." indicator
        await context.bot.send_chat_action(chat_id=chat_id, action='typing')

        # Process the command using the pm_agent
        # Running in a separate thread to avoid blocking the asyncio event loop
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None, handle_command, user_message
        )

        logger.info(f"Sending response to chat_id {chat_id}: '{response[:100]}...'")
        await update.message.reply_text(response)

    except Exception as e:
        logger.error(f"Error handling message for chat_id {chat_id}: {e}", exc_info=True)
        await update.message.reply_text(
            "Sorry, an error occurred while processing your request. "
            "The error has been logged."
        )


def main() -> None:
    """Starts the Telegram bot."""
    if not check_env_variables():
        return

    logger.info("Starting Telegram bot...")

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # on non command i.e message - handle the message from user
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot until the user presses Ctrl-C
    try:
        application.run_polling()
    except Exception as e:
        logger.fatal(f"Bot failed to start or crashed: {e}", exc_info=True)


if __name__ == '__main__':
    main()
