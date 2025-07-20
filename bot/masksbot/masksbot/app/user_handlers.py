import zipfile
from aiogram.filters import Command, CommandObject
from aiogram.types import Document
import shutil
import cv2
import numpy as np
import mediapipe as mp
import os
import random
from PIL import Image
from aiogram import Bot, Dispatcher, F, types, Router
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command
from config import TOKEN, ADMINS
from aiogram.filters import or_f

user_handlers = Router()
bot = Bot(token=TOKEN)
dp = Dispatcher()

mp_face_detection = mp.solutions.face_detection
face_detection = mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5)

class UploadStates(StatesGroup):
    UPLOAD_MASKS = State()
    UPLOAD_BANNERS = State()

def get_random_banner():
    banners_dir = "img/banners"
    banners = os.listdir(banners_dir)
    banner_file = random.choice(banners)
    banner_path = os.path.join(banners_dir, banner_file)
    return Image.open(banner_path)

class userStates(StatesGroup):
    MEME = State()
    TEXT_MEME = State()

def get_two_masks():
    masks_dir = "img/masks"
    # Получаем только файлы изображений
    masks = [f for f in os.listdir(masks_dir) 
             if os.path.isfile(os.path.join(masks_dir, f)) and 
             f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'))]
    
    if not masks:
        raise ValueError("No mask images found in masks directory")
    
    if len(masks) < 2:
        # Если масок меньше 2, используем одну и ту же маску дважды
        mask = Image.open(os.path.join(masks_dir, masks[0]))
        return mask, mask.copy()
    
    # Выбираем 2 случайные маски
    mask1, mask2 = random.sample(masks, 2)
    return Image.open(os.path.join(masks_dir, mask1)), Image.open(os.path.join(masks_dir, mask2))

@user_handlers.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Send me a picture and I'll apply the mask 🎭\n\n/meme - Apply masks to faces\n/tickermeme - Apply masks to faces + add ticker text\n/ticker - Only add ticker text (no face detection)")

# @user_handlers.message(Command("meme"))
# async def cmd_meme(message: Message, state: FSMContext):
#     await state.clear()
#     await state.set_state(userStates.MEME)
#     await message.answer("Reply with a picture to this message and I'll apply the mask 🎭")

# @user_handlers.message(Command("textmeme"))
# async def cmd_textmeme(message: Message, state: FSMContext):
#     await state.clear()
#     await state.set_state(userStates.TEXT_MEME)
#     await message.answer("Reply with a picture to this message and I'll apply the mask 🎭")

@user_handlers.message(F.photo, or_f(Command("meme"), Command("tickermeme"), Command("ticker")))
async def handle_meme_photo(message: Message, command: Command):
    user_id = message.from_user.id
    is_text_meme = command.command == "tickermeme"
    is_ticker_only = command.command == "ticker"

    photo = message.photo[-1]
    file_id = photo.file_id
    file_info = await bot.get_file(file_id)
    file = await bot.download_file(file_info.file_path)

    file_bytes = np.asarray(bytearray(file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    if img is None:
        return

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(img_rgb)

    # For ticker-only mode, skip face detection and mask application
    if is_ticker_only:
        # Only add ticker/banner without any face detection
        banner_img = get_random_banner()
        img_width, img_height = img_pil.size
        
        # Random scale factor for banner between 75% and 125%
        banner_scale_factor = random.uniform(0.75, 1.25)
        base_banner_width = int(img_width * 0.4)
        base_banner_height = int(img_height * 0.4)
        new_banner_width = int(base_banner_width * banner_scale_factor)
        new_banner_height = int(base_banner_height * banner_scale_factor)
        resized_banner = banner_img.resize((new_banner_width, new_banner_height), Image.LANCZOS)

        # Place banner in bottom left corner
        banner_x = 0
        banner_y = img_height - new_banner_height
        banner_position = (banner_x, banner_y)
        img_pil.paste(resized_banner, banner_position, resized_banner)
    else:
        # Original logic for meme and tickermeme commands (with face detection)
        results = face_detection.process(img_rgb)

        if not results.detections:
            await message.reply("😅 Face not found! Try another photo")
            return

        mask1, mask2 = get_two_masks()
        
        # Collect face bounding boxes for overlap checking
        face_boxes = []
        for detection in results.detections:
            bboxC = detection.location_data.relative_bounding_box
            img_h, img_w, _ = img.shape
            x, y, w, h = int(bboxC.xmin * img_w), int(bboxC.ymin * img_h), int(bboxC.width * img_w), int(bboxC.height * img_h)
            face_boxes.append((x, y, w, h))

        def check_overlap(sticker_x, sticker_y, sticker_w, sticker_h, face_boxes):
            """Check if sticker overlaps with any face"""
            for face_x, face_y, face_w, face_h in face_boxes:
                # Check if rectangles overlap
                if (sticker_x < face_x + face_w and
                    sticker_x + sticker_w > face_x and
                    sticker_y < face_y + face_h and
                    sticker_y + sticker_h > face_y):
                    return True
            return False

        def find_random_position(img_w, img_h, sticker_w, sticker_h, face_boxes, max_attempts=50):
            """Find a random position that doesn't overlap with faces"""
            for _ in range(max_attempts):
                x = random.randint(0, max(0, img_w - sticker_w))
                y = random.randint(0, max(0, img_h - sticker_h))
                
                if not check_overlap(x, y, sticker_w, sticker_h, face_boxes):
                    return (x, y)
            
            # If we can't find a non-overlapping position, place it in a corner
            return (0, 0)

        for i, detection in enumerate(results.detections):
            bboxC = detection.location_data.relative_bounding_box
            img_h, img_w, _ = img.shape
            x, y, w, h = int(bboxC.xmin * img_w), int(bboxC.ymin * img_h), int(bboxC.width * img_w), int(bboxC.height * img_h)

            mask_img = mask1 if i % 2 == 0 else mask2
            
            # Random scale factor between 75% and 125%
            scale_factor = random.uniform(0.75, 1.25)
            mask_width = int(w * 2 * scale_factor)
            mask_height = int(h * 3 * scale_factor)
            resized_mask = mask_img.resize((mask_width, mask_height), Image.LANCZOS)

            if random.choice([True, False]):
                resized_mask = resized_mask.transpose(Image.FLIP_LEFT_RIGHT)

            # Position mask on the face (centered)
            mask_x = x - mask_width // 4
            mask_y = y - mask_height // 4
            top_left = (mask_x, mask_y)
            img_pil.paste(resized_mask, top_left, resized_mask)

        if is_text_meme:
            banner_img = get_random_banner()
            img_width, img_height = img_pil.size
            
            # Random scale factor for banner between 75% and 125%
            banner_scale_factor = random.uniform(0.75, 1.25)
            base_banner_width = int(img_width * 0.4)
            base_banner_height = int(img_height * 0.4)
            new_banner_width = int(base_banner_width * banner_scale_factor)
            new_banner_height = int(base_banner_height * banner_scale_factor)
            resized_banner = banner_img.resize((new_banner_width, new_banner_height), Image.LANCZOS)

            # Find random position for banner that doesn't overlap with faces
            banner_position = find_random_position(img_width, img_height, new_banner_width, new_banner_height, face_boxes)
            img_pil.paste(resized_banner, banner_position, resized_banner)

    output_path = f"img/output/{user_id}_output.jpg"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img_pil.save(output_path)

    photo_file = FSInputFile(output_path)
    await message.reply_photo(photo=photo_file)


async def clear_directory(directory: str):
    if os.path.exists(directory):
        shutil.rmtree(directory)
    os.makedirs(directory, exist_ok=True)

async def extract_zip(file_path, extract_to):
    await clear_directory(extract_to)
    
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        # Список поддерживаемых расширений изображений
        image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')
        
        for file in zip_ref.namelist():
            # Пропускаем папки
            if file.endswith('/'):
                continue
                
            # Проверяем, что файл - изображение
            if file.lower().endswith(image_extensions):
                # Извлекаем файл напрямую в целевую директорию
                filename = os.path.basename(file)
                with zip_ref.open(file) as source, open(os.path.join(extract_to, filename), 'wb') as target:
                    shutil.copyfileobj(source, target)

@user_handlers.message(Command("upload_masks"))
async def upload_masks(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        await message.answer("⛔ You don't have permission to use this command.")
        return
    await state.set_state(UploadStates.UPLOAD_MASKS)
    await message.answer("📤 Please send a ZIP archive with masks.")


@user_handlers.message(Command("upload_banners"))
async def upload_banners(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        await message.answer("⛔ You don't have permission to use this command.")
        return
    await state.set_state(UploadStates.UPLOAD_BANNERS)
    await message.answer("📤 Please send a ZIP archive with banners.")

@user_handlers.message(F.document)
async def handle_zip_upload(message: Message, state: FSMContext):
    user_id = message.from_user.id
    current_state = await state.get_state()

    if message.from_user.id not in ADMINS:
        await message.answer("⛔ You don't have permission to use this command.")
        return

    document: Document = message.document
    file_name = document.file_name.lower()

    if not file_name.endswith(".zip"):
        await message.answer("❌ Please upload a ZIP archive.")
        return

    if current_state == UploadStates.UPLOAD_MASKS.state:
        extract_to = "img/masks"
    elif current_state == UploadStates.UPLOAD_BANNERS.state:
        extract_to = "img/banners"
    else:
        await message.answer("⚠ Unknown upload context. Use /upload_masks or /upload_banners.")
        return

    file_info = await bot.get_file(document.file_id)
    file_path = f"temp/{file_name}"

    os.makedirs("temp", exist_ok=True)
    await bot.download_file(file_info.file_path, file_path)

    try:
        await extract_zip(file_path, extract_to)
        await message.answer(f"✅ Archive successfully extracted to `{extract_to}`. Old files have been removed.")
    except Exception as e:
        await message.answer(f"❌ Error extracting the archive: {e}")

    os.remove(file_path)
    await state.clear()

