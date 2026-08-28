import os
import random
import requests

from datetime import time, datetime
from dotenv import load_dotenv
from zoneinfo import ZoneInfo

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Киров
LATITUDE = 58.6036
LONGITUDE = 49.6680

# ID Котика сюда добавим чуть позже
CHAT_ID = 747742170


def get_weather():
    """Получает текущую и дневную погоду в Кирове."""

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "current": [
            "temperature_2m",
            "apparent_temperature",
            "weather_code",
            "wind_speed_10m",
        ],
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_probability_max",
        ],
        "timezone": "Europe/Moscow",
        "forecast_days": 1,
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    return response.json()


def weather_description(code):
    """Переводит код погоды Open-Meteo в человеческий вид."""

    descriptions = {
        0: "ясно ☀️",
        1: "преимущественно ясно 🌤️",
        2: "переменная облачность ⛅",
        3: "пасмурно ☁️",
        45: "туман 🌫️",
        48: "туман 🌫️",
        51: "небольшая морось 🌧️",
        53: "морось 🌧️",
        55: "сильная морось 🌧️",
        61: "небольшой дождь 🌧️",
        63: "дождь 🌧️",
        65: "сильный дождь 🌧️",
        71: "небольшой снег 🌨️",
        73: "снег 🌨️",
        75: "сильный снег ❄️",
        80: "ливень 🌧️",
        81: "ливень 🌧️",
        82: "сильный ливень 🌧️",
        95: "гроза ⛈️",
        96: "гроза с градом ⛈️",
        99: "гроза с градом ⛈️",
    }

    return descriptions.get(code, "неизвестная погода")


def get_clothing(temp, feels_like, rain_probability, wind):
    """Определяет, что лучше надеть."""

    if feels_like <= -20:
        clothing = "очень тёплая куртка, свитер, шапка, перчатки и зимняя обувь 🥶"
    elif feels_like <= -10:
        clothing = "тёплая куртка, свитер, шапка, перчатки и тёплая обувь 🧣"
    elif feels_like <= 0:
        clothing = "тёплая куртка, свитер/худи и закрытая обувь 🧥"
    elif feels_like <= 8:
        clothing = "куртка, худи или свитер и закрытая обувь 🧥"
    elif feels_like <= 15:
        clothing = "лёгкая куртка/ветровка и что-нибудь с длинным рукавом 🧥"
    elif feels_like <= 22:
        clothing = "футболка и лёгкая верхняя одежда на всякий случай 👕"
    elif feels_like <= 28:
        clothing = "лёгкая одежда — футболка и что-нибудь удобное ☀️"
    else:
        clothing = "что-нибудь максимально лёгкое и не забудь пить воду 🥵"

    if rain_probability >= 50:
        clothing += "\n☔ И обязательно возьми зонт."

    if wind >= 8:
        clothing += "\n🌬️ На улице ветрено, лучше взять что-нибудь непродуваемое."

    return clothing

def get_greeting():
    """Выбирает приветствие в зависимости от времени суток."""

    hour = datetime.now().hour

    if 5 <= hour < 12:
        messages = [
            "☀️ Доброе утро, Котик!",
            "☀️ Доброе утро, любимый!",
            "🐾 Котик, доброе утро ❤️",
            "☕ Доброе утро, мой хороший!",
            "☀️ Доброе утро. Я уже проверила погоду для тебя 🐾",
        ]

    elif 12 <= hour < 18:
        messages = [
            "🌤 Добрый день, Котик!",
            "☀️ Добрый день, любимый!",
            "🐾 Котик, как твой день?",
            "🌤 Ну что, Котик, посмотрим, что там на улице?",
            "❤️ Маленькая проверка: как там мой Котик?",
        ]

    elif 18 <= hour < 23:
        messages = [
            "🌙 Добрый вечер, Котик!",
            "🌙 Добрый вечер, любимый!",
            "🐾 Котик, вечерняя проверка погоды для тебя.",
            "❤️ Надеюсь, твой день прошёл хорошо.",
            "🌙 Я снова здесь. Давай посмотрим, что там на улице?",
        ]

    else:
        messages = [
            "🌙 Доброй ночи, Котик.",
            "🌙 Котик, ты чего ещё не спишь? 🥺",
            "🐾 Уже ночь, любимый. Пора спать ❤️",
            "🌙 Ночной прогноз для самого любимого Котика.",
            "🥺 Ты почему ещё не спишь? Погоду тебе посмотреть или сначала спать отправить?",
        ]

    return random.choice(messages)

def get_love_message(feels_like, rain_probability):
    """Выбирает заботливое сообщение в зависимости от времени и погоды."""

    hour = datetime.now().hour

    if 5 <= hour < 12:
        if feels_like <= 0:
            messages = [
                "🥺 Утреннее напоминание: оденься потеплее, пожалуйста. Я хочу, чтобы ты не замёрз ❤️",
                "☀️ Котик, начни день с чего-нибудь тёплого. И себя тоже не забудь утеплить ❤️",
            ]
        elif rain_probability >= 60:
            messages = [
                "☔ Утреннее напоминание: возьми с собой зонт и не промокни, пожалуйста ❤️",
                "🥺 На улице дождик, так что не забудь зонт. Я тебя знаю ❤️",
            ]
        else:
            messages = [
                "☀️ Хорошего тебе утра, Котик. Береги себя и хорошо оденься ❤️",
                "☕ Пусть утро будет добрым. А ты, пожалуйста, береги себя ❤️",
                "🐾 Маленькое утреннее напоминание: ты мне нужен здоровым и тёплым 🥺❤️",
                "❤️ Хорошего дня, любимый. Не забывай беречь себя.",
            ]

    elif 12 <= hour < 18:
        if feels_like <= 0:
            messages = [
                "🧣 Днём холодно, Котик. Не замёрзни там, пожалуйста ❤️",
                "🥺 Если ещё будешь выходить — оденься потеплее. Я беспокоюсь ❤️",
            ]
        elif rain_probability >= 60:
            messages = [
                "☔ Если сегодня ещё будешь выходить — не забудь зонт ❤️",
                "🥺 Береги себя и не промокни там, пожалуйста.",
            ]
        else:
            messages = [
                "🌤 Хорошего тебе дня, Котик. Береги себя ❤️",
                "🐾 Просто напоминаю среди дня: я о тебе беспокоюсь ❤️",
                "❤️ Пусть остаток дня будет хорошим. Не забывай беречь себя.",
            ]

    elif 18 <= hour < 23:
        if feels_like <= 0:
            messages = [
                "🌙 Вечером будет холодно, Котик. Если пойдёшь куда-нибудь — утеплись ❤️",
                "🧣 Не замёрзни по дороге домой, пожалуйста. Я тебя знаю 🥺❤️",
            ]
        elif rain_probability >= 60:
            messages = [
                "☔ Если ещё будешь выходить — возьми зонт, любимый ❤️",
                "🌧 Вечером обещают дождь. Не промокни там, пожалуйста 🥺",
            ]
        else:
            messages = [
                "🌙 Хорошего тебе вечера, Котик. Береги себя ❤️",
                "🐾 Вечернее напоминание: не засиживайся допоздна и береги себя ❤️",
                "❤️ Надеюсь, твой день прошёл хорошо. Отдыхай и береги себя.",
            ]

    else:
        messages = [
            "🌙 Котик, уже ночь. Иди отдыхать, пожалуйста. Ты мне нужен выспавшимся ❤️",
            "🥺 Уже поздно. Давай теперь спать? Береги себя, любимый ❤️",
            "🌙 Доброй ночи, Котик. Выдыхай, отдыхай и ни о чём не переживай ❤️",
            "🐾 Ночное напоминание: пора спать. Завтра тебя снова ждёт новый день ❤️",
        ]

    return random.choice(messages)

def make_weather_message():
    """Создаёт итоговое сообщение."""

    data = get_weather()

    current = data["current"]
    daily = data["daily"]

    temp = current["temperature_2m"]
    feels_like = current["apparent_temperature"]
    weather_code = current["weather_code"]
    wind = current["wind_speed_10m"]

    max_temp = daily["temperature_2m_max"][0]
    min_temp = daily["temperature_2m_min"][0]
    rain_probability = daily["precipitation_probability_max"][0]

    description = weather_description(weather_code)
    clothing = get_clothing(
        temp,
        feels_like,
        rain_probability,
        wind,
    )

    love_message = get_love_message(
        feels_like,
        rain_probability,
    )

    greeting = get_greeting()
    message = f"""
<b>{greeting}</b>

📍 <b>Киров</b>

🌡 Сейчас: <b>{temp:.0f}°C</b>
🥶 Ощущается как: <b>{feels_like:.0f}°C</b>
🌤 Погода: <b>{description}</b>

📈 Днём: <b>{max_temp:.0f}°C</b>
📉 Ночью: <b>{min_temp:.0f}°C</b>
🌧 Вероятность осадков: <b>{rain_probability}%</b>
💨 Ветер: <b>{wind:.0f} м/с</b>

🧥 <b>Что надеть:</b>
{clothing}

{love_message}
"""

    return message.strip()

async def weather_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает кнопку «Узнать погоду»."""

    query = update.callback_query
    await query.answer()

    try:
        message = make_weather_message()

        await query.message.reply_text(
            message,
            parse_mode="HTML"
        )

    except Exception as e:
        print("Ошибка:", e)

        await query.message.reply_text(
            "Не смогла получить погоду 😭"
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    keyboard = [
        ["🌤 Узнать погоду"]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "Привет, Котик ❤️\n\n"
        "Я буду каждое утро рассказывать тебе погоду "
        "в Кирове и напоминать, как лучше одеться ☀️🧥\n\n"
        "А если захочешь узнать погоду прямо сейчас — "
        "просто нажми кнопку ниже 🐾",
        reply_markup=reply_markup
    )

    print(f"CHAT_ID Котика: {chat_id}")


async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /weather для тестирования."""

    try:
        message = make_weather_message()

        await update.message.reply_text(
            message,
            parse_mode="HTML"
        )

    except Exception as e:
        print("Ошибка:", e)

        await update.message.reply_text(
            "Не смогла получить погоду 😭"
        )


async def morning_message(context: ContextTypes.DEFAULT_TYPE):
    """Автоматическая отправка утром."""

    if CHAT_ID is None:
        print("CHAT_ID пока не указан.")
        return

    try:
        message = make_weather_message()

        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            parse_mode="HTML"
        )

    except Exception as e:
        print("Ошибка отправки:", e)


def main():

    if not BOT_TOKEN:
        raise ValueError(
            "Не найден BOT_TOKEN в файле .env"
        )

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("weather", weather)
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & filters.Regex("^🌤 Узнать погоду$"),
            weather
        )
    )

    # Каждое утро в 06:50 по московскому времени
    application.job_queue.run_daily(
        morning_message,
        time=time(
            hour=4,
            minute=18,
            tzinfo=ZoneInfo("Europe/Moscow")
        ),
        name="morning_weather",
    )

    print("Бот запущен ❤️")

    application.run_polling()


if __name__ == "__main__":
    main()