import os
import random
import requests

import json
from pathlib import Path

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
CHAT_ID = 1820808404
ADMIN_CHAT_ID = 747742170

love_poslaniya_messages = [
    "🐾 Котик, надеюсь, сегодня у тебя будет хотя бы одна причина улыбнуться. А лучше миллион ❤️",
    "💌 Если вдруг день будет не очень - помни, что тебе не обязательно всегда со всем справляться идеально. Я в тебя верю! ",
    "❤️ Напоминаю, что ты не только мой любимый мальчик, но и очень хороший человек. Не забывай об этом.",
    "🐈‍⬛ Котик, срочное сообщение: тебя тут очень любят. Всё, можешь продолжать свои важные котиковые дела.",
    "Пожалуйста, не забывай сегодня про себя. Поесть, отдохнуть, выдохнуть - ты тоже заслуживаешь заботы.",
    "☀️ Пусть сегодня всё складывается чуточку легче, чем ты ожидаешь. Обнимаю тебя мысленно ❤️",
    "💗 Я не знаю, каким будет твой день, но точно знаю, что хочу, чтобы ты был счастливым.",
    "🐾 Маленькое напоминание от твоего котёнка: ты можешь ошибаться, уставать и иногда ничего не успевать. Я всё равно в тебя верю.",
    "❤️ Надеюсь, сегодня ты хоть на секунду остановишься и поймёшь, какой ты у меня замечательный.",
    "🧸 Если бы я сейчас была рядом, то просто обняла бы тебя, поцеловала и ещё немного не отпускала.",
    "💌 Котик, пусть сегодня у тебя получится что-нибудь, чем ты сам будешь гордиться. А я и так тобой горжусь ❤️",
    "🌷 Необязательно каждый день быть продуктивным, сильным и собранным. Иногда достаточно просто прожить его. Береги себя.",
    "🐾 Передаю тебе виртуальный поцелуй. Можешь считать его официальным разрешением немного улыбнуться ❤️",
    "💗 Знаешь, что мне нравится? Просто знать, что ты есть в моей жизни. Вот такое маленькое напоминание на сегодня.",
    "Если сегодня никто не сказал тебе ничего хорошего, то вот: я тебя очень люблю, ценю и хочу, чтобы у тебя всё было хорошо ❤️",
]

async def message_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет Котику случайное послание."""

    message = get_next_love_message()

    await update.message.reply_text(message)

async def send_to_him(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_CHAT_ID:
        return

    if not context.args:
        await update.message.reply_text("Напиши сообщение после /send ❤️")
        return

    text = " ".join(context.args)

    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=text
    )

    await update.message.reply_text("Отправила ❤️")

async def weather_him(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_CHAT_ID:
        return

    try:
        message = make_weather_message()

        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            parse_mode="HTML"
        )

        await update.message.reply_text("Прогноз ему отправлен 🌤️❤️")

    except Exception as e:
        print("Ошибка отправки погоды:", e)
        await update.message.reply_text("Погода решила сегодня не сотрудничать 😭")    

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
        0: "СОЛНЦЕ ВЫШЛО НА РАБОТУ ☀️",
        1: "солнышко есть, облачка тоже. все при деле 🌤️",
        2: "небо загрузило текстуры облаков ⛅",
        3: "солнце сегодня решило поработать удалённо ☁️",

        45: "туман. карта не прогрузилась 🌫️",
        48: "Котик, там улица вообще существует? 🌫️",

        51: "небо немного расчувствовалось 🌦️",
        53: "облака плачут, но пока держатся 🌧️",
        55: "небо вспомнило всё и сразу 🌧️",

        61: "дождик вышел погулять. накинь капюшон 🌧️",
        63: "с неба капает. вот такие новости 🌧️",
        65: "НЕБО, МЫ ЖЕ ДОГОВАРИВАЛИСЬ 🌧️",

        71: "снежинки загружаются... 🌨️",
        73: "зима зашла проверить, не расслабились ли мы 🌨️",
        75: "небо рассыпало DLC со снегом ❄️",

        80: "дождик решил перейти на серьёзные разговоры 🌧️",
        81: "небо включило режим душа. без предупреждения 🌧️",
        82: "ТАМ ЧТО, ВЕДРО ПЕРЕВЕРНУЛИ?! 🌧️",

        95: "гроза. Котик, это ты слишком сильно в CS нажимаешь? ⛈️",
        96: "гроза и град. погодный босс финального уровня ⛈️",
        99: "НЕБО АГРЕССИВНО НАСТРОЕНО. В УКРЫТИЕ ⛈️",
    }

    return descriptions.get(code, "погода хуй знает какая")


def get_clothing(temp, feels_like, rain_probability, wind):
    """Определяет, что лучше надеть."""

    if feels_like <= -20:
        clothing = "зимняя курточка, теплая!!! кофта. голову, шею, руки в тепло! 🥶"
    elif feels_like <= -10:
        clothing = "зимняя курточка, кофта какая-нибудь, на голову что-то обязательно, и руки береги 🧣"
    elif feels_like <= 0:
        clothing = "тёплая куртка, свитер/худи 🧥"
    elif feels_like <= 8:
        clothing = "ветровка, худи или свитер 🧥"
    elif feels_like <= 15:
        clothing = "худаааааак теплый обязательно 🧥"
    elif feels_like <= 22:
        clothing = "футболка и лёгкая верхняя одежда на всякий случай 👕"
    elif feels_like <= 28:
        clothing = "лёгкая одежда - футболка и что-нибудь удобное ☀️"
    else:
        clothing = "что-нибудь максимально лёгкое и не забудь пить воду 🥵"

    if rain_probability >= 50:
        clothing += "\n☔ И обязательно учти дождь, иначе ты будешь промокшим."

    if wind >= 8:
        clothing += "\n🌬️ На улице ветрено, лучше взять что-нибудь потеплее или ветронепродуваемое."

    return clothing

def get_greeting():
    """Выбирает приветствие в зависимости от времени суток."""

    hour = datetime.now(ZoneInfo("Europe/Moscow")).hour

    if 5 <= hour < 12:
        messages = [
            "☀️ Доброе утро, моё солнышко! Надеюсь, ты хорошо спал ❤️",
            "🐾 Котик, подъём! Твоя персональная служба погоды уже на месте",
            "☕ Доброе утро, мой хороший. Пусть день будет к тебе добрым ❤️",
            "☀️ Просыпайся потихоньку, любимый. Я тут принесла тебе прогноз",
            "❤️ Доброе утро, Котик. Обнимаю тебя на расстоянии",
            "🐾 Проверка связи: мой любимый мальчик уже проснулся?",
            "🌤 Доброе утро! Надеюсь, сегодня у тебя будет побольше поводов улыбнуться",
            "☀️ Котик, я узнала, что там за окном. Сейчас всё расскажу!",
        ]

    elif 12 <= hour < 18:
        messages = [
            "🌤 Как там поживает мой любимый человек?",
            "🐾 Маленький перерыв на заботу. Как твои дела, хороший?",
            "☀️ Любимый, держи прогноз погоды. Одевайся там по-человечески ❤️",
            "💌 Это напоминание, что кто-то тебя очень любит. А ещё вот погода!",
            "🐈 Ну что, Котик, как проходит день? Не забывай отдыхать",
            "❤️ Надеюсь, сегодня у тебя всё получается. А если нет - ты всё равно умничка",
            "🌤 Сводка для самого любимого мальчика. Приём!",
            "🥺 Ты там поел сегодня? И погоду заодно давай проверим",
        ]

    elif 18 <= hour < 23:
        messages = [
            "🌙 Добрый вечер, мой хороший. Как прошёл твой день? ❤️",
            "🐾 Котик, вечерняя доставка погоды и немного моей любви",
            "❤️ Ну что, любимый, день тебя не слишком замучил?",
            "🌙 Я принесла прогноз. Заодно мысленно обнимаю тебя",
            "🐈 Котик, ты сегодня молодец. Даже если сам так не считаешь",
            "💌 Вечерняя проверка: мой любимый мальчик в порядке?",
            "🌙 Надеюсь, вечером ты сможешь немного выдохнуть и отдохнуть",
            "❤️ Погода на улице - это одно, а я надеюсь, что у тебя внутри тепло",
        ]

    else:
        messages = [
            "🌙 Котик, ты чего ещё не спишь? Я вообще-то волнуюсь 🥺❤️",
            "🐾 Ночной прогноз для моего любимого сонного комочка",
            "🥺 Любимый, может, уже спать? Завтра тебе ещё мир покорять",
            "🌙 Я бы сейчас укрыла тебя одеялком и пожелала сладких снов",
            "❤️ Если ты ещё не спишь - обнимаю. А если спишь, то пусть тебе снятся хорошие сны",
            "🐈 Котик, служба погоды работает круглосуточно, но тебе тоже нужен сон!",
            "🌙 Всё, последняя проверка погоды - и марш отдыхать, мой хороший",
            "🥺 Погоду показать или сразу завернуть тебя в одеяло?",
        ]

    return random.choice(messages)

def get_love_message(feels_like, rain_probability):
    """Выбирает заботливое сообщение в зависимости от времени и погоды."""

    hour = datetime.now(ZoneInfo("Europe/Moscow")).hour

    if 5 <= hour < 12:
        if feels_like <= 0:
            messages = [
                "🥺 Котик, на улице холодно! Укутайся там хорошенько, я мысленно проверю ❤️",
                "🧣 Доброе утро, любимый. Одевайся теплее, пожалуйста. Мне нужен тёплый и довольный Котик",
                "🐾 Если сегодня замёрзнешь, я буду недовольна. Так что шарф, куртка и вперёд ❤️",
                "☕ Пусть тебя сегодня согревают не только мои мысли о тебе, но и нормальная тёплая одежда",
            ]
        elif rain_probability >= 60:
            messages = [
                "☔ Котик, надень одежду с капюшоном, пожалуйста. Не хочу, чтобы ты пришёл домой мокрым котёнком ❤️",
                "🌧 На улице дождик. Учти это, а то знаю я вас, мужчин 🐾",
                "🥺 Любимый, проверь перед выходом: телефон, ключи, укрытие от дождя. Всё взял? ❤️",
                "☔ Дождь сегодня решил вмешаться в твои планы. Не дай ему победить!",
            ]
        else:
            messages = [
                "☀️ Хорошего утра, мой хороший. Пусть сегодня всё складывается чуточку легче ❤️",
                "🐈 Котик, отправляю тебе виртуальное обнимашечное одеялко на весь день",
                "💌 Напоминание с самого утра: ты любимый, ты важный, и я очень хочу, чтобы у тебя всё было хорошо",
                "☕ Позавтракай, попей водички и не пытайся сразу спасти весь мир. Он подождёт ❤️",
                "🐾 Пусть день будет приятным, а люди вокруг не проверяют твоё терпение на прочность",
            ]

    elif 12 <= hour < 18:
        if feels_like <= 0:
            messages = [
                "🧣 Котик, если ещё куда-то пойдёшь, утеплись. Я за тебя и против твоих замёрзших ушей ❤️",
                "🥺 Там холодно, хороший. Не геройствуй без шапки, пожалуйста",
                "🐈 Передаю срочное распоряжение: согреваться, не мёрзнуть и иногда вспоминать обо мне ❤️",
            ]
        elif rain_probability >= 60:
            messages = [
                "☔ Котик, укрытие от дождя с собой? Я провожу внезапную проверку твоей готовности к дождю",
                "🌧 Не промокни там, любимый. А то мне придётся мысленно сушить тебя феном ❤️",
                "🐾 Если собрался выходить - глянь на погоду. Она сегодня явно что-то задумала",
            ]
        else:
            messages = [
                "❤️ Какой бы ни была середина дня, надеюсь, у тебя найдётся минутка выдохнуть",
                "🐾 Просто маленький привет от человека, который очень тебя любит",
                "☀️ Котик, не забывай делать перерывы. Даже самым крутым игрокам нужно восстановление",
                "💌 Пусть хотя бы одна вещь сегодня порадует тебя неожиданно и сильно",
                "🐈 Мысленно чмокнула тебя в нос. Всё, можешь возвращаться к своим важным делам ❤️",
            ]

    elif 18 <= hour < 23:
        if feels_like <= 0:
            messages = [
                "🌙 Любимый, если возвращаешься домой, утеплись. Хочу, чтобы ты добрался в тепле ❤️",
                "🧣 Котик, береги свои лапки и носик от холода. Они у тебя вообще-то ценные",
                "🥺 На улице холодно. Пожалуйста, не мёрзни по дороге, мой хороший",
            ]
        elif rain_probability >= 60:
            messages = [
                "☔ Котик, если ещё куда-то пойдёшь, захвати укрытие от дождя. Я не хочу мокрого кота ❤️",
                "🌧 Пусть дорога домой будет спокойной, сухой и короткой. Обнимаю тебя мысленно",
                "🐾 Вечерний чек-лист: ключи, телефон, укрытие от дождя и знание, что тебя любят ❤️",
            ]
        else:
            messages = [
                "🌙 Хорошего вечера, мой хороший. Надеюсь, сегодня у тебя осталось что-то приятное в памяти ❤️",
                "🐈 Котик, можно уже немного расслабиться. Необязательно всё успевать за один день",
                "💌 Если день был тяжёлым - пусть вечер будет мягким. Ты заслужил отдых",
                "❤️ Желаю тебе спокойного вечера, вкусной еды и поменьше поводов нервничать",
                "🐾 Вечерняя доставка любви прибыла. Получатель - самый любимый Котик",
            ]

    else:
        messages = [
            "🌙 Котик, время отправляться в объятия подушки. Это не просьба, это заботливая рекомендация ❤️",
            "🥺 Любимый, давай спать. Мне нужен выспавшийся Котик, а не ночной зомби",
            "🐾 Ночное распоряжение: укрыться, устроиться поудобнее и отдыхать. Целую в нос ❤️",
            "🌙 Пусть все мысли подождут до завтра. Сейчас твоя задача - сладко спать, родной",
            "❤️ Спокойной ночи, мой родной. Жаль, что нельзя прямо сейчас обнять тебя и укрыть одеялом",
            "🐈 Котик, серверу пора на техническое обслуживание. Перезагрузка - во сне!",
            "💌 Если ты это читаешь перед сном, считай, что я обняла тебя крепко-крепко. Сладких снов ❤️",
        ]

    return random.choice(messages)


# Файл, в котором сохраняется очередь посланий
MESSAGES_STATE_FILE = Path(__file__).with_name("messages_state.json")


def get_next_love_message():
    """Выбирает послание без повторов и сохраняет очередь между перезапусками."""

    # Убираем дубликаты одинаковых текстов
    all_messages = list(dict.fromkeys(love_poslaniya_messages))

    if not all_messages:
        raise ValueError("Список love_poslaniya_messages пуст!")

    # Загружаем сохранённое состояние
    try:
        with open(MESSAGES_STATE_FILE, "r", encoding="utf-8") as file:
            state = json.load(file)

        queue = state.get("queue", [])
        previous_messages = state.get("messages", [])

        # Если список фраз изменился, обновляем очередь:
        # оставляем неотправленные фразы и добавляем новые
        if set(previous_messages) != set(all_messages):
            queue = [
                message for message in queue
                if message in all_messages
            ]

            for message in all_messages:
                if message not in previous_messages and message not in queue:
                    queue.append(message)

            random.shuffle(queue)

    except (FileNotFoundError, json.JSONDecodeError, OSError, AttributeError):
        # Если сохранения нет или оно повреждено — создаём очередь заново
        queue = all_messages.copy()
        random.shuffle(queue)

    # Если все фразы закончились, начинаем новый круг
    if not queue:
        queue = all_messages.copy()
        random.shuffle(queue)

    # Забираем одну фразу
    message = queue.pop(0)

    # Сначала сохраняем очередь, затем отправляем сообщение.
    # Это помогает не повторять фразу после неожиданного перезапуска.
    state = {
        "messages": all_messages,
        "queue": queue,
    }

    with open(MESSAGES_STATE_FILE, "w", encoding="utf-8") as file:
        json.dump(state, file, ensure_ascii=False, indent=2)

    return message


async def remind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_CHAT_ID:
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "Формат: /remind 08:30 сообщение"
        )
        return

    time_text = context.args[0]
    text = " ".join(context.args[1:])

    try:
        hour, minute = map(int, time_text.split(":"))

        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("Некорректное время")

        now = datetime.now(ZoneInfo("Europe/Moscow"))
        target = now.replace(
            hour=hour,
            minute=minute,
            second=0,
            microsecond=0
        )

        if target <= now:
            from datetime import timedelta
            target += timedelta(days=1)

        context.job_queue.run_once(
            send_reminder,
            when=target,
            data=text,
            name=f"reminder_{hour:02d}_{minute:02d}"
        )

        await update.message.reply_text(
            f"Хорошо, отправлю ему в {time_text} по Москве ❤️"
        )

    except ValueError:
        await update.message.reply_text(
            "Не поняла время 😭 Напиши, например: /remind 08:30 выходи"
        )

async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    text = context.job.data

    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=text
    )

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
            "я сломалась, потеряла компас погоды"
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    keyboard = [
        ["🌤 Узнать погоду"],
        ["💌 Получить послание"]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "Привет, мой самый любимый мальчик на свете ❤️\n\n"
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
        import traceback
        print("ОШИБКА В WEATHER:")
        traceback.print_exc()

        await update.message.reply_text(
            "АХ ДА ГДЕ Ж ЭТА ПОГОДА, СПРОСИ ПОПОЗЖЕ СНОВА"
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
        CommandHandler("weatherhim", weather_him)
    )

    application.add_handler(
            CommandHandler("send", send_to_him)
        )

    application.add_handler(
            CommandHandler("remind", remind)
        )

    application.add_handler(
        MessageHandler(
            filters.TEXT & filters.Regex("^🌤 Узнать погоду$"),
            weather
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & filters.Regex("^💌 Получить послание$"),
            message_button
        )
    )

    # Каждое утро в 06:50 по московскому времени
    application.job_queue.run_daily(
        morning_message,
        time=time(
            hour=6,
            minute=50,
            tzinfo=ZoneInfo("Europe/Moscow")
        ),
        name="morning_weather",
    )

    print("Бот запущен ❤️")

    application.run_polling()


if __name__ == "__main__":
    main()