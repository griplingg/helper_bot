import datetime

import telegram
from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler
from telegram.ext import CallbackContext, CommandHandler
from telegram.ext import CommandHandler, ConversationHandler
from data import db_session
from data.citati import Citat
from data.notes import Note
from data.habits import Habit
from data.tracking import Tracking
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
import random
import requests
import logging
from telegram import InlineKeyboardButton
from telegram_bot_pagination import InlineKeyboardPaginator
from pytz import timezone
import pytz

db_session.global_init("db/notes.db")
# db_session.global_init("db/citati.db")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)


def main():
    updater = Updater('5103219044:AAGIibAfCpvXjLp8el1qy9T67bctCZj84iQ', use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("settings", settings))
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('motivation', motivation)],
        states={
            1: [MessageHandler(Filters.text & ~Filters.command, citati, pass_user_data=True)],
        },
        fallbacks=[CommandHandler('menu', menu)]
    )
    conv_handler2 = ConversationHandler(
        entry_points=[CommandHandler('quote', quote)],
        states={
            2: [MessageHandler(Filters.text & ~Filters.command, add_quote, pass_user_data=True)],
        },
        fallbacks=[CommandHandler('menu', menu)]
    )
    conv_handler3 = ConversationHandler(
        entry_points=[CommandHandler('new_note', new_note)],
        states={
            "get_text": [MessageHandler(Filters.text & ~Filters.command, get_text, pass_user_data=True)],
        },
        fallbacks=[CommandHandler('save_note', save_note)]
    )
    conv_handler4 = ConversationHandler(
        # Точка входа в диалог.
        # В данном случае — команда /start. Она задаёт первый вопрос.
        entry_points=[CommandHandler('add_tracker', add_tracker)],

        # Состояние внутри диалога.
        # Вариант с двумя обработчиками, фильтрующими текстовые сообщения.
        states={
            # Функция читает ответ на первый вопрос и задаёт второй.
            1: [MessageHandler(Filters.text & ~Filters.command, first_response)],
            # Функция читает ответ на второй вопрос и завершает диалог.
            2: [MessageHandler(Filters.text & ~Filters.command, second_response)],
            3: [MessageHandler(Filters.text & ~Filters.command, third_response)]},
        fallbacks=[CommandHandler('stop', stop)])
    dp.add_handler(conv_handler)
    dp.add_handler(conv_handler2)
    dp.add_handler(conv_handler3)
    dp.add_handler(conv_handler4)
    dp.add_handler(CallbackQueryHandler(tracking))
    dp.add_handler(CommandHandler('read_all_notes', read_all_notes))
    dp.add_handler(CallbackQueryHandler(note_page_callback, pattern='^note#'))
    dp.add_handler(CommandHandler("weather", weather))
    dp.add_handler(CommandHandler("read_note", read_note))
    updater.start_polling()
    updater.idle()


def start(update, context):
    reply_keyboard = [['/motivation', '/settings'],
                      ['/help', '/quote']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
    update.message.reply_text(
        "Я бот-помощник, выберите интересующую вас функцию",
        reply_markup=markup
    )


def help(update, context):
    update.message.reply_text(
        "Привет! я бот-помощник, во мне собрано множество функций,\n"
        "которые помогут тебе в распределении времени и дел")


def menu(update, context):
    reply_keyboard = [['/motivation', '/settings'],
                      ['/help', '/quote']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
    update.message.reply_text(
        "Я бот-помощник, выберите интересующую вас функцию",
        reply_markup=markup
    )


def citati(update, context):
    context.user_data['locality'] = update.message.text
    print(context.user_data['locality'])
    if context.user_data['locality'] == 'текст':
        db_sess = db_session.create_session()
        base = list(db_sess.query(Citat.name).all())
        print(base)
        update.message.reply_text(random.choice(base)[0])
    elif context.user_data['locality'] == 'картинка':
        jp = open('images/c1.jpg', 'rb')
        context.bot.send_photo(
            update.message.chat_id,
            jp)
    else:
        update.message.reply_text('что-то пошло не так, попробуйте еще раз;)')
    context.user_data.clear()
    return ConversationHandler.END


def motivation(update, context):
    update.message.reply_text(
        "Если хотите получить текстовую цитату, то введите 'текст',\n"
        "если хотите получить картинку, то введите 'картинка'")
    return 1


def quote(update, context):
    update.message.reply_text('Пришлите текст цитаты, чтобы добавить ее в базу')
    return 2


def add_quote(update, context):
    context.user_data['locality'] = update.message.text
    db_sess = db_session.create_session()
    newquote = Citat(name=context.user_data['locality'])
    db_sess.add(newquote)
    db_sess.commit()
    update.message.reply_text('Успешно!')
    return ConversationHandler.END


def weather(update, context):
    city = context.args[0]
    api_server = "http://geocode-maps.yandex.ru/1.x/"
    apikey = "40d1649f-0493-4b70-98ba-98533de7710b"
    api_server_weather = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "apikey": apikey,
        "geocode": city,
        "format": "json"
    }
    response = requests.get(api_server, params=params)
    if response:
        json_response = response.json()
        toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
        toponym_coodrinates = toponym["Point"]["pos"]
        long, lat = [float(a) for a in toponym_coodrinates.split(" ")]
        params_weather = {
            "lat": lat,
            "lon": long,
            "appid": "127ecd8394c0d718a9778cfbd957ff2d",
            "lang": "ru",
            "units": "metric"
        }
        response_w = requests.get(api_server_weather, params=params_weather)
        if response_w:
            json_response_w = response_w.json()
            weather = json_response_w["weather"][0]['description']
            temp = json_response_w["main"]["temp"]
            temp_f = json_response_w["main"]["feels_like"]
            wind = json_response_w["wind"]["speed"]
            update.message.reply_text(f"За окном {weather}\n"
                                      f"Температура воздуха {temp}, ощущается как {temp_f}\n"
                                      f"Скорость ветра {wind}")
        else:
            update.message.reply_text("Ошибка выполнения запроса")
            print("Ошибка выполнения запроса")
            print(response)
            print("Http статус:", response.status_code, "(", response.reason, ")")
    else:
        update.message.reply_text("Ошибка выполнения запроса")
        print("Ошибка выполнения запроса")
        print(response)
        print("Http статус:", response.status_code, "(", response.reason, ")")


def new_note(update, context):
    update.message.reply_text("Введите новую запись")
    context.user_data["new_note"] = ''
    return "get_text"


def save_note(update, context):
    db_sess = db_session.create_session()
    new = Note(text=context.user_data["new_note"], username=update.message.from_user["username"])
    db_sess.add(new)
    db_sess.commit()
    update.message.reply_text('Запись сохранена')
    context.user_data.clear()
    return ConversationHandler.END


def get_text(update, context):
    context.user_data["new_note"] += update.message.text
    context.user_data["new_note"] += "\n\n"
    return "get_text"


def read_all_notes(update, context):
    db_sess = db_session.create_session()
    base_data = list(db_sess.query(Note.text, Note.date).filter(Note.username == update.message.from_user["username"]))
    base = list(map(reformat, base_data))
    print(base)
    context.user_data['base'] = base
    c = len(base)
    paginator = InlineKeyboardPaginator(
        len(base),
        data_pattern='note#{page}'
    )

    update.message.reply_text(
        text=base[0],
        reply_markup=paginator.markup,
        parse_mode='Markdown'
    )


def note_page_callback(update, context):
    query = update.callback_query

    query.answer()

    base = context.user_data['base']

    page = int(query.data.split('#')[1])

    paginator = InlineKeyboardPaginator(
        len(base),
        current_page=page,
        data_pattern='note#{page}'
    )

    query.edit_message_text(
        text=base[page - 1],
        reply_markup=paginator.markup,
        parse_mode='Markdown'
    )


def open(update, context):
    query = update.callback_query
    base = context.user_data['base']
    query.answer()
    st = f"Запись от {base[0][1].strftime('%d/%m/%Y, %H:%M')}\n{base[0][0]}"
    keyboard = [
        [
            InlineKeyboardButton("назад", callback_data="back"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text=st, reply_markup=reply_markup
    )
    return 0


def read_note(update, context):
    date = [int(x) for x in context.args[0].split('.')]
    dt = datetime.datetime(date[2], date[1], date[0], 0, 0, 0)
    dtm = datetime.datetime(date[2], date[1], date[0], 23, 59, 59, 0)
    db_sess = db_session.create_session()
    base = list(db_sess.query(Note.text, Note.date).filter(Note.username == update.message.from_user["username"], Note.date >= dt, Note.date >= dt))
    for i in range(len(base)):
        context.bot.send_message(
            text=reformat(base[i]),
            parse_mode=telegram.ParseMode.MARKDOWN, chat_id=update.message.chat_id
        )


def reformat(x):
    return f"""_Запись от {x[1].strftime('%d.%m.%Y, %H:%M')}_
            \n-----------------------------\n{x[0]}"""


def add_tracker(update, context):
    update.message.reply_text("Какую привычку вы хотите отслеживать?")
    return 1


def first_response(update, context):
    habit = update.message.text
    context.user_data["habit"] = habit
    update.message.reply_text("Какой вопрос вым задавать при отслеживании привычки?\n"
                              "(ответом на него могут быть лишь варианты да/нет)")
    return 2


def second_response(update, context):
    question = update.message.text
    context.user_data["question"] = question
    update.message.reply_text("В какое время присылать уведомление?\n"
                              "ответ напишите в 24-х часовом формате часы:минуты")
    return 3


def third_response(update, context):
    add_timer(update, context, [context.user_data['habit'], context.user_data['question'], update.message.text])
    context.user_data.clear()
    update.message.reply_text("Трекер создан")
    return ConversationHandler.END


def remove_job_if_exists(name, context):
    """Удаляем задачу по имени.
    Возвращаем True если задача была успешно удалена."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


def add_timer(update, context, data):
    db_sess = db_session.create_session()
    time = [int(x) for x in data[2].split(':')]
    dt = datetime.time(time[0] - 3, time[1])
    new = Habit(habit=data[0], question=data[1], time=dt, username=update.message.from_user["username"])
    db_sess.add(new)
    db_sess.commit()
    chat_id = update.message.chat_id
    try:
        db_sess = db_session.create_session()
        data = list(db_sess.query(Habit.id).filter(Habit.username == update.message.from_user["username"]))[-1][0]
        context.job_queue.run_daily(task, dt, context=chat_id, name=str(data))
    except (IndexError, ValueError):
        update.message.reply_text('Использование: /set <секунд>')


def task(context):
    job = context.job
    n = job.name
    db_sess = db_session.create_session()
    data = list(db_sess.query(Habit.question).filter(Habit.id == int(n)))[0][0]
    keyboard = [[
        InlineKeyboardButton("Да", callback_data=f'yes{n}'),
        InlineKeyboardButton("Нет", callback_data=f'no{n}')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(job.context, text=data, reply_markup=reply_markup)


def tracking(update, context):
    callback = update.callback_query
    callback.answer()
    db_sess = db_session.create_session()
    now = datetime.date.today()
    if callback.data[:3] == 'yes':
        new = Tracking(date=now, done=True, habit_id=int(callback.data[3:]))
        db_sess.add(new)
        db_sess.commit()
    else:
        new = Tracking(date=now, done=False, habit_id=int(callback.data[2:]))
        db_sess.add(new)
        db_sess.commit()


def unset(update, context):
    """Удаляет задачу, если пользователь передумал"""
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = 'Таймер отменен!' if job_removed else 'У вас нет активных таймеров'
    update.message.reply_text(text)


def stop():
    pass


def settings(update, context):
    update.message.reply_text("функция  разработке")


if __name__ == '__main__':
    main()
