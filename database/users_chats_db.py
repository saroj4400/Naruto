import re
import time
import datetime
from pymongo.errors import DuplicateKeyError
import motor.motor_asyncio
from info import (DATABASE_NAME, DATABASE_URI, CUSTOM_FILE_CAPTION, IMDB, IMDB_TEMPLATE, 
                  MELCOW_NEW_USERS, P_TTI_SHOW_OFF, SINGLE_BUTTON, SPELL_CHECK_REPLY, 
                  PROTECT_CONTENT, AUTO_DELETE, MAX_BTN, AUTO_FFILTER, SHORTLINK_API, 
                  SHORTLINK_URL, IS_SHORTLINK, TUTORIAL, IS_TUTORIAL)

# Initialize Async MongoDB Client
client = motor.motor_asyncio.AsyncIOMotorClient(DATABASE_URI)
db = client[DATABASE_NAME]

# Reference collections
users_col = db.users
groups_col = db.groups
bots_col = db.clone_bots

async def referal_add_user(user_id, ref_user_id):
    user_db = db.referal_users  # Fixed collection reference
    user = {'_id': ref_user_id}
    try:
        await user_db.insert_one(user)
        return True
    except DuplicateKeyError:
        return False

async def get_referal_all_users(user_id):
    user_db = db.referal_users
    return user_db.find()

async def get_referal_users_count(user_id):
    user_db = db.referal_users
    return await user_db.count_documents({})

async def delete_all_referal_users(user_id):
    user_db = db.referal_users
    await user_db.delete_many({})


class Database:
    default_setgs = {
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
        self.users = self.db.users  # Fixed typo (was 'uersz')
        self.groups = self.db.groups
        self.bots = self.db.clone_bots

    def new_user(self, user_id, name):
        return {
            "id": user_id,
            "name": name,
            "file_id": None,
            "caption": None,
            "message_command": None,
            "save": False,
            "ban_status": {"is_banned": False, "ban_reason": ""}
        }

    async def add_user(self, user_id, name):
        user = self.new_user(user_id, name)
        await self.users.insert_one(user)

    async def is_user_exist(self, user_id):
        return await self.users.find_one({"id": int(user_id)}) is not None

    async def total_users_count(self):
        return await self.users.count_documents({})

    async def add_clone_bot(self, bot_id, user_id, bot_token):
        settings = {
            "bot_id": bot_id,
            "bot_token": bot_token,
            "user_id": user_id,
            "url": None,
            "api": None,
            "tutorial": None,
            "update_channel_link": None,
        }
        await self.bots.insert_one(settings)

    async def is_clone_exist(self, user_id):
        return await self.bots.find_one({"user_id": int(user_id)}) is not None

    async def delete_clone(self, user_id):
        await self.bots.delete_many({"user_id": int(user_id)})

    async def get_clone(self, user_id):
        return await self.bots.find_one({"user_id": user_id})

    async def update_clone(self, user_id, user_data):
        await self.bots.update_one({"user_id": user_id}, {"$set": user_data}, upsert=True)

    async def ban_user(self, user_id, ban_reason="No Reason"):
        await self.users.update_one({"id": user_id}, {"$set": {"ban_status": {"is_banned": True, "ban_reason": ban_reason}}})

    async def remove_ban(self, user_id):
        await self.users.update_one({"id": user_id}, {"$set": {"ban_status": {"is_banned": False, "ban_reason": ""}}})

    async def get_ban_status(self, user_id):
        user = await self.users.find_one({"id": int(user_id)})
        return user.get("ban_status", {"is_banned": False, "ban_reason": ""}) if user else {"is_banned": False, "ban_reason": ""}

    async def get_all_users(self):
        return self.users.find({})

    async def delete_user(self, user_id):
        await self.users.delete_many({"id": int(user_id)})

    async def get_db_size(self):
        return (await self.db.command("dbstats"))["dataSize"]

    async def get_user(self, user_id):
        return await self.users.find_one({"id": user_id})

    async def update_user(self, user_data):
        await self.users.update_one({"id": user_data["id"]}, {"$set": user_data}, upsert=True)

    async def has_premium_access(self, user_id):
        user_data = await self.get_user(user_id)
        if user_data and user_data.get("expiry_time"):
            return datetime.datetime.now() <= user_data["expiry_time"]
        return False

    async def check_remaining_usage(self, user_id):
        user_data = await self.get_user(user_id)
        expiry_time = user_data.get("expiry_time") if user_data else None
        return expiry_time - datetime.datetime.now() if expiry_time else None

    async def give_free_trial(self, user_id):
        expiry_time = datetime.datetime.now() + datetime.timedelta(minutes=5)
        await self.users.update_one({"id": user_id}, {"$set": {"expiry_time": expiry_time, "has_free_trial": True}}, upsert=True)

    async def all_premium_users(self):
        return await self.users.count_documents({"expiry_time": {"$gt": datetime.datetime.now()}})

db = Database(DATABASE_URI, DATABASE_NAME)
