import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from openai import AsyncOpenAI

# 1. Muhit o'zgaruvchilarini yuklash
load_dotenv()

# 2. Kalitlarni olish
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not BOT_TOKEN or not OPENAI_API_KEY:
    sys.exit("Xatolik: BOT_TOKEN yoki OPENAI_API_KEY topilmadi!")

# 3. OpenAI klientini sozlash
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# 4. Bot va Dispatcher ni sozlash
dp = Dispatcher()

# --- SYSTEM PROMPT (Botning "miyasi") ---
# Bu yerda botga qanday ishlash kerakligini o'rgatamiz
SYSTEM_INSTRUCTION = """
Sen professional lingvist va tarjimonsan (O'zbek <-> Rus).
Sening vazifang matnlarni RP (Roleplay) va jonli suhbat kontekstiga moslab, tabiiy va adabiy tarjima qilishdir.

QOIDALAR:
1. Tilni aniqla: 
   - Agar matn O'zbek tilida bo'lsa -> Rus tiliga tarjima qil.
   - Agar matn Rus tilida bo'lsa -> O'zbek tiliga tarjima qil.
   - Agar aralash yoki boshqa tilda bo'lsa, asosiy ma'noga qarab Rus yoki O'zbek tiliga o'gir.

2. Uslub (Tone):
   - Robot kabi so'zma-so'z tarjima QILMA.
   - Kontekstni hisobga ol. Jumlalar tabiiy jaranglasin. 
   - RP (Roleplay) uslubini saqla (his-tuyg'ular va urg'ularni to'g'ri yetkaz).

3. Chiqish (Output):
   - Javobda FAQAT tarjimaning o'zi bo'lsin.
   - Hech qanday "Tarjimasi:", "Rus tilida bunday bo'ladi:" degan ortiqcha so'zlar bo'lmasin.
   - Kirish va xulosa so'zlar yozma.

4. MAXSUS HOLAT (1 so'z):
   - Agar foydalanuvchi faqat 1 dona so'z yuborsa (masalan: "yugurmoq" yoki "бежать"), sen bitta tarjima emas, balki shu so'zning 3-5 ta sinonim va variantlarini ro'yxat shaklida chiqarib ber.
   - Format: 
     1. Variant 1
     2. Variant 2 (sinonim)
     3. Variant 3 (kontekstual ma'no)
"""

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    # html.bold o'rniga oddiy matn ishlating yoki f-stringni to'g'irlang
    await message.answer(
        f"Salom, {message.from_user.full_name}!\n\n"
        "Men aqlli tarjimon botman (UZ <-> RU).\n"
        "Menga matn yuboring, men uni RP va jonli suhbatga moslab tarjima qilaman.\n"
        "Agar bitta so'z yuborsangiz, variantlarni taqdim etaman."
    )

@dp.message(F.text)
async def translate_handler(message: Message) -> None:
    # Telegramdan "yozmoqda..." statusini ko'rsatish
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    user_text = message.text

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini", # Arzon va juda aqlli model (yoki gpt-3.5-turbo)
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": user_text}
            ],
            temperature=0.7, # Kreativlik darajasi (0.7 - oltin o'rtalik)
        )
        
        translated_text = response.choices[0].message.content
        await message.reply(translated_text)

    except Exception as e:
        logging.error(f"Xatolik: {e}")
        await message.reply("Tarjima jarayonida xatolik yuz berdi. Iltimos qayta urinib ko'ring.")

async def main() -> None:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    print("Tarjimon bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot to'xtatildi")