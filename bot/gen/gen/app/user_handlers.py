from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command
import os
import asyncio
import logging
import fal_client
import random
from datetime import datetime, timedelta
from collections import defaultdict
from PIL import Image
import requests
from io import BytesIO
from aiogram.types import InputFile
from aiogram.types.input_file import BufferedInputFile

from config import TOKEN
from app.db import Database

bot = Bot(token=TOKEN)
user_handlers = Router()

# Initialize database
db = Database('bot_database.db')

# Dictionary to store user usage data
user_usage = defaultdict(list)
MAX_USES_PER_DAY = 10

# Configure FAL API
os.environ["FAL_KEY"] = "c96cf91d-c066-437f-b3c5-9bb0f46b3313:d301951fae038237fdba3532a9e07843"
DEFAULT_LORA = "https://v3.fal.media/files/monkey/WJzfPtEbCoNV-nCanhQek_pytorch_lora_weights.safetensors"
BANK_NOTE_LORA = "https://v3.fal.media/files/elephant/nJ_6LSsC--pHh5Pnt4VJS_pytorch_lora_weights.safetensors"

# Default random images for flux-pro API (can be updated via admin)
random_images_dir = 'random_images'
os.makedirs(random_images_dir, exist_ok=True)
# RANDOM_IMAGES больше не нужен, так как изображения хранятся в базе данных

async def get_telegram_file_url(file_id):
    bot = Bot(token=TOKEN)
    file = await bot.get_file(file_id)
    file_path = file.file_path
    return f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"

VALID_PARAMS = {
    "image_size": {
        "width": 768,  
        "height": 1024 
    },
    "num_inference_steps": 28,
    "guidance_scale": 3.5,
    "num_images": 1,
    "enable_safety_checker": False,
    "output_format": "jpeg",
    "loras": [{"path": DEFAULT_LORA, "scale": 1}]
}

GENCASH_PARAMS = {
    "image_size": {
        "width": 1920,
        "height": 1080 
    },
    "num_inference_steps": 28,
    "guidance_scale": 3.5,
    "num_images": 1,
    "enable_safety_checker": True,
    "output_format": "jpeg",
    "loras": [
        {"path": DEFAULT_LORA, "scale": 1.0},
        {"path": BANK_NOTE_LORA, "scale": 1.0}
    ]
}

async def check_user_limit(user_id: int) -> bool:
    """Check if user has exceeded the daily limit"""
    if await db.is_admin(user_id):
        return True
    
    now = datetime.now()
    user_usage[user_id] = [use_time for use_time in user_usage[user_id] 
                          if now - use_time < timedelta(days=1)]
    
    return len(user_usage[user_id]) < MAX_USES_PER_DAY

async def generate_with_fal(prompt: str):
    """Generate image using FAL API"""
    def on_queue_update(update):
        if isinstance(update, fal_client.InProgress):
            for log in update.logs:
                print(log["message"])

    try:
        result = fal_client.subscribe(
            "fal-ai/flux-lora",
            arguments={
                "prompt": prompt,
                **VALID_PARAMS
            },
            with_logs=True,
            on_queue_update=on_queue_update,
        )
        
        if not result.get("images"):
            raise ValueError("No images in response")
            
        return result["images"][0]["url"]  # Return the first image URL
        
    except Exception as e:
        print(f"Error during generation: {str(e)}")
        raise

async def generate_with_flux_pro(prompt: str):
    """Generate image using flux-pro API with random Telegram CDN image"""
    def on_queue_update(update):
        if isinstance(update, fal_client.InProgress):
            for log in update.logs:
                print(log["message"])

    try:
        # Получаем случайное изображение из базы данных
        random_image = await db.get_random_image()
        if not random_image:
            raise ValueError("No images available for generation")
        
        file_id, file_path = random_image
        image_url = await get_telegram_file_url(file_id)
        
        result = fal_client.subscribe(
            "fal-ai/flux-pro/kontext",
            arguments={
                "prompt": prompt,
                "image_url": image_url,
                "image_size": "portrait_4_3",
                "num_inference_steps": 28,
                "guidance_scale": 3.5,
                "num_images": 1,
                "enable_safety_checker": True,
                "output_format": "jpeg"
            },
            with_logs=True,
            on_queue_update=on_queue_update,
        )
        
        if not result.get("images"):
            raise ValueError("No images in response")
            
        return result["images"][0]["url"]  # Return the first image URL
        
    except Exception as e:
        print(f"Error during generation: {str(e)}")
        raise

async def generate_with_fal_gencash(prompt: str):
    """Generate image using FAL API with two LoRAs for gencash command"""
    def on_queue_update(update):
        if isinstance(update, fal_client.InProgress):
            for log in update.logs:
                print(log["message"])

    try:
        result = fal_client.subscribe(
            "fal-ai/flux-lora",
            arguments={
                "prompt": prompt,
                **GENCASH_PARAMS
            },
            with_logs=True,
            on_queue_update=on_queue_update,
        )
        
        if not result.get("images"):
            raise ValueError("No images in response")
            
        return result["images"][0]["url"]  # Return the first image URL
        
    except Exception as e:
        print(f"Error during generation: {str(e)}")
        raise

@user_handlers.message(Command("gen"))
async def generate_image(message: types.Message):
    user_id = message.from_user.id
    
    if not await check_user_limit(user_id):
        await message.reply(f"⚠️ You've reached your daily limit of {MAX_USES_PER_DAY} generations. Please try again tomorrow.")
        return
    
    prompt = message.text.split("/gen", 1)[1].strip()
    
    if not prompt:
        await message.reply("Please provide a prompt after /gen command")
        return
    
    processing_msg = await message.reply("vajunnie dreaming….")
    
    try:
        # Record the usage (except for admins)
        if not await db.is_admin(user_id):
            user_usage[user_id].append(datetime.now())
        
        full_prompt = f"the creature character is {prompt}"
        image_url = await generate_with_flux_pro(full_prompt)
        print(image_url)
        await message.reply_photo(
            photo=image_url
        )
        
    except Exception as e:
        print(f"Error: {str(e)}")
        if not await db.is_admin(user_id) and user_usage[user_id]:
            user_usage[user_id].pop()
        await message.reply("❌ Error generating image. Please try again.")
        
    finally:
        await bot.delete_message(
            chat_id=message.chat.id,
            message_id=processing_msg.message_id
        )

@user_handlers.message(Command("gencash"))
async def generate_cash_image(message: types.Message):
    user_id = message.from_user.id
    
    if not await check_user_limit(user_id):
        await message.reply(f"⚠️ You've reached your daily limit of {MAX_USES_PER_DAY} generations. Please try again tomorrow.")
        return
    
    user_prompt = message.text.split("/gencash", 1)[1].strip()
    
    if not user_prompt:
        await message.reply("Please provide a prompt after /gencash command")
        return
    
    # Prepend the hidden prompt to user's input
    full_prompt = f"exoticnote exotic bank note of vajunnie {user_prompt}"
    
    processing_msg = await message.reply("vajunnie dreaming….")
    
    try:
        # Record the usage (except for admins)
        if not await db.is_admin(user_id):
            user_usage[user_id].append(datetime.now())
        
        image_url = await generate_with_fal_gencash(full_prompt)
        print(image_url)
        await message.reply_photo(
            photo=image_url
        )
        
    except Exception as e:
        print(f"Error: {str(e)}")
        if not await db.is_admin(user_id) and user_usage[user_id]:
            user_usage[user_id].pop()
        await message.reply("❌ Error generating image. Please try again.")
        
    finally:
        await bot.delete_message(
            chat_id=message.chat.id,
            message_id=processing_msg.message_id
        )

@user_handlers.message(Command("tickergen"))
async def tickergen_image(message: types.Message):
    user_id = message.from_user.id

    if not await check_user_limit(user_id):
        await message.reply(f"⚠️ You've reached your daily limit of {MAX_USES_PER_DAY} generations. Please try again tomorrow.")
        return

    prompt = message.text.split("/tickergen", 1)[1].strip()

    if not prompt:
        await message.reply("Please provide a prompt after /tickergen command")
        return

    processing_msg = await message.reply("vajunnie dreaming….")

    try:
        # Record the usage (except for admins)
        if not await db.is_admin(user_id):
            user_usage[user_id].append(datetime.now())

        full_prompt = f"the creature character is {prompt}"
        image_url = await generate_with_flux_pro(full_prompt)
        print(image_url)

        # Download generated image
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content)).convert("RGBA")

        # Open sticker
        sticker = Image.open("ticker-text.png").convert("RGBA")
        # Resize sticker if it's too big
        max_sticker_width = img.width // 3
        if sticker.width > max_sticker_width:
            ratio = max_sticker_width / sticker.width
            sticker = sticker.resize((int(sticker.width * ratio), int(sticker.height * ratio)), Image.Resampling.LANCZOS)

        # Place sticker at the top center
        x = (img.width - sticker.width) // 2
        y = 20
        img.paste(sticker, (x, y), sticker)

        # Save to buffer
        output = BytesIO()
        img = img.convert("RGB")
        img.save(output, format="JPEG")
        output.seek(0)

        await message.reply_photo(photo=BufferedInputFile(output.read(), filename="result.jpg"))

    except Exception as e:
        print(f"Error: {str(e)}")
        if not await db.is_admin(user_id) and user_usage[user_id]:
            user_usage[user_id].pop()
        await message.reply("❌ Error generating image. Please try again.")

    finally:
        await bot.delete_message(
            chat_id=message.chat.id,
            message_id=processing_msg.message_id
        )