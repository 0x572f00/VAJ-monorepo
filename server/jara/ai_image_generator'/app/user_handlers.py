from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command
import os
import asyncio
import logging
import fal_client
from datetime import datetime, timedelta
from collections import defaultdict

from config import TOKEN, ADMINS

bot = Bot(token=TOKEN)
user_handlers = Router()

# Dictionary to store user usage data
user_usage = defaultdict(list)
MAX_USES_PER_DAY = 10

# Configure FAL API
os.environ["FAL_KEY"] = "c96cf91d-c066-437f-b3c5-9bb0f46b3313:d301951fae038237fdba3532a9e07843"
DEFAULT_LORA = "https://github.com/0x572f00/VAJ-monorepo/raw/refs/heads/main/lora/vajunnie.safetensors"

VALID_PARAMS = {
    "image_size": {
        "width": 768,   # Ширина изображения
        "height": 1024   # Высота изображения (соотношение 4:5)
    },
    "num_inference_steps": 28,
    "guidance_scale": 3.5,
    "num_images": 1,
    "enable_safety_checker": True,
    "output_format": "jpeg",
    "loras": [{"path": DEFAULT_LORA, "scale": 1}]
}


def check_user_limit(user_id: int) -> bool:
    """Check if user has exceeded the daily limit"""
    if user_id in ADMINS:
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

@user_handlers.message(Command("gen"))
async def generate_image(message: types.Message):
    user_id = message.from_user.id
    
    if not check_user_limit(user_id):
        await message.reply(f"⚠️ You've reached your daily limit of {MAX_USES_PER_DAY} generations. Please try again tomorrow.")
        return
    
    prompt = message.text.split("/gen", 1)[1].strip()
    
    if not prompt:
        await message.reply("Please provide a prompt after /gen command")
        return
    
    processing_msg = await message.reply("Generating image...")
    
    try:
        # Record the usage (except for admins)
        if user_id not in ADMINS:
            user_usage[user_id].append(datetime.now())
        
        image_url = await generate_with_fal(prompt)
        print(image_url)
        await message.reply_photo(
            photo=image_url
        )
        
    except Exception as e:
        print(f"Error: {str(e)}")
        if user_id not in ADMINS and user_usage[user_id]:
            user_usage[user_id].pop()
        await message.reply("❌ Error generating image. Please try again.")
        
    finally:
        await bot.delete_message(
            chat_id=message.chat.id,
            message_id=processing_msg.message_id
        )