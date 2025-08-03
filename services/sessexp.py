from pyrogram import Client
import os
from dotenv import load_dotenv

load_dotenv()

api_id = os.environ.get("TG_API_ID")
api_hash = os.environ.get("TG_API_HASH")
session_name = os.environ.get("TG_SESSION_NAME")

with Client(session_name, api_id=api_id, api_hash=api_hash) as app:
    print(app.export_session_string())
