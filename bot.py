import json
import os
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Load token from environment variable
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable not set.")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Load menu from JSON
with open("menu.json", encoding="utf-8") as f:
    menu = json.load(f)

user_state = {}

@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar"),
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
    )
    await message.answer("اختر اللغة / Choose language / Выберите язык:", reply_markup=kb)
    user_state[message.from_user.id] = {"step": "lang"}

@dp.callback_query_handler(lambda c: c.data and c.data.startswith("lang_"))
async def choose_language_callback(callback_query: types.CallbackQuery):
    lang_code = callback_query.data.split("_")[1]
    if lang_code not in menu["languages"]:
        await callback_query.answer("الرجاء اختيار لغة صحيحة.")
        return
    user_state[callback_query.from_user.id] = {"lang": lang_code, "step": "main"}
    
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for topic in menu["menu"][lang_code]:
        markup.add(KeyboardButton(topic))
    markup.add(KeyboardButton("🔙 Назад"))
    
    await bot.send_message(callback_query.from_user.id, "اختر القسم / Choose category:", reply_markup=markup)
    await callback_query.answer()

@dp.message_handler(lambda message: user_state.get(message.from_user.id, {}).get("step") == "main")
async def choose_topic(message: types.Message):
    lang = user_state[message.from_user.id]["lang"]
    topic = message.text
    
    if topic == "🔙 Назад":
        await start_cmd(message)
        return
    
    if topic not in menu["menu"][lang]:
        await message.answer("اختر من القائمة فقط.")
        return
    
    user_state[message.from_user.id]["topic"] = topic
    user_state[message.from_user.id]["step"] = "sub"
    
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for sub in menu["menu"][lang][topic]:
        markup.add(KeyboardButton(sub))
    markup.add(KeyboardButton("🔙 Назад"))
    
    await message.answer("اختر القسم الفرعي / Choose subsection:", reply_markup=markup)

@dp.message_handler(lambda message: user_state.get(message.from_user.id, {}).get("step") == "sub")
async def choose_sub(message: types.Message):
    lang = user_state[message.from_user.id]["lang"]
    topic = user_state[message.from_user.id]["topic"]
    sub = message.text
    
    if sub == "🔙 Назад":
        user_state[message.from_user.id]["step"] = "main"
        await choose_topic(message)
        return
    
    url = menu["menu"][lang][topic].get(sub)
    if not url:
        await message.answer("اختر من القائمة فقط.")
        return
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("افتح المعلومات 📄", url=url))
    
    await message.answer(f"معلومات عن: *{sub}*", parse_mode="Markdown", reply_markup=markup)

async def on_startup(dp):
    await bot.delete_webhook(drop_pending_updates=True)

if __name__ == "__main__":
    executor.start_polling(dp, on_startup=on_startup)
