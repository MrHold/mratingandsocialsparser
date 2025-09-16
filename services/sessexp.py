from pyrogram import Client
import os
from dotenv import load_dotenv

load_dotenv()

api_id = "tg_api_id"
api_hash = "tg_api_hash"
session_name = "session"

with Client(session_name, api_id=api_id, api_hash=api_hash) as app:
    print(app.export_session_string())
