import os
import asyncio
import logging
from collections import defaultdict
from datetime import datetime, time
import pytz

from aiogram import Bot, Dispatcher, types
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
    InputMediaPhoto, InputMediaVideo
)
from aiogram.utils import executor
from aiogram.utils.exceptions import ChatNotFound
from dotenv import load_dotenv

import db

logging.basicConfig(level=logging.INFO)
load_dotenv()

TOKEN = os.getenv("TOKEN")
CHANNELS_IDS = os.getenv("CHANNELS_IDS", "").split(",")
CHANNELS = {
    int(cid): name
    for cid, name in zip(CHANNELS_IDS, ["RepNews CNFANS²", "RepNews ACBuy²", "RN ALL FINDS"])
}

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

ctx = {}
album_buf = defaultdict(list)
awaiting_limit: dict[int, int] = {}
awaiting_admin_limit: dict[int, dict] = {}
owner_stats = {}
limit_channel_selection = {}
post_buffer = {}

start_kb = ReplyKeyboardMarkup(
    [[KeyboardButton("📤 Post"), KeyboardButton("🛠 Panel")], [KeyboardButton("❓ Help")]],
    resize_keyboard=True
)

# Add back button to channel selection  
def get_chan_kb():
    buttons = [[KeyboardButton(name)] for name in CHANNELS.values()]
    buttons.append([KeyboardButton("🔙 Back")])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

chan_kb = get_chan_kb()

# Add back button to mode selection
mode_kb = ReplyKeyboardMarkup(
    [[
        KeyboardButton("📷 Media only"),
        KeyboardButton("📝 Text only"),
        KeyboardButton("🖼️ Media + caption")
    ], [KeyboardButton("🔙 Back")]],
    resize_keyboard=True
)

# Add back button to menu
menu_kb = ReplyKeyboardMarkup([[
    KeyboardButton("✏️ Change limit"), KeyboardButton("👥 Admin limits")],
    [KeyboardButton("📊 Today"), KeyboardButton("📈 All time")],
    [KeyboardButton("🔙 Back to main")]
], resize_keyboard=True)

admin_menu_kb = ReplyKeyboardMarkup([[
    KeyboardButton("➕ Set admin limit"), KeyboardButton("📋 View admin limits")],
    [KeyboardButton("❌ Remove admin limit"), KeyboardButton("🔙 Back to menu")]
], resize_keyboard=True)

async def is_owner(cid: int, uid: int) -> bool:
    try:
        mem = await bot.get_chat_member(cid, uid)
        return mem.status == "creator"
    except:
        return False

async def is_admin(cid: int, uid: int) -> bool:
    try:
        mem = await bot.get_chat_member(cid, uid)
        return mem.status in ("creator", "administrator")
    except:
        return False

async def get_channel_admins(cid: int) -> list[tuple[int, str]]:
    """Получить список администраторов канала"""
    try:
        admins = await bot.get_chat_administrators(cid)
        result = []
        for admin in admins:
            if admin.status in ("creator", "administrator"):
                name = admin.user.full_name or f"User {admin.user.id}"
                result.append((admin.user.id, name))
        return result
    except:
        return []

async def reset_limits_scheduler():
    """Планировщик для сброса лимитов в полночь по китайскому времени"""
    china_tz = pytz.timezone('Asia/Shanghai')
    last_reset_date = None
    
    logging.info("🕐 Запущен планировщик сброса лимитов (China Time Zone)")
    logging.info(f"🇨🇳 Текущее время в Китае: {datetime.now(china_tz)}")
    
    while True:
        try:
            # Получаем текущее время в Китае
            china_now = datetime.now(china_tz)
            current_date = china_now.date()
            
            # Если сейчас полночь (00:00-00:59) и мы еще не сбрасывали сегодня
            if china_now.hour == 0 and last_reset_date != current_date:
                logging.info(f"Сброс дневных лимитов в полночь по китайскому времени: {china_now}")
                await db.reset_daily_limits()
                last_reset_date = current_date
                
            # Проверяем каждые 30 минут
            await asyncio.sleep(1800)
                
        except Exception as e:
            logging.error(f"Ошибка в планировщике сброса лимитов: {e}")
            await asyncio.sleep(1800)  # Ждем 30 минут перед повторной попыткой

@dp.message_handler(commands=["start", "help"])
async def cmd_start(m: types.Message):
    instructions = (
        "👋 Welcome to Admin Posts Handler Bot!\n\n"
        "🤖 **What this bot does:**\n"
        "• Allows channel admins to post content with daily limits\n"
        "• Tracks posting statistics\n"
        "• Manages individual admin limits\n\n"
        "📱 **How to use:**\n"
        "• **📤 Post** - Share content to your channels (admins only)\n"
        "• **🛠 Panel** - View stats and manage settings (owners only)\n"
        "• **❓ Help** - Show this help message\n\n"
        "💡 **Tips:**\n"
        "• Use 🔙 Back buttons to navigate between menus\n"
        "• Daily limits reset automatically at 00:00 China time\n"
        "• Contact channel owner for limit changes\n\n"
        "Ready to start? Choose an option below:"
    )
    await m.answer(instructions, reply_markup=start_kb)

@dp.message_handler(lambda m: m.text == "❓ Help")
async def help_command(m: types.Message):
    help_text = (
        "📚 **Detailed Instructions:**\n\n"
        "**For Admins:**\n"
        "1. Click 📤 Post\n"
        "2. Select your channel\n"
        "3. Choose posting mode:\n"
        "   • 📷 Media only - Send photos/videos without text\n"
        "   • 📝 Text only - Send text messages\n"
        "   • 🖼️ Media + caption - Send media with text description\n"
        "4. Send your content\n\n"
        "**For Channel Owners:**\n"
        "• Use 🛠 Panel to access management tools\n"
        "• Set daily limits for the channel\n"
        "• Manage individual admin limits\n"
        "• View posting statistics\n\n"
        "**Navigation:**\n"
        "• Use 🔙 Back buttons to go to previous menu\n"
        "• Type /start anytime to return to main menu\n\n"
        "⏰ **Important:**\n"
        "• Daily posting limits reset automatically at 00:00 China time\n"
        "• All users start fresh each day\n\n"
        "❓ Need more help? Contact your channel administrator."
    )
    await m.answer(help_text, reply_markup=start_kb)

# Add back to main menu handler
@dp.message_handler(lambda m: m.text == "🔙 Back to main")
async def back_to_main(m: types.Message):
    await m.answer("🏠 Back to main menu:", reply_markup=start_kb)

# Handle back button in various contexts
@dp.message_handler(lambda m: m.text == "🔙 Back")
async def handle_back_button(m: types.Message):
    uid = m.from_user.id
    
    # Clear any pending operations
    if uid in ctx:
        ctx.pop(uid, None)
    if uid in album_buf:
        album_buf[uid].clear()
    if uid in awaiting_limit:
        awaiting_limit.pop(uid, None)
    if uid in awaiting_admin_limit:
        awaiting_admin_limit.pop(uid, None)
    if uid in owner_stats:
        owner_stats.pop(uid, None)
    
    await m.answer("🔙 Returning to main menu:", reply_markup=start_kb)

@dp.message_handler(lambda m: m.text == "📤 Post")
async def start_post(m: types.Message):
    uid = m.from_user.id
    for cid in CHANNELS:
        if await is_admin(cid, uid):
            owner_stats[uid] = "post"
            return await m.answer("Select channel to post into:", reply_markup=chan_kb)
    await m.answer("❌ You are not an admin of any configured channel.", reply_markup=start_kb)

@dp.message_handler(lambda m: m.text in ("📷 Media only", "📝 Text only", "🖼️ Media + caption"))
async def pick_mode(m: types.Message):
    uid, txt = m.from_user.id, m.text
    if uid not in ctx:
        return await m.answer("Press 📤 Post first.", reply_markup=start_kb)
    mode = {
        "📷 Media only": "media_only",
        "📝 Text only": "text",
        "🖼️ Media + caption": "media_caption"
    }[txt]
    ctx[uid]["mode"] = mode
    if mode == "media_caption":
        album_buf[uid].clear()
    
    # Add back button for content posting
    back_kb = ReplyKeyboardMarkup([[KeyboardButton("🔙 Back")]], resize_keyboard=True)
    await m.answer(f"✅ Mode set: {txt}\n\n📝 Now send your content!\n\n💡 Use 🔙 Back to change mode", reply_markup=back_kb)

@dp.message_handler(content_types=[types.ContentType.PHOTO, types.ContentType.VIDEO])
async def handle_media(m: types.Message):
    uid = m.from_user.id
    info = ctx.get(uid)
    if not info:
        return
    mode = info.get("mode")
    if mode in ("media_only", "media_caption"):
        album_buf[uid].append(m)

@dp.message_handler(lambda m: m.text == "🛠 Panel")
async def panel_btn(m: types.Message):
    uid = m.from_user.id
    for cid in CHANNELS:
        if await is_owner(cid, uid):
            return await m.answer("🛠 Owner panel:", reply_markup=menu_kb)
    await m.answer("❌ Only channel owner can use panel.", reply_markup=start_kb)

@dp.message_handler(lambda m: m.text == "✏️ Change limit")
async def change_limit_start(m: types.Message):
    uid = m.from_user.id
    for cid in CHANNELS:
        if await is_owner(cid, uid):
            owner_stats[uid] = "change_limit"
            return await m.answer("Select channel to change limit:", reply_markup=chan_kb)
    await m.answer("❌ Only channel owner can change limits.", reply_markup=menu_kb)

@dp.message_handler(lambda m: m.text == "👥 Admin limits")
async def admin_limits_menu(m: types.Message):
    uid = m.from_user.id
    for cid in CHANNELS:
        if await is_owner(cid, uid):
            return await m.answer("👥 Admin limits management:", reply_markup=admin_menu_kb)
    await m.answer("❌ Only channel owner can manage admin limits.", reply_markup=menu_kb)

@dp.message_handler(lambda m: m.text == "🔙 Back to menu")
async def back_to_menu(m: types.Message):
    uid = m.from_user.id
    for cid in CHANNELS:
        if await is_owner(cid, uid):
            return await m.answer("🛠 Owner panel:", reply_markup=menu_kb)
    await m.answer("❌ Access denied.", reply_markup=start_kb)

@dp.message_handler(lambda m: m.text == "➕ Set admin limit")
async def set_admin_limit_start(m: types.Message):
    uid = m.from_user.id
    for cid in CHANNELS:
        if await is_owner(cid, uid):
            owner_stats[uid] = "set_admin_limit"
            return await m.answer("Select channel to set admin limit:", reply_markup=chan_kb)
    await m.answer("❌ Only channel owner can set admin limits.", reply_markup=admin_menu_kb)

@dp.message_handler(lambda m: m.text == "📋 View admin limits")
async def view_admin_limits_start(m: types.Message):
    uid = m.from_user.id
    for cid in CHANNELS:
        if await is_owner(cid, uid):
            owner_stats[uid] = "view_admin_limits"
            return await m.answer("Select channel to view admin limits:", reply_markup=chan_kb)
    await m.answer("❌ Only channel owner can view admin limits.", reply_markup=admin_menu_kb)

@dp.message_handler(lambda m: m.text == "❌ Remove admin limit")
async def remove_admin_limit_start(m: types.Message):
    uid = m.from_user.id
    for cid in CHANNELS:
        if await is_owner(cid, uid):
            owner_stats[uid] = "remove_admin_limit"
            return await m.answer("Select channel to remove admin limit:", reply_markup=chan_kb)
    await m.answer("❌ Only channel owner can remove admin limits.", reply_markup=admin_menu_kb)

# === Обробник введення нового значення лимита для канала
@dp.message_handler(lambda m: m.from_user.id in awaiting_limit and m.text.isdigit())
async def apply_new_limit(m: types.Message):
    uid = m.from_user.id
    cid = awaiting_limit.pop(uid)
    new = int(m.text)
    await db.set_limit(cid, new)
    await m.answer(f"✅ New daily limit for {CHANNELS[cid]}: {new}", reply_markup=menu_kb)

# === Обработчик введения нового значения лимита для администратора
@dp.message_handler(lambda m: m.from_user.id in awaiting_admin_limit and m.text.isdigit())
async def apply_new_admin_limit(m: types.Message):
    uid = m.from_user.id
    limit_data = awaiting_admin_limit.pop(uid)
    admin_id = limit_data["admin_id"]
    cid = limit_data["channel_id"]
    new_limit = int(m.text)
    
    await db.set_admin_limit(admin_id, cid, new_limit)
    
    try:
        admin_member = await bot.get_chat_member(cid, admin_id)
        admin_name = admin_member.user.full_name or f"User {admin_id}"
    except:
        admin_name = f"User {admin_id}"
    
    await m.answer(
        f"✅ Set daily limit for {admin_name} in {CHANNELS[cid]}: {new_limit}",
        reply_markup=admin_menu_kb
    )

@dp.message_handler(lambda m: m.text == "📊 Today")
async def today_stats(m: types.Message):
    uid = m.from_user.id
    for cid in CHANNELS:
        if await is_owner(cid, uid):
            owner_stats[uid] = "today"
            return await m.answer("Select channel for stats:", reply_markup=chan_kb)
    await m.answer("❌ Only owners can view stats.", reply_markup=menu_kb)

@dp.message_handler(lambda m: m.text == "📈 All time")
async def all_time_stats(m: types.Message):
    uid = m.from_user.id
    for cid in CHANNELS:
        if await is_owner(cid, uid):
            owner_stats[uid] = "all_time"
            return await m.answer("Select channel for stats:", reply_markup=chan_kb)
    await m.answer("❌ Only owners can view stats.", reply_markup=menu_kb)

@dp.message_handler(lambda m: m.text in CHANNELS.values())
async def handle_channel_selection(m: types.Message):
    uid = m.from_user.id
    sel = m.text
    cid = next((k for k, v in CHANNELS.items() if v == sel), None)
    if not cid:
        return await m.answer("❌ Unknown channel.")

    action = owner_stats.get(uid)

    if action == "post" and await is_admin(cid, uid):
        post_buffer[uid] = {"channel": cid}
        owner_stats.pop(uid, None)
        ctx[uid] = {"chat_id": cid}
        return await m.answer("✅ Channel selected.\nChoose posting mode:", reply_markup=mode_kb)

    elif action == "change_limit" and await is_owner(cid, uid):
        awaiting_limit[uid] = cid
        owner_stats.pop(uid, None)
        
        # Add back button for limit input
        back_kb = ReplyKeyboardMarkup([[KeyboardButton("🔙 Back")]], resize_keyboard=True)
        return await m.answer(f"Enter new daily limit for '{sel}':", reply_markup=back_kb)

    elif action == "set_admin_limit" and await is_owner(cid, uid):
        # Получаем список администраторов
        admins = await get_channel_admins(cid)
        if not admins:
            return await m.answer("❌ No admins found in this channel.", reply_markup=admin_menu_kb)
        
        admin_buttons = []
        for admin_id, admin_name in admins:
            # Показываем только администраторов, не владельцев
            if not await is_owner(cid, admin_id):
                admin_buttons.append([KeyboardButton(f"{admin_name} ({admin_id})")])
        
        if not admin_buttons:
            return await m.answer("❌ No admins (non-owners) found in this channel.", reply_markup=admin_menu_kb)
        
        admin_buttons.append([KeyboardButton("🔙 Back")])
        admin_kb = ReplyKeyboardMarkup(admin_buttons, resize_keyboard=True)
        
        awaiting_admin_limit[uid] = {"channel_id": cid, "step": "select_admin"}
        return await m.answer("Select admin to set limit for:", reply_markup=admin_kb)

    elif action == "view_admin_limits" and await is_owner(cid, uid):
        admin_limits = await db.get_all_admin_limits(cid)
        channel_limit = await db.get_limit(cid)
        
        if not admin_limits:
            msg = f"📋 Admin limits in {sel}:\nNo individual admin limits set.\nDefault channel limit: {channel_limit}"
        else:
            lines = [f"📋 Admin limits in {sel}:"]
            lines.append(f"Default channel limit: {channel_limit}")
            lines.append("\nIndividual limits:")
            
            for admin_id, limit in admin_limits:
                try:
                    member = await bot.get_chat_member(cid, admin_id)
                    name = member.user.full_name or f"User {admin_id}"
                except:
                    name = f"User {admin_id}"
                lines.append(f"- {name}: {limit}")
            
            msg = "\n".join(lines)
        
        return await m.answer(msg, reply_markup=admin_menu_kb)

    elif action == "remove_admin_limit" and await is_owner(cid, uid):
        admin_limits = await db.get_all_admin_limits(cid)
        
        if not admin_limits:
            return await m.answer("❌ No individual admin limits set for this channel.", reply_markup=admin_menu_kb)
        
        admin_buttons = []
        for admin_id, limit in admin_limits:
            try:
                member = await bot.get_chat_member(cid, admin_id)
                name = member.user.full_name or f"User {admin_id}"
            except:
                name = f"User {admin_id}"
            admin_buttons.append([KeyboardButton(f"{name} ({admin_id})")])
        
        admin_buttons.append([KeyboardButton("🔙 Back")])
        admin_kb = ReplyKeyboardMarkup(admin_buttons, resize_keyboard=True)
        
        awaiting_admin_limit[uid] = {"channel_id": cid, "step": "remove_admin"}
        return await m.answer("Select admin to remove limit for:", reply_markup=admin_kb)

    elif action in ("today", "all_time") and await is_owner(cid, uid):
        if action == "today":
            raw_stats = await db.get_today(cid)
            label = "📊 Today"
        else:
            raw_stats = await db.get_all_time(cid)
            label = "📈 All time"

        if not raw_stats:
            msg = f"{label} in {sel}: no data yet."
        else:
            lines = []
            for admin_id, count in raw_stats:
                try:
                    member = await bot.get_chat_member(cid, admin_id)
                    name = member.user.full_name
                except:
                    name = f"User {admin_id}"
                
                # Показываем индивидуальный лимит администратора
                admin_limit = await db.get_admin_limit(admin_id, cid)
                lines.append(f"- {name}: {count} (limit: {admin_limit})")
            msg = f"{label} in {sel}:\n" + "\n".join(lines)

        # ⛔ НЕ удаляем owner_stats[uid], чтобы разрешить повторный выбор каналов
        return await m.answer(msg, reply_markup=menu_kb)

    else:
        return await m.answer("❌ You are not allowed to perform this action.")

# Обработчик выбора администратора для установки лимита
@dp.message_handler(lambda m: m.from_user.id in awaiting_admin_limit)
async def handle_admin_selection(m: types.Message):
    uid = m.from_user.id
    limit_data = awaiting_admin_limit.get(uid)
    
    if not limit_data:
        return
    
    if m.text == "🔙 Back":
        awaiting_admin_limit.pop(uid, None)
        return await m.answer("👥 Admin limits management:", reply_markup=admin_menu_kb)
    
    # Извлекаем ID администратора из текста кнопки
    if "(" in m.text and ")" in m.text:
        try:
            admin_id = int(m.text.split("(")[-1].split(")")[0])
        except:
            return await m.answer("❌ Invalid admin selection.", reply_markup=admin_menu_kb)
    else:
        return await m.answer("❌ Invalid admin selection.", reply_markup=admin_menu_kb)
    
    if limit_data["step"] == "select_admin":
        awaiting_admin_limit[uid] = {
            "channel_id": limit_data["channel_id"],
            "admin_id": admin_id,
            "step": "enter_limit"
        }
        
        # Add back button for limit input
        back_kb = ReplyKeyboardMarkup([[KeyboardButton("🔙 Back")]], resize_keyboard=True)
        await m.answer(f"Enter daily limit for selected admin:", reply_markup=back_kb)
    
    elif limit_data["step"] == "remove_admin":
        await db.remove_admin_limit(admin_id, limit_data["channel_id"])
        
        try:
            admin_member = await bot.get_chat_member(limit_data["channel_id"], admin_id)
            admin_name = admin_member.user.full_name or f"User {admin_id}"
        except:
            admin_name = f"User {admin_id}"
        
        awaiting_admin_limit.pop(uid, None)
        await m.answer(
            f"✅ Removed individual limit for {admin_name}.\nThey will now use the default channel limit.",
            reply_markup=admin_menu_kb
        )

@dp.message_handler(lambda m: m.from_user.id in awaiting_limit and m.text.isdigit())
async def set_new_limit(m: types.Message):
    uid = m.from_user.id
    new = int(m.text)
    cid = awaiting_limit.pop(uid)
    await db.set_limit(cid, new)
    await m.answer(f"✅ New daily limit for {CHANNELS[cid]}: {new}", reply_markup=menu_kb)

@dp.message_handler(content_types=[types.ContentType.TEXT])
async def handle_text(m: types.Message):
    if m.text in ("🛠 Panel","✏️ Change limit","📊 Today","📈 All time","👥 Admin limits","➕ Set admin limit","📋 View admin limits","❌ Remove admin limit","🔙 Back to menu","🔙 Back to main","🔙 Back","❓ Help"):
        return
    uid = m.from_user.id
    info = ctx.get(uid)
    if not info:
        return
    cid  = info["chat_id"]
    mode = info.get("mode")
    
    # Используем индивидуальный лимит администратора вместо лимита канала
    limit = await db.get_admin_limit(uid, cid)
    used  = await db.get_count(uid, cid)
    
    if used >= limit:
        await m.answer(f"⚠️ {used}/{limit} reached.", reply_markup=start_kb)
        ctx.pop(uid, None)
        album_buf[uid].clear()
        return
    if mode == "text":
        # Preserve original message entities (links, formatting, etc.)
        await bot.send_message(cid, m.text, entities=m.entities)
    else:
        if album_buf.get(uid):
            media = []
            for i, msg in enumerate(album_buf[uid]):
                file_id = msg.photo[-1].file_id if msg.photo else msg.video.file_id
                cls = InputMediaPhoto if msg.photo else InputMediaVideo
                if len(album_buf[uid]) >= 2:
                    if i == 0 and mode == "media_caption":
                        media.append(cls(file_id, caption=m.text, caption_entities=m.entities))
                    else:
                        media.append(cls(file_id))
                else:
                    if msg.photo:
                        await bot.send_photo(cid, file_id, caption=m.text if mode == "media_caption" else None, caption_entities=m.entities if mode == "media_caption" else None)
                    else:
                        await bot.send_video(cid, file_id, caption=m.text if mode == "media_caption" else None, caption_entities=m.entities if mode == "media_caption" else None)
                    media = None
            if media:
                await bot.send_media_group(cid, media)
        else:
            # Preserve original message entities (links, formatting, etc.)
            await bot.send_message(cid, m.text, entities=m.entities)

    await db.inc_count(uid, cid)
    await m.answer(f"✅ Posted {used + 1}/{limit}", reply_markup=start_kb)
    ctx.pop(uid, None)
    album_buf[uid].clear()

async def main():
    """Главная функция для запуска бота и планировщика"""
    await db.init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запускаем планировщик сброса лимитов в фоне
    asyncio.create_task(reset_limits_scheduler())
    
    # Запускаем бота
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
