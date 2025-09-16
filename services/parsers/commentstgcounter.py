from pyrogram import Client
from datetime import datetime
from pyrogram.errors import MsgIdInvalid

import os
from dotenv import load_dotenv

load_dotenv()

API_ID = os.environ.get("TG_API_ID")
API_HASH = os.environ.get("TG_API_HASH")
SESSION_NAME = os.environ.get("TG_SESSION_NAME")
SESSION_STRING = os.environ.get("TG_SESSION_STRING")
CHANNEL_USERNAME = "@polytech_petra" #"@bgtu_voenmeh" #"@krylachvoenmeh"  # юзернейм или ID канала

# Инициализация клиента
app = Client(SESSION_NAME, session_string=SESSION_STRING, api_id=API_ID, api_hash=API_HASH) #Client(SESSION_NAME, api_id=API_ID, api_hash=API_HASH)

async def tg_comments_counter(channel_username, start_dt, end_dt, app):
    # получение ссылки на обсуждение (группа для комментариев) канала
    k = 0
    async for message in app.get_chat_history(channel_username):
        if k >= 10:
            return {}
        k += 1
        try:
            m = await app.get_discussion_message(channel_username, message.id)
            discussion_group = m.chat.id
            discussion_group_name = m.chat.title
            channel_id = m.sender_chat.id
            break
        except MsgIdInvalid:
            continue
        except ValueError:
            continue
    else:
        return {}
    comms = 0 # кол-во комментариев
    print(f"Working in discussion_group {discussion_group_name}, id: {discussion_group}")
    ids = set()
    commids = set()
    nids = {}
    async for message in app.get_chat_history(chat_id=discussion_group, offset_date=end_dt):
        if message:
            if getattr(message, 'forward_from_chat', None) and message.forward_from_chat.id == channel_id:
                if start_dt <= message.date <= end_dt:
                    ids.add(message.id)
            elif message.date < start_dt:
                break
    async for message in app.get_chat_history(chat_id=discussion_group, offset_date=end_dt):
        if message:
            if getattr(message, 'forward_from_chat', None) and message.forward_from_chat.id == channel_id:  #or "automatic_forward": true check
                continue
            elif getattr(message, 'reply_to_message_id', None) and message.reply_to_message_id in ids:
                if start_dt <= message.date <= end_dt:
                    commids.add(message.id)
                    # nids[message.reply_to_message_id] = nids.get(message.reply_to_message_id, [])
                    # nids[message.reply_to_message_id].append(message.id)
                    # print(message)
            elif message.date < start_dt:
                break
    async for message in app.get_chat_history(chat_id=discussion_group, offset_date=end_dt):
        if message:
            if getattr(message, 'forward_from_chat', None) and message.forward_from_chat.id == channel_id:  #or "automatic_forward": true check
                continue
            elif getattr(message, 'reply_to_message_id', None) and message.reply_to_message_id in ids or message.reply_to_message_id in commids:
                if start_dt <= message.date <= end_dt:
                    # nids[message.reply_to_message_id] = nids.get(message.reply_to_message_id, [])
                    # nids[message.reply_to_message_id].append(message.id)
                    # print(message)
                    comms += 1
            elif message.date < start_dt:
                break
    print(comms)
    return comms

if __name__ == "__main__":
    start_dt = datetime(2025, 8, 1)
    end_dt = datetime(2025, 8, 20, 23, 59, 59)
    with app:
        app.run(tg_comments_counter(CHANNEL_USERNAME, start_dt, end_dt, app))
