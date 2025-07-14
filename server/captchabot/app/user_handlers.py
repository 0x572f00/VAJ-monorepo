from aiogram import Bot, Dispatcher, F, types, Router
from aiogram.types import WebAppInfo, Message, CallbackQuery, ContentType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
from aiogram.enums.chat_member_status import ChatMemberStatus
from aiogram.filters import CommandStart, Command
import aiogram.exceptions as exceptions

import app.keyboard as kb
from config import TOKEN

import random
import string
from datetime import datetime
import requests

user_handlers = Router()
bot = Bot(token=TOKEN)

class CaptchaStates(StatesGroup):
    WAITING_CAPTCHA = State()
    PASSED_CAPTCHA = State()  # New state for users who passed captcha

EMOJIS = ["😀", "😎", "🤩", "🥳", "🤠", "👽", "🤖", "👻", "🐶", "🦊", "🐵", "🦄", "🐲", "🍕", "🎮", "🚀", "🌈", "⭐"]

async def generate_captcha():
    selected_emojis = random.sample(EMOJIS, 9)
    correct_emoji = random.choice(selected_emojis)
    return selected_emojis, correct_emoji

@user_handlers.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    current_state = await state.get_state()
    
    # Check if user already passed captcha
    if current_state == CaptchaStates.PASSED_CAPTCHA:
        data = await state.get_data()
        if 'invite_link' in data:
            await message.answer(f"✅ You already passed verification! Here's your invite link:\n\n{data['invite_link']}")
            return
    
    # If not, generate new captcha
    await state.clear()
    emojis, correct_emoji = await generate_captcha()
    
    builder = InlineKeyboardBuilder()
    for emoji in emojis:
        builder.button(text=emoji, callback_data=f"captcha_{emoji}")
    builder.adjust(3)
    
    await state.update_data(correct_emoji=correct_emoji)
    await state.set_state(CaptchaStates.WAITING_CAPTCHA)
    
    await message.answer(
        f"Please select an emoji: <b>{correct_emoji}</b>",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )

@user_handlers.callback_query(F.data.startswith("captcha_"), CaptchaStates.WAITING_CAPTCHA)
async def process_captcha(callback: CallbackQuery, state: FSMContext):
    selected_emoji = callback.data.split("_")[1]
    data = await state.get_data()
    correct_emoji = data.get("correct_emoji")
    user_id = callback.from_user.id
    
    if selected_emoji == correct_emoji:
        # Check if we already have a link in state data
        if 'invite_link' in data:
            await callback.message.delete()
            await callback.message.answer(text=f"✅ You already passed verification! Here's your invite link:\n\n{data['invite_link']}")
            await state.set_state(CaptchaStates.PASSED_CAPTCHA)
            await callback.answer()
            return
        
        # Create new invite link
        await callback.message.delete()
        
        export_resp = requests.get(
            f"https://api.telegram.org/bot{TOKEN}/createChatInviteLink",
            params={
                "chat_id": -1002503998427,
                "member_limit": 1,
                "name": f"invite_{user_id}",
                "creates_join_request": False
            }
        ).json()
        link = export_resp.get("result", {}).get("invite_link", "")

        # Save link to state data and set PASSED_CAPTCHA state
        await state.update_data(invite_link=link)
        await state.set_state(CaptchaStates.PASSED_CAPTCHA)
        
        tg_text = f"✅ You've been verified! Here's your invite link:\n\n{link}"
        await callback.message.answer(text=tg_text)
    else:
        emojis, correct_emoji = await generate_captcha()
        
        builder = InlineKeyboardBuilder()
        for emoji in emojis:
            builder.button(text=emoji, callback_data=f"captcha_{emoji}")
        builder.adjust(3)
        
        await state.update_data(correct_emoji=correct_emoji)
        
        await callback.message.edit_text(
            f"Incorrect selection. Please select an emoji: <b>{correct_emoji}</b>",
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
    
    await callback.answer()

    

# @user_handlers.message(Command("send_post"))
# async def cmd_start(message: Message, state: FSMContext):
#     kb = InlineKeyboardMarkup(inline_keyboard=[
#     [InlineKeyboardButton(text='captcha', url="https://t.me/vajunnie_security_bot")]
#     ])
#     await bot.send_message(chat_id=-1002599593499, text="pass the captcha 👇", reply_markup=kb)
