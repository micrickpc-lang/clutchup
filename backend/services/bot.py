import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from config import settings
from models import User


bot = Bot(token=settings.bot_token)
logger = logging.getLogger(__name__)


def player_link(user: User) -> str:
    return f"@{user.username}" if user.username else f"tg://user?id={user.telegram_id}"


async def _send(user: User, other: User) -> None:
    try:
        await bot.send_message(
            chat_id=user.telegram_id,
            text=f"У вас мэтч! Ссылка на игрока: {player_link(other)}",
        )
    except TelegramAPIError:
        logger.exception("Could not notify Telegram user %s", user.telegram_id)


async def send_match_notifications(first: User, second: User) -> None:
    await asyncio.gather(_send(first, second), _send(second, first))

