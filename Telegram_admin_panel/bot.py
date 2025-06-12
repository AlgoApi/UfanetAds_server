import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, ForceReply, InlineKeyboardMarkup, InlineKeyboardButton
import httpx
import logging
from dotenv import load_dotenv
from schemas.user import RoleEnum

load_dotenv()

API_ID = int(os.getenv("TG_API_ID"))
API_HASH = os.getenv("TG_API_HASH")
BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
BACKEND_URL = os.getenv("BACKEND_URL")
SUPERADMIN_ID = int(os.getenv("SUPERADMIN_ID"))

# --- ЛОГИРОВАНИЕ ---
logging.basicConfig(
    level="INFO",
    format="%(asctime)s %(levelname)-8s %(name)-12s %(message)s"
)
logger = logging.getLogger(__name__)

SESSIONS: dict[int, str] = {}

app = Client("ufanet_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_context: dict[int, dict[str, dict[str, str|list[int]]]] = {}

# --- ETC ---------------------------------------------------
async def delete_later(msg: Message, delay: float = 1.0):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except:
        pass

async def check_cred(message: Message) -> str | None:
    user_id = message.from_user.id
    token = SESSIONS.get(user_id)
    if token:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BACKEND_URL}/api/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            if resp.status_code != 200: token = None
    if not token:
        try:
            await message.answer("Сначала войдите командой /login", show_alert=True)
            return None
        except:
            await message.reply("Сначала войдите командой /login")
            return None
    return token

# --- SUPERADMIN: CREATE ADMIN ----------------------------------
@ app.on_message(filters.private & filters.user(SUPERADMIN_ID) & filters.regex("^create_admin$"))
async def cmd_create_admin(c: Client, m: Message):
    global user_context
    user_id = m.from_user.id
    if not await check_cred(m):
        return
    user_context[user_id] = {"step": {"name": "create_admin_login"}, "ctx": {}}
    await m.reply("Введите логин нового администратора:", reply_markup=ForceReply(True))

# --- ADMIN: LOGIN ------------------------------------------------
@ app.on_message(filters.private & filters.command("login"))
async def cmd_login(c: Client, m: Message):
    global user_context
    user_id = m.from_user.id
    user_context[user_id] = {"step": {"name": "login_login"}, "ctx": {}}
    await m.reply("Введите ваш логин:", reply_markup=ForceReply(True))

# --- LOGOUT -------------------------------------------------------
@ app.on_callback_query(filters.regex("^logout$"))
async def logout(c: Client, q):
    SESSIONS.pop(q.from_user.id, None)
    await q.answer("Вы вышли.")
    await q.message.delete()

# --- ADD OFFER FLOW ----------------------------------------------
@ app.on_callback_query(filters.regex("^create_offer$"))
async def cb_create_offer(c: Client, q):
    user_id = q.from_user.id
    if not await check_cred(q):
        return
    await q.message.reply("Введите заголовок предложения:", reply_markup=ForceReply(True))
    await q.message.delete()
    user_context[user_id] = {"step": {"name": "create_offer_title"}, "ctx": {}}


# --- ADD category FLOW ----------------------------------------------
@ app.on_callback_query(filters.regex("^create_category$"))
async def cb_create_category(c: Client, q):
    user_id = q.from_user.id
    if not await check_cred(q):
        return
    await q.message.reply("Введите заголовок категории:", reply_markup=ForceReply(True))
    await q.message.delete()
    user_context[user_id] = {"step": {"name": "create_category_title"}, "ctx": {}}


# --- ADD cities FLOW ----------------------------------------------
@ app.on_callback_query(filters.regex("^create_city$"))
async def cb_create_city(c: Client, q):
    user_id = q.from_user.id
    if not await check_cred(q):
        return
    await q.message.reply("Введите название города:", reply_markup=ForceReply(True))
    await q.message.delete()
    user_context[user_id] = {"step": {"name": "create_city_title"}, "ctx": {}}


# --- GLOBAL reply_handler ----------------------------------------------
@ app.on_message(filters.reply & filters.private)
async def reply_handler(c: Client, m: Message):
    global user_context
    user_id = m.from_user.id
    if user_context.get(user_id):
        if not user_context.get(user_id).get("step"):
            return
        if user_context.get(user_id).get("ctx") is None:
            return
        text = m.text.strip()
        if not text:
            return
        if user_context.get(user_id).get("step").get("name") == "create_admin_login":
            user_context[user_id]["ctx"]["login"] = text
            await m.reply("Введите пароль для нового администратора:", reply_markup=ForceReply(True))
            await delete_later(m)
            user_context[user_id]["step"]["name"] = "create_admin_pass"
            return
        if user_context.get(user_id).get("step").get("name") == "create_admin_pass":
            login = user_context[user_id]["ctx"].get("login")
            token = SESSIONS.get(user_id)
            async with httpx.AsyncClient() as client:
                resp = await client.post(f"{BACKEND_URL}/api/auth/signup",
                                         json={
                                             "username": login,
                                             "password": text
                                         },
                                         headers={"Authorization": f"Bearer {token}"})
            await delete_later(m)
            if resp.status_code == 201:
                await m.reply(f"Администратор {resp.text} успешно создан.")
            else:
                await m.reply(f"Ошибка при создании: {resp.text}")
            del user_context[user_id]
            return
        if user_context.get(user_id).get("step").get("name") == "login_login":
            user_context[user_id]["ctx"]["login"] = text
            await m.reply("Введите ваш пароль:", reply_markup=ForceReply(True))
            user_context[user_id]["step"]["name"] = "login_pass"
            await delete_later(m)
            return
        if user_context.get(user_id).get("step").get("name") == "login_pass":
            login = user_context[user_id]["ctx"]["login"]
            async with httpx.AsyncClient() as client:
                resp = await client.post(f"{BACKEND_URL}/api/auth/token",
                                         data={"grant_type": "password", "username": login, "password": text},
                                         headers={"Content-Type": "application/x-www-form-urlencoded"})
            await delete_later(m)
            if resp.status_code == 200:
                token = resp.json().get("access_token")
                SESSIONS[m.from_user.id] = token
                reply_markup = [
                    [InlineKeyboardButton("Добавить предложение", callback_data="create_offer")],
                    [InlineKeyboardButton("Добавить город", callback_data="create_city")],
                    [InlineKeyboardButton("Добавить категорию", callback_data="create_category")],
                    [InlineKeyboardButton("Выйти", callback_data="logout")],
                ]
                async with httpx.AsyncClient() as client:
                    resp = await client.get(
                        f"{BACKEND_URL}/api/auth/me",
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    if resp.json().get("role") == RoleEnum.superadmin:
                        reply_markup.append([InlineKeyboardButton("Создать админа", callback_data="create_admin")])
                await m.reply("Вы вошли успешно.", reply_markup=InlineKeyboardMarkup(reply_markup))
            else:
                await m.reply("Неверный логин или пароль.")
            del user_context[user_id]
            return
        if user_context.get(user_id).get("step").get("name") == "create_offer_title":
            token = SESSIONS.get(user_id)
            if not token: return
            user_context[user_id]["ctx"]["title"] = text
            await m.reply("Введите описание:", reply_markup=ForceReply(True))
            user_context[user_id]["step"]["name"] = "create_offer_description"
            await delete_later(m)
            return
        if user_context.get(user_id).get("step").get("name") == "create_offer_description":
            token = SESSIONS.get(user_id)
            if not token: return
            user_context[user_id]["ctx"]["description"] = text
            await m.reply("Введите прямую ссылку на изображение для вона карточки:",
                                reply_markup=ForceReply(True))
            user_context[user_id]["step"]["name"] = "create_offer_BackURL"
            await delete_later(m)
            return
        if user_context.get(user_id).get("step").get("name") == "create_offer_BackURL":
            token = SESSIONS.get(user_id)
            if not token: return
            user_context[user_id]["ctx"]["BackURL"] = text
            await m.reply("Введите прямую ссылку на изображение логотипа:", reply_markup=ForceReply(True))
            user_context[user_id]["step"]["name"] = "create_offer_LogoURL"
            await delete_later(m)
            return
        if user_context.get(user_id).get("step").get("name") == "create_offer_LogoURL":
            token = SESSIONS.get(user_id)
            if not token: return
            user_context[user_id]["ctx"]["LogoURL"] = text
            await m.reply("Введите Название компании:", reply_markup=ForceReply(True))
            user_context[user_id]["step"]["name"] = "create_offer_company"
            await delete_later(m)
            return
        if user_context.get(user_id).get("step").get("name") == "create_offer_company":
            token = SESSIONS.get(user_id)
            if not token: return
            user_context[user_id]["ctx"]["company"] = text
            await m.reply("Введите ID городов через запятую:", reply_markup=ForceReply(True))
            user_context[user_id]["step"]["name"] = "create_offer_cities"
            await delete_later(m)
            return
        if user_context.get(user_id).get("step").get("name") == "create_offer_cities":
            token = SESSIONS.get(user_id)
            if not token: return
            user_context[user_id]["ctx"]["city_ids"] = [int(x) for x in text.split(",") if x.strip().isdigit()]
            await m.reply("Введите ID категорий (до 2) через запятую:", reply_markup=ForceReply(True))
            user_context[user_id]["step"]["name"] = "create_offer_categories"
            await delete_later(m)
            return
        if user_context.get(user_id).get("step").get("name") == "create_offer_categories":
            token = SESSIONS.get(user_id)
            if not token: return
            category_ids = [int(x) for x in text.split(",") if x.strip().isdigit()]
            ctx = user_context[user_id].get("ctx")
            if len(category_ids) > 2:
                await m.reply(f"Ошибка: ID категорий больше двух")
                await delete_later(m)
                return
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{BACKEND_URL}/api/offers/",
                    json={
                        "title": ctx["title"],
                        "description": ctx["description"],
                        "backgroundImageUrl": ctx["BackURL"],
                        "companyLogoUrl": ctx["LogoURL"],
                        "companyName": ctx["company"],
                        "cityIds": ctx["city_ids"],
                        "categoryIds": category_ids
                    },
                    headers={"Authorization": f"Bearer {token}"}
                )
            await m.reply("Успешно создано." if resp.status_code == 201 else f"Ошибка: {resp.text}")
            await delete_later(m)
            del user_context[user_id]
            return
        if user_context.get(user_id).get("step").get("name") == "create_category_title":
            token = SESSIONS.get(user_id)
            if not token: return
            user_context[user_id]["ctx"]["category_title"] = text
            await m.reply("Введите прямую ссылку на изображение для вона категории:",
                                reply_markup=ForceReply(True))
            user_context[user_id]["step"]["name"] = "create_category_BackURL"
            await delete_later(m)
            return
        if user_context.get(user_id).get("step").get("name") == "create_category_BackURL":
            token = SESSIONS.get(user_id)
            if not token: return
            backurl = text
            ctx = user_context[user_id].get("ctx")
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{BACKEND_URL}/api/categories/",
                    json={
                        "name": ctx["category_title"],
                        "image_url": backurl,
                    },
                    headers={"Authorization": f"Bearer {token}"}
                )
            await m.reply("Успешно создано." if resp.status_code == 201 else f"Ошибка: {resp.text}")
            await delete_later(m)
            del user_context[user_id]
            return
        if user_context.get(user_id).get("step").get("name") == "create_city_title":
            token = SESSIONS.get(user_id)
            if not token: return
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{BACKEND_URL}/api/cities/",
                    json={
                        "name": text,
                    },
                    headers={"Authorization": f"Bearer {token}"}
                )
            await m.reply("Успешно создано." if resp.status_code == 201 else f"Ошибка: {resp.text}")
            await delete_later(m)
            del user_context[user_id]
            return

if __name__ == "__main__":
    app.run()

