import asyncio
from aiogram import Bot, Dispatcher, F, types, Router
from aiogram.types import Message, WebAppInfo, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import os

import app.keyboard as kb
import random
from config import TOKEN

from app.db import Database

random_images_dir = 'random_images'
os.makedirs(random_images_dir, exist_ok=True)

admin_handlers = Router()
bot = Bot(token=TOKEN)

# Инициализация базы данных
db = Database('bot_database.db')

# Инициализация администраторов больше не нужна, так как все управление происходит через админ панель

async def migrate_existing_images():
    """Миграция существующих изображений из папки в базу данных"""
    import glob
    existing_images = glob.glob(os.path.join(random_images_dir, "random_*.jpg"))
    
    migrated_count = 0
    for image_path in existing_images:
        # Извлекаем file_id из имени файла
        filename = os.path.basename(image_path)
        if filename.startswith("random_") and filename.endswith(".jpg"):
            file_id = filename[7:-4]  # Убираем "random_" и ".jpg"
            
            # Проверяем, есть ли уже в базе
            images = await db.get_all_random_images()
            existing_file_ids = [img[1] for img in images]
            
            if file_id not in existing_file_ids:
                await db.add_random_image(file_id, image_path)
                migrated_count += 1
    
    return migrated_count

class adminStates(StatesGroup):
    enter_password = State()
    add_random_image = State()
    delete_random_image = State()
    add_admin = State()
    delete_admin = State()

admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='📸 Add Random Image')],
        [KeyboardButton(text='📋 View Random Images')],
        [KeyboardButton(text='🗑 Delete Random Image')],
        [KeyboardButton(text='👤 Add Admin'), KeyboardButton(text='🗑 Delete Admin')],
        [KeyboardButton(text='👥 View Admins')],
        [KeyboardButton(text='🏘 Home')]
    ],
    resize_keyboard=True
)

@admin_handlers.message(F.text == '/admin')
async def cmd_admin(message: Message, state: FSMContext):
    await message.answer("🔐 Please enter the admin panel password to proceed:", parse_mode='Markdown')
    await state.set_state(adminStates.enter_password)

@admin_handlers.message(adminStates.enter_password)
async def state_enter_password(message: Message, state: FSMContext):
    if not message.text or not message.from_user:
        await message.answer("🚫 Invalid input. Please try again.", parse_mode='Markdown')
        return
    
    password = message.text
    user_id = message.from_user.id
    username = message.from_user.username or str(message.from_user.id)

    if password == 'douglasmcrae':
        # Мигрируем существующие изображения при первом входе
        migrated_count = await migrate_existing_images()
        if migrated_count > 0:
            await message.answer(f"🔄 Migrated {migrated_count} existing images to database.")
        
        await message.answer(f"👋🏻 Welcome to the admin panel, *{username}*!", parse_mode='Markdown', reply_markup=admin_keyboard)
        await state.clear()
    else:
        await message.answer("🚫 Incorrect password. Please try again.", parse_mode='Markdown')
        return

@admin_handlers.message(F.text == '📸 Add Random Image')
async def add_random_image_callback(message: Message, state: FSMContext):
    await message.answer("📸 Please send the image file for the random image pool:")
    await state.set_state(adminStates.add_random_image)

@admin_handlers.message(adminStates.add_random_image)
async def handle_add_random_image(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer("❌ Please send a photo file.")
        return
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    file_path = file.file_path
    if not file_path:
        await message.answer("❌ Failed to get file path.")
        return
    file_name = f"random_{photo.file_id}.jpg"
    dest_path = os.path.join(random_images_dir, file_name)
    await bot.download_file(file_path, dest_path)
    
    # Добавляем в базу данных
    if await db.add_random_image(photo.file_id, dest_path):
        await message.answer(f"✅ Image added successfully to database!", reply_markup=admin_keyboard)
    else:
        await message.answer("❌ Failed to add image to database.", reply_markup=admin_keyboard)
    
    await state.clear()

@admin_handlers.message(F.text == '📋 View Random Images')
async def view_random_images_callback(message: Message):
    images = await db.get_all_random_images()
    if not images:
        await message.answer("📋 No random images configured yet.", reply_markup=admin_keyboard)
        return
    image_list = "\n".join([f"{i+1}. {os.path.basename(img[2])} (ID: {img[0]})\n  Added: {img[3]}" for i, img in enumerate(images)])
    await message.answer(f"📋 Current random images:\n\n{image_list}", reply_markup=admin_keyboard)

@admin_handlers.message(F.text == '🏘 Home')
async def home_callback(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏘 Welcome back to the admin panel!", reply_markup=admin_keyboard)

@admin_handlers.message(F.text == '🗑 Delete Random Image')
async def ask_delete_random_image(message: Message, state: FSMContext):
    images = await db.get_all_random_images()
    if not images:
        await message.answer("No images to delete.", reply_markup=admin_keyboard)
        return
    image_list = "\n".join([f"{i+1}. {os.path.basename(img[2])} (ID: {img[0]})" for i, img in enumerate(images)])
    await message.answer(f"Select the number of the image to delete:\n\n{image_list}", reply_markup=admin_keyboard)
    await state.set_state(adminStates.delete_random_image)

@admin_handlers.message(adminStates.delete_random_image)
async def delete_random_image(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Please enter a valid image number.", reply_markup=admin_keyboard)
        return
    try:
        idx = int(message.text.strip()) - 1
        images = await db.get_all_random_images()
        if idx < 0 or idx >= len(images):
            raise ValueError
        image_id = images[idx][0]  # Получаем ID изображения из базы
    except Exception:
        await message.answer("Please enter a valid image number.", reply_markup=admin_keyboard)
        return
    
    # Удаляем из базы данных
    file_path = await db.remove_random_image(image_id)
    if file_path:
        try:
            os.remove(file_path)  # Удаляем файл с диска
        except Exception:
            pass
        await message.answer("✅ Image deleted from database and disk!", reply_markup=admin_keyboard)
    else:
        await message.answer("❌ Failed to delete image.", reply_markup=admin_keyboard)
    
    await state.clear()

@admin_handlers.message(F.text == '👤 Add Admin')
async def add_admin_callback(message: Message, state: FSMContext):
    await message.answer("👤 Please send the user ID of the person you want to add as admin:")
    await state.set_state(adminStates.add_admin)

@admin_handlers.message(adminStates.add_admin)
async def handle_add_admin(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Please enter a valid user ID (number).", reply_markup=admin_keyboard)
        return
    try:
        user_id = int(message.text.strip())
        username = f"user_{user_id}"  # Временное имя, может быть обновлено при первом взаимодействии
        
        if await db.add_admin(user_id, username):
            await message.answer(f"✅ Admin added successfully!\nUser ID: {user_id}", reply_markup=admin_keyboard)
        else:
            await message.answer(f"❌ Failed to add admin. User ID: {user_id}", reply_markup=admin_keyboard)
    except ValueError:
        await message.answer("❌ Please enter a valid user ID (number).", reply_markup=admin_keyboard)
        return
    
    await state.clear()

@admin_handlers.message(F.text == '🗑 Delete Admin')
async def delete_admin_callback(message: Message, state: FSMContext):
    admins = await db.get_all_admins()
    if not admins:
        await message.answer("👥 No admins found.", reply_markup=admin_keyboard)
        return
    
    admin_list = "\n".join([f"{i+1}. {admin[1]} (ID: {admin[0]})" for i, admin in enumerate(admins)])
    await message.answer(f"👥 Current admins:\n\n{admin_list}\n\nEnter the user ID of the admin you want to remove:")
    await state.set_state(adminStates.delete_admin)

@admin_handlers.message(adminStates.delete_admin)
async def handle_delete_admin(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Please enter a valid user ID (number).", reply_markup=admin_keyboard)
        return
    try:
        user_id = int(message.text.strip())
        
        if await db.remove_admin(user_id):
            await message.answer(f"✅ Admin removed successfully!\nUser ID: {user_id}", reply_markup=admin_keyboard)
        else:
            await message.answer(f"❌ Admin not found or failed to remove.\nUser ID: {user_id}", reply_markup=admin_keyboard)
    except ValueError:
        await message.answer("❌ Please enter a valid user ID (number).", reply_markup=admin_keyboard)
        return
    
    await state.clear()

@admin_handlers.message(F.text == '👥 View Admins')
async def view_admins_callback(message: Message):
    admins = await db.get_all_admins()
    if not admins:
        await message.answer("👥 No admins found.", reply_markup=admin_keyboard)
        return
    
    admin_list = "\n".join([f"• {admin[1]} (ID: {admin[0]})\n  Added: {admin[2]}" for admin in admins])
    await message.answer(f"👥 Current admins:\n\n{admin_list}", reply_markup=admin_keyboard)

