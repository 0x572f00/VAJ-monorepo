import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram import F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
import logging
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

ADMIN_GROUP_ID = -4981041969

#API_TOKEN = "8159703179:AAH2W0GMnQcfxgT3dEkYBmbN1WLwHRnAOXo"  # Замініть на свій токен
API_TOKEN = "7565724761:AAHyNCjj_DxkZaOhiKlbUW6lra-IPEGI3t8"

# Ініціалізація бота та диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VipForm(StatesGroup):
    full_name = State()
    account_number = State()
    balance = State()
    email = State()
    summary = State()

class CountryForm(StatesGroup):
    custom_country = State()
    amount = State()

class VantageVipForm(StatesGroup):
    full_name = State()
    uid = State()
    balance = State()
    email = State()
    summary = State()

class OctaVipForm(StatesGroup):
    full_name = State()
    uid = State()
    balance = State()
    email = State()
    summary = State()

# Обробник команди /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_name = message.from_user.first_name if message.from_user else "there"
    logger.info(f"/start від {user_name} (id={message.from_user.id if message.from_user else 'unknown'})")
    hello_message = f"Hey {user_name}!  Hope you're doing well!\n\n Secure your spot in Bugatti Bob's VIP Circle by answering 3 quick questions! 💼"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="YES Bob", callback_data="yes_ben")],
            [InlineKeyboardButton(text="No Bob", callback_data="no_ben")]
        ]
    )
    
    await message.answer(hello_message)
    await message.answer("Do you have any trading experience?", reply_markup=keyboard)

@dp.callback_query(F.data == "no_ben")
async def handle_no_ben(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="UK", callback_data="country_uk")],
            [InlineKeyboardButton(text="USA", callback_data="country_usa")],
            [InlineKeyboardButton(text="Germany", callback_data="country_germany")],
            [InlineKeyboardButton(text="India", callback_data="country_india")],
            [InlineKeyboardButton(text="Australia", callback_data="country_australia")],
            [InlineKeyboardButton(text="Nigeria", callback_data="country_nigeria")],
            [InlineKeyboardButton(text="Singapore", callback_data="country_singapore")],
            [InlineKeyboardButton(text="Romania", callback_data="country_romania")],
            [InlineKeyboardButton(text="Iran/Iraq", callback_data="country_iran_iraq")],
            [InlineKeyboardButton(text="Others", callback_data="country_others")],
        ]
    )

    await callback.message.answer("Thank you, which country do you live in?", reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data == "yes_ben")
async def handle_yes_ben(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Vantage", callback_data="broker_vantage")],
            [InlineKeyboardButton(text="ICMarkets", callback_data="broker_icmarkets")],
            [InlineKeyboardButton(text="Exness", callback_data="broker_exness")],
            [InlineKeyboardButton(text="T4Trade", callback_data="broker_t4trade")],
            [InlineKeyboardButton(text="Fxcess", callback_data="broker_fxcess")],
            [InlineKeyboardButton(text="OctaFX", callback_data="broker_octafx")],
            [InlineKeyboardButton(text="Others", callback_data="broker_others")],
        ]
    )
    await callback.message.answer("Which broker are you trading with?", reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data.in_(["broker_icmarkets", "broker_exness", "broker_t4trade", "broker_fxcess", "broker_others","broker_octafx"]))
async def handle_other_brokers(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="UK", callback_data="country_uk")],
            [InlineKeyboardButton(text="USA", callback_data="country_usa")],
            [InlineKeyboardButton(text="Germany", callback_data="country_germany")],
            [InlineKeyboardButton(text="India", callback_data="country_india")],
            [InlineKeyboardButton(text="Australia", callback_data="country_australia")],
            [InlineKeyboardButton(text="Nigeria", callback_data="country_nigeria")],
            [InlineKeyboardButton(text="Singapore", callback_data="country_singapore")],
            [InlineKeyboardButton(text="Romania", callback_data="country_romania")],
            [InlineKeyboardButton(text="Iran/Iraq", callback_data="country_iran_iraq")],
            [InlineKeyboardButton(text="Others", callback_data="country_others")],
        ]
    )
    await callback.message.answer("Thank you, which country do you live in?", reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data == "country_usa")
async def handle_country_usa(callback: types.CallbackQuery):
    await callback.message.answer(
        "USA I see..\nUnfortunately I don't offer free VIP to my USA clients...\n\nIf there are any offers in zfuture, I'll be sure to let you know!"
        )
    await callback.answer()

# @dp.callback_query(F.data.in_(["country_australia", "country_singapore", "country_romania", "country_iran_iraq"]))
# async def handle_special_countries(callback: types.CallbackQuery):
#     user_name = callback.from_user.first_name if callback.from_user else "there"
#     # Перше текстове повідомлення
#     await callback.message.answer(f"Dear {user_name},\n\nIf you're seeing this message, congratulations! You've been selected as the winner for our FREE VIP Club.😤\n\nAll you need to do now is create an account using the link below and claim your 100% bonus to join my VIP Circle for free.🤯")
#     # Друге текстове повідомлення
#     await callback.message.answer("⚠️ Ps. This offer will only be valid for the next 13 minutes")
#     # Надсилання фото (замініть 'YOUR_PHOTO_FILE_ID_OR_URL' на свій file_id або URL)
#     chat_id = callback.message.chat.id
#     photo = FSInputFile("images/fxcessregisterstep.jpg")
#     await bot.send_photo(chat_id, photo)
#     # Інлайн-клавіатура (приклад)
#     keyboard = InlineKeyboardMarkup(
#         inline_keyboard=[
#             [InlineKeyboardButton(text="Next Step!", callback_data="next_step")],
#             [InlineKeyboardButton(text="I have Fxcess Acc", callback_data="i_have_fxcess_acc")],
#         ]
#     )
#     await callback.message.answer("<u>STEP 1/2</u> \n\nRegister your account within 2 minutes!\n\nCreate a FXCESS account and CLAIM your 100% deposit bonus!🤩\n\n📲https://go.fxcess.com/visit/?bta=35458&brand=fxcess\n\nTrading platform: MT4\n\nAccount Type: Classic\n\nBonus: 100% Sharing Bonus",
#      reply_markup=keyboard,
#      parse_mode="HTML"
#      )
#     await callback.answer()
#
# @dp.callback_query(F.data == "i_have_fxcess_acc")
# async def handle_i_have_fxcess_acc(callback: types.CallbackQuery, state: FSMContext):
#     await callback.message.answer(
#         "Kindly send click the link below to contact @wallstreetben\n\n"
#         "https://t.me/m/0vt0UX2QZTM1"
#     )
#     await state.clear()
#
#
#
# @dp.callback_query(F.data == "next_step")
# async def handle_next_step(callback: types.CallbackQuery):
#     chat_id = callback.message.chat.id
#     photo = FSInputFile("images/fxcessregisterstep.jpg")
#     await bot.send_photo(chat_id, photo)
#     keyboard = InlineKeyboardMarkup(
#         inline_keyboard=[
#             [InlineKeyboardButton(text="Ready for VIP", callback_data="ready_for_vip")]
#         ]
#     )
#     await callback.message.answer(
#         "<u>STEP 2/2!</u>\nNow everything is set up properly.. \n\nFinal step is to deposit, and join Bugatti Bob's VIP Circle!🥳\n\n📲Recommended deposit amount: 500USD and above! \n\n🥺Minimum deposit amount:\n400USD",
#         reply_markup=keyboard,
#         parse_mode="HTML"
#     )
#     await callback.answer()
#
# @dp.callback_query(F.data == "ready_for_vip")
# async def start_vip_form(callback: types.CallbackQuery, state: FSMContext):
#     await callback.message.answer("LAST STEP:\n\nFill in your details and you'll receive the VIP invite😇\n\nLet's go 🚀")
#     await callback.message.answer("Please let us know your\n\nFxcess Full Name: 👇")
#     await state.set_state(VipForm.full_name)
#     await callback.answer()
#
# @dp.message(VipForm.full_name)
# async def process_full_name(message: types.Message, state: FSMContext):
#     await state.update_data(full_name=message.text)
#     await message.answer("Fxcess Account Number: 👇")
#     await state.set_state(VipForm.account_number)
#
# @dp.message(VipForm.account_number)
# async def process_account_number(message: types.Message, state: FSMContext):
#     data = await state.get_data()
#     change_mode = data.get("change_mode")
#     await state.update_data(account_number=message.text)
#     if change_mode == "account_number":
#         # Після зміни одразу показуємо підсумок
#         data = await state.get_data()
#         summary = (
#             "Please double-check your credentials below and make sure your equity is 400USD and above to avoid rejection.⚠️\n\n"
#             f"Fxcess Account Number: {data['account_number']}\n"
#             f"Fxcess Balance: {data['balance']}\n\n"
#             "Please double-check it and follow all steps to avoid rejection.🤗"
#         )
#         keyboard = InlineKeyboardMarkup(
#             inline_keyboard=[
#                 [InlineKeyboardButton(text="Change Acc Number", callback_data="change_acc_number")],
#                 [InlineKeyboardButton(text="Change Acc Balance", callback_data="change_acc_balance")],
#                 [InlineKeyboardButton(text="Deposited & READY!", callback_data="deposited_ready")],
#             ]
#         )
#         await message.answer(summary, reply_markup=keyboard)
#         await state.set_state(VipForm.summary)
#         await state.update_data(change_mode=None)
#     else:
#         await message.answer("Account Balance: 👇")
#         await state.set_state(VipForm.balance)
#
# @dp.message(VipForm.balance)
# async def process_balance(message: types.Message, state: FSMContext):
#     data = await state.get_data()
#     change_mode = data.get("change_mode")
#     await state.update_data(balance=message.text)
#     if change_mode == "balance":
#         # Після зміни одразу показуємо підсумок
#         data = await state.get_data()
#         summary = (
#             "Please double-check your credentials below and make sure your equity is 400USD and above to avoid rejection.⚠️\n\n"
#             f"Fxcess Account Number: {data['account_number']}\n"
#             f"Fxcess Balance: {data['balance']}\n\n"
#             "Please double-check it and follow all steps to avoid rejection.🤗"
#         )
#         keyboard = InlineKeyboardMarkup(
#             inline_keyboard=[
#                 [InlineKeyboardButton(text="Change Acc Number", callback_data="change_acc_number")],
#                 [InlineKeyboardButton(text="Change Acc Balance", callback_data="change_acc_balance")],
#                 [InlineKeyboardButton(text="Deposited & READY!", callback_data="deposited_ready")],
#             ]
#         )
#         await message.answer(summary, reply_markup=keyboard)
#         await state.set_state(VipForm.summary)
#         await state.update_data(change_mode=None)
#     else:
#         await message.answer("Email (For VIP Invitation): 👇")
#         await state.set_state(VipForm.email)
#
# @dp.message(VipForm.email)
# async def process_email(message: types.Message, state: FSMContext):
#     await state.update_data(email=message.text)
#     data = await state.get_data()
#     first = ("Please double-check your credentials below and make sure your equity is 400USD and above to avoid rejection.⚠️\n\n")
#     summary = (
#         f"Fxcess Account Number: {data['account_number']}\n"
#         f"Fxcess Balance: {data['balance']}\n\n"
#         "Please double-check it and follow all steps to avoid rejection.🤗"
#     )
#     keyboard = InlineKeyboardMarkup(
#         inline_keyboard=[
#             [InlineKeyboardButton(text="Change Acc Number", callback_data="change_acc_number")],
#             [InlineKeyboardButton(text="Change Acc Balance", callback_data="change_acc_balance")],
#             [InlineKeyboardButton(text="Deposited & READY!", callback_data="deposited_ready")],
#         ]
#     )
#     await message.answer(first + summary, reply_markup=keyboard)
#     await state.set_state(VipForm.summary)

@dp.callback_query(F.data == "change_acc_number", StateFilter(VipForm.summary))
async def change_acc_number(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Kindly key in the correct account number: 👇")
    await state.update_data(change_mode="account_number")
    await state.set_state(VipForm.account_number)
    await callback.answer()

@dp.callback_query(F.data == "change_acc_balance", StateFilter(VipForm.summary))
async def change_acc_balance(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Kindly key in the correct balance: 👇")
    await state.update_data(change_mode="balance")
    await state.set_state(VipForm.balance)
    await callback.answer()

@dp.callback_query(F.data == "deposited_ready", VipForm.summary)
async def deposited_ready(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Thank you! Your data has been submitted for review. You'll receive your VIP invite soon! 🥳")
    await state.clear()
    await callback.answer()

@dp.callback_query(F.data.in_(["broker_vantage", "vantage_have_acc"]))
async def handle_broker_vantage(callback: types.CallbackQuery):
    # 1. Перше повідомлення з кнопкою DONE
    keyboard_done = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="DONE", callback_data="vantage_done")]
        ]
    )
    await callback.message.answer("Complete the steps below to CLAIM your FREE VIP slot NOW! 🆓")
    await callback.message.answer(
        "🟡 CLAIM your FREE VIP slot NOW! 🟡\n\n"
        "ps.It takes just 10 seconds!\n\n"
        "https://secure.vantagemarkets.com/profile/transfer-ib-affiliate\n\n"
        "Partnership Type: IB\n"
        "New IB code: BugattiFX\n"
        "Reason for Transfer: Free signals & education!",
        reply_markup=keyboard_done
    )

    # 2. Фото
    photo = FSInputFile("images/broker_vantagetransfer.jpg")
    await bot.send_photo(callback.message.chat.id, photo)

    # 3. Друге повідомлення з кнопкою NEXT STEP
    keyboard_next = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="NEXT STEP", callback_data="vantage_next_step")]
        ]
    )
    await callback.message.answer(
        "<b>❗IMPORTANT ❗\n🚫 Please close all positions before initiating transfer\n⏳ Wait for confirmation email before trading again</b>",
        reply_markup=keyboard_next,
        parse_mode="HTML"
    )
    await callback.answer()

@dp.callback_query(F.data.in_(["vantage_done", "vantage_next_step"]))
async def handle_vantage_last_step(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("LAST STEP:\n\nFill in your details and you'll receive the VIP invite🤩\n\nLet's go 🚀")
    await callback.message.answer("Please let us know your\n\nVantage Full Name:")
    await state.set_state(VantageVipForm.full_name)
    await callback.answer()

# @dp.callback_query(F.data == "broker_octafx")
# async def handle_broker_octafx(callback: types.CallbackQuery):
#     # 1. Перше повідомлення
#     await callback.message.answer(
#         "Complete the steps below to CLAIM your FREE VIP slot NOW! 🆓"
#     )
#
#     # 2. Фото
#     photo = FSInputFile("images/octaFX.jpg")
#     await bot.send_photo(callback.message.chat.id, photo)
#
#     # 3. Друге повідомлення з кнопкою DONE
#     keyboard_done = InlineKeyboardMarkup(
#         inline_keyboard=[
#             [InlineKeyboardButton(text="DONE", callback_data="octafx_done")]
#         ]
#     )
#     await callback.message.answer(
#         "🟡 CLAIM your FREE VIP slot NOW! 🟡\n\n"
#         "ps.It takes just 10 seconds!\n\n"
#         "https://my.octabroker.com/change-partner-request/?partner=14293994\n\n"
#         "Partnership Type: IB\n"
#         "New IB code:14293994\n"
#         "Reason for Transfer: Free signals & education!",
#         reply_markup=keyboard_done
#     )
#     await callback.answer()
#
# @dp.callback_query(F.data == "octafx_done")
# async def start_octa_vip_form(callback: types.CallbackQuery, state: FSMContext):
#     await callback.message.answer("Full Name: 👇")
#     await state.set_state(OctaVipForm.full_name)
#     await callback.answer()
#
# @dp.message(OctaVipForm.full_name)
# async def process_octa_full_name(message: types.Message, state: FSMContext):
#     await state.update_data(full_name=message.text)
#     await message.answer("OctaFX UID: 👇")
#     await state.set_state(OctaVipForm.uid)
#
# @dp.message(OctaVipForm.uid)
# async def process_octa_uid(message: types.Message, state: FSMContext):
#     await state.update_data(uid=message.text)
#     await message.answer("OctaFX Balance: 👇")
#     await state.set_state(OctaVipForm.balance)
#
# @dp.message(OctaVipForm.balance)
# async def process_octa_balance(message: types.Message, state: FSMContext):
#     await state.update_data(balance=message.text)
#     await message.answer("Email (For VIP Invitation): 👇")
#     await state.set_state(OctaVipForm.email)
#
# @dp.message(OctaVipForm.email)
# async def process_octa_email(message: types.Message, state: FSMContext):
#     await state.update_data(email=message.text)
#     data = await state.get_data()
#     summary = (
#         "Please double-check your credentials below and make sure your equity is 500USD and above to avoid rejection!⚠️"
#     )
#     await message.answer(summary)
#     summary2 = (
#         f"OctaFX UID: {data['uid']}. \nOctaFX Balance: {data['balance']}\n\nPlease double-check it and follow all steps to avoid rejection.🤗"
#     )
#     keyboard = InlineKeyboardMarkup(
#         inline_keyboard=[
#             [InlineKeyboardButton(text="Change OctaFX UID", callback_data="change_octa_uid")],
#             [InlineKeyboardButton(text="Change OctaFX Balance", callback_data="change_octa_balance")],
#             [InlineKeyboardButton(text="Deposited & READY!", callback_data="octa_deposited_ready")],
#         ]
#     )
#     await message.answer(summary2, reply_markup=keyboard)
#     await state.set_state(OctaVipForm.summary)
#
# @dp.callback_query(F.data == "change_octa_uid", StateFilter(OctaVipForm.summary))
# async def change_octa_uid(callback: types.CallbackQuery, state: FSMContext):
#     await callback.message.answer("OctaFX UID: 👇")
#     await state.set_state(OctaVipForm.uid)
#     await callback.answer()
#
# @dp.callback_query(F.data == "change_octa_balance", StateFilter(OctaVipForm.summary))
# async def change_octa_balance(callback: types.CallbackQuery, state: FSMContext):
#     await callback.message.answer("OctaFX Balance: 👇")
#     await state.set_state(OctaVipForm.balance)
#     await callback.answer()
#
# @dp.callback_query(F.data == "octa_deposited_ready", StateFilter(OctaVipForm.summary))
# async def octa_deposited_ready(callback: types.CallbackQuery, state: FSMContext):
#     await callback.message.answer("Thank you! Your data has been submitted for review. You'll receive your VIP invite soon! 🥳")
#     await state.clear()
#     await callback.answer()

# Обробник для всіх країн, крім Others
@dp.callback_query(F.data.in_([
    "country_uk", "country_germany", "country_india", "country_nigeria", "country_australia", "country_singapore", "country_romania", "country_iran_iraq"
]))
async def handle_country(callback: types.CallbackQuery, state: FSMContext):
    country_map = {
        "country_uk": "UK",
        "country_germany": "Germany",
        "country_india": "India",
        "country_nigeria": "Nigeria"
    }
    country = country_map.get(callback.data, "your country")
    await state.update_data(selected_country=country)
    await callback.message.answer(f"Most of my members are from {country} as well!\n\nLastly, how much will you be trading with please?")
    await state.set_state(CountryForm.amount)
    await callback.answer()

# Обробник для Others
@dp.callback_query(F.data == "country_others")
async def handle_country_others(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Could you specify your country please?")
    await state.set_state(CountryForm.custom_country)
    await callback.answer()

# Приймаємо назву країни від користувача (Others)
@dp.message(CountryForm.custom_country)
async def process_custom_country(message: types.Message, state: FSMContext):
    country = message.text.strip()
    await state.update_data(selected_country=country)
    await message.answer(f"Most of my members are from {country} as well!\n\nLastly, how much will you be trading with please?")
    await state.set_state(CountryForm.amount)

# Приймаємо суму для будь-якої країни
@dp.message(CountryForm.amount)
async def process_country_amount(message: types.Message, state: FSMContext):
    amount = message.text.strip()
    data = await state.get_data()
    country = data.get("selected_country", "your country")
    user = message.from_user
    admin_text = (
        f"COUNTRY REGISTRATION\n"
        f"User: {user.full_name} (id: {user.id})\n"
        f"Country: {country}\n"
        f"Amount: {amount} USD\n"
    )
    try:
        await bot.send_message(ADMIN_GROUP_ID, admin_text)
    except Exception as e:
        print(f"Не вдалося надіслати повідомлення в групу: {e}")
    await state.clear()

    # 1. Awesome Sasha! ... (ім'я користувача)
    user_name = message.from_user.first_name if message.from_user and message.from_user.first_name else ""
    await message.answer(
        f"Awesome {user_name}! You're all set for the last FREE VIP spot! 🎉"
    )

    # 2. Фото
    photo = FSInputFile("images/vantageregistration.jpg")
    await message.bot.send_photo(message.chat.id, photo)

    # 3. STEP 1/3 + інструкція
    await message.answer(
        "STEP 1/3 \n\n"
        "Create a Vantage account and CLAIM your 100% deposit bonus!🤩\n\n"
        "https://www.vantagemarkets.com/open-live-account/?affid=MTQ2NjI3\n\n"
        "1. Enter your email 📧\n"
        "2. Click \"Send Code\" 📨\n"
        "3. Check your email for the code 📬\n"
        "4. Enter the code 🔢\n"
        "5. Set your password 🔐\n\n"
        "Click Create Account! (https://www.vantagemarkets.com/open-live-account/?affid=MTQ2NjI3)"
    )

    # 4. Повідомлення з інлайн-кнопками
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Next Step!", callback_data="vantage_next_step_2")],
            [InlineKeyboardButton(text="I have Vantage Acc", callback_data="vantage_have_acc")]
        ]
    )
    await message.answer(
        "STEP 1/3\n\nCreate a Vantage account and CLAIM your 100% deposit bonus!🤩",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "vantage_next_step_2")
async def handle_vantage_next_step_2(callback: types.CallbackQuery):
    # 1. Фото
    photo = FSInputFile("images/vantagestep2.jpg")
    await bot.send_photo(callback.message.chat.id, photo)

    # 2. Повідомлення з інлайн-кнопкою
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Final Step!", callback_data="vantage_final_step")]
        ]
    )
    await callback.message.answer(
        "STEP 2/3\n"
        "1. Choosing a trading platform\n"
        "MetaTrader 4 or MetaTrader 5\n\n"
        "2. Choose an Account Type\n"
        "Standard STP\n\n"
        "3. Account Currency\n"
        "USD, EUR or GBP only! \n"
        "Other currencies are not accepted\n\n"
        "Click Submit!",
        reply_markup=keyboard
    )
    await callback.answer()

@dp.callback_query(F.data == "vantage_final_step")
async def handle_vantage_final_step(callback: types.CallbackQuery):
    # 1. Фото
    photo = FSInputFile("images/vantage_final_step.jpg")
    await bot.send_photo(callback.message.chat.id, photo)

    # 2. Повідомлення з інлайн-кнопкою
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Ready for VIP", callback_data="ready_for_vip")]
        ]
    )
    await callback.message.answer(
        "STEP 3/3!\n"
        "Now everything is set up properly..\n\n"
        "Final step is to deposit, and join Bugatti Bob's VIP Circle!🥳\n\n"
        "Be sure to “Opt-in Now”!\n\n"
        "📲Recommended deposit amount: 500USD and above!",
        reply_markup=keyboard
    )
    await callback.answer()

@dp.callback_query(F.data == "ready_for_vip")
async def start_vantage_vip_form(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "LAST STEP:\n\nFill in your details and you'll receive the VIP invite🤩\n\nLet's go 🚀"
    )
    await callback.message.answer("Please let us know your\n\nVantage Full Name:")
    await state.set_state(VantageVipForm.full_name) 
    await callback.answer()

@dp.message(VantageVipForm.full_name)
async def process_vantage_full_name(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer("Vantage UID: 👇")
    await state.set_state(VantageVipForm.uid)

@dp.message(VantageVipForm.uid)
async def process_vantage_uid(message: types.Message, state: FSMContext):
    await state.update_data(uid=message.text)
    await message.answer("Vantage Balance: 👇")
    await state.set_state(VantageVipForm.balance)

@dp.message(VantageVipForm.balance)
async def process_vantage_balance(message: types.Message, state: FSMContext):
    await state.update_data(balance=message.text)
    await message.answer("Email (For VIP Invitation): 👇")
    await state.set_state(VantageVipForm.email)

@dp.message(VantageVipForm.email)
async def process_vantage_email(message: types.Message, state: FSMContext):
    await state.update_data(email=message.text)
    data = await state.get_data()
    summary = (
        "Please double-check your credentials below and make sure your equity is 500USD and above to avoid rejection!⚠️"
    )
    await message.answer(summary)
    summary2 = (
        f"Vantage UID: {data['uid']}. \nVantage Balance: {data['balance']}\n\nPlease double-check it and follow all steps to avoid rejection.🤗"
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Change Vantage UID", callback_data="change_vantage_uid")],
            [InlineKeyboardButton(text="Change Vantage Balance", callback_data="change_vantage_balance")],
            [InlineKeyboardButton(text="Deposited & READY!", callback_data="vantage_deposited_ready")],
        ]
    )
    await message.answer(summary2, reply_markup=keyboard)
    await state.set_state(VantageVipForm.summary)

@dp.callback_query(F.data == "change_vantage_uid", StateFilter(VantageVipForm.summary))
async def change_vantage_uid(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Vantage UID: 👇")
    await state.set_state(VantageVipForm.uid)
    await callback.answer()

@dp.callback_query(F.data == "change_vantage_balance", StateFilter(VantageVipForm.summary))
async def change_vantage_balance(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Vantage Balance: 👇")
    await state.set_state(VantageVipForm.balance)
    await callback.answer()

@dp.callback_query(F.data == "vantage_deposited_ready", StateFilter(VantageVipForm.summary))
async def vantage_deposited_ready(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = callback.from_user
    username = f"@{user.username}" if user.username else user.full_name
    admin_text = (
        f"VANTAGE VIP REGISTRATION\n"
        f"User: {username} (id: {user.id})\n"
        f"Full Name: {data.get('full_name')}\n"
        f"UID: {data.get('uid')}\n"
        f"Balance: {data.get('balance')}\n"
        f"Email: {data.get('email')}\n"
    )
    try:
        await bot.send_message(ADMIN_GROUP_ID, admin_text)
    except Exception as e:
        print(f"Не вдалося надіслати повідомлення в групу: {e}")
    await callback.message.answer("Thank you! Your data has been submitted for review. You'll receive your VIP invite soon! 🥳")
    await state.clear()
    await callback.answer()


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
