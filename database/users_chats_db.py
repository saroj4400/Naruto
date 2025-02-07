import re
import motor.motor_asyncio
from pymongo.errors import DuplicateKeyError
from info import (
    DATABASE_NAME, DATABASE_URI, CUSTOM_FILE_CAPTION, IMDB, IMDB_TEMPLATE, 
    MELCOW_NEW_USERS, P_TTI_SHOW_OFF, SINGLE_BUTTON, SPELL_CHECK_REPLY, 
    PROTECT_CONTENT, AUTO_DELETE, MAX_BTN, AUTO_FFILTER, SHORTLINK_API, 
    SHORTLINK_URL, IS_SHORTLINK, TUTORIAL, IS_TUTORIAL
)
import datetime

class Database:

    default_settings = {
        'button': SINGLE_BUTTON,
        'botpm': P_TTI_SHOW_OFF,
        'file_secure': PROTECT_CONTENT,
        'imdb': IMDB,
        'spell_check': SPELL_CHECK_REPLY,
        'welcome': MELCOW_NEW_USERS,
        'auto_delete': AUTO_DELETE,
        'auto_ffilter': AUTO_FFILTER,
        'max_btn': MAX_BTN,
        'template': IMDB_TEMPLATE,
        'caption': CUSTOM_FILE_CAPTION,
        'shortlink': SHORTLINK_URL,
        'shortlink_api': SHORTLINK_API,
        'is_shortlink': IS_SHORTLINK,
        'fsub': None,
        'tutorial': TUTORIAL,
        'is_tutorial': IS_TUTORIAL,
    }

    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.users = self.db["users"]
        self.groups = self.db["groups"]
        self.bots = self.db["clone_bots"]

    async def add_user(self, user_id, name):
        user = {
            "id": user_id,
            "name": name,
            "file_id": None,
            "caption": None,
            "message_command": None,
            "save": False,
            "ban_status": {"is_banned": False, "ban_reason": ""},
        }
        try:
            await self.users.insert_one(user)
            return True
        except DuplicateKeyError:
            return False

    async def is_user_exist(self, user_id):
        user = await self.users.find_one({"id": int(user_id)})
        return bool(user)

    async def total_users_count(self):
        return await self.users.count_documents({})

    async def ban_user(self, user_id, reason="No Reason"):
        await self.users.update_one(
            {"id": int(user_id)}, {"$set": {"ban_status": {"is_banned": True, "ban_reason": reason}}}
        )

    async def get_ban_status(self, user_id):
        user = await self.users.find_one({"id": int(user_id)})
        return user.get("ban_status", {"is_banned": False, "ban_reason": ""}) if user else {"is_banned": False, "ban_reason": ""}

    async def remove_ban(self, user_id):
        await self.users.update_one({"id": int(user_id)}, {"$set": {"ban_status": {"is_banned": False, "ban_reason": ""}}})

    async def get_all_users(self):
        return await self.users.find().to_list(length=None)

    async def delete_user(self, user_id):
        await self.users.delete_many({"id": int(user_id)})

    async def add_clone_bot(self, bot_id, user_id, bot_token):
        bot_data = {
            "bot_id": bot_id,
            "bot_token": bot_token,
            "user_id": user_id,
            "url": None,
            "api": None,
            "tutorial": None,
            "update_channel_link": None
        }
        await self.bots.insert_one(bot_data)

    async def get_clone(self, user_id):
        return await self.bots.find_one({"user_id": int(user_id)})

    async def update_clone(self, user_id, data):
        await self.bots.update_one({"user_id": int(user_id)}, {"$set": data}, upsert=True)

    async def delete_clone(self, user_id):
        await self.bots.delete_many({"user_id": int(user_id)})

    async def add_chat(self, chat_id, title):
        chat = {
            "id": chat_id,
            "title": title,
            "chat_status": {"is_disabled": False, "reason": ""},
            "settings": self.default_settings
        }
        await self.groups.insert_one(chat)

    async def disable_chat(self, chat_id, reason="No Reason"):
        await self.groups.update_one({"id": int(chat_id)}, {"$set": {"chat_status": {"is_disabled": True, "reason": reason}}})

    async def enable_chat(self, chat_id):
        await self.groups.update_one({"id": int(chat_id)}, {"$set": {"chat_status": {"is_disabled": False, "reason": ""}}})

    async def get_chat(self, chat_id):
        chat = await self.groups.find_one({"id": int(chat_id)})
        return chat.get("chat_status") if chat else None

    async def update_settings(self, chat_id, settings):
        await self.groups.update_one({"id": int(chat_id)}, {"$set": {"settings": settings}})

    async def get_settings(self, chat_id):
        chat = await self.groups.find_one({"id": int(chat_id)})
        return chat.get("settings", self.default_settings) if chat else self.default_settings

    async def total_chat_count(self):
        return await self.groups.count_documents({})

    async def get_all_chats(self):
        return await self.groups.find().to_list(length=None)

    async def get_db_size(self):
        return (await self.db.command("dbstats"))["dataSize"]

db = Database(DATABASE_URI, DATABASE_NAME)
