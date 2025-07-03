from pyrogram import Client
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

API_ID = os.environ.get("TG_API_ID")
API_HASH = os.environ.get("TG_API_HASH")
SESSION_NAME = os.environ.get("TG_SESSION_NAME")
CHANNEL_USERNAME = "@bgtu_voenmeh" #"@krylachvoenmeh"  # юзернейм или ID канала

# Инициализация клиента
app = Client(SESSION_NAME, api_id=API_ID, api_hash=API_HASH)

async def tg_ultimate_parser(channel_username: str, start_dt: datetime, end_dt: datetime, app: Client) -> tuple[int,int,int,int]:
    views = 0
    count = 0
    reacts = 0
    forwards = 0
    last_grouped_id = -1  # Для отслеживания связанных медиа-сообщений

    async for message in app.get_chat_history(channel_username, offset_date=end_dt):
        if message:
            if start_dt <= message.date <= end_dt:
                # Проверяем наличие grouped_id и пропускаем повторные медиа-группы
                curr_grouped_id = getattr(message, 'media_group_id', None)
                if curr_grouped_id is not None and curr_grouped_id == last_grouped_id:
                    continue
                try:
                    reactions = message.reactions.reactions
                    for react in reactions:
                        reacts += react.count
                except AttributeError:
                    continue
                count += 1
                forwards += message.forwards if message.forwards else 0
                views += message.views if message.views else 0  # Суммируем просмотры, если они есть
                # Обновляем ID группы, если оно есть
                last_grouped_id = curr_grouped_id

            elif message.date < start_dt:
                break

    return count, views, reacts, forwards

if __name__ == "__main__":
    start_dt = datetime(2025, 4, 1)
    end_dt = datetime(2025, 4, 30, 23, 59, 59)
    with app:
        app.run(tg_ultimate_parser(CHANNEL_USERNAME, start_dt, end_dt, app))
