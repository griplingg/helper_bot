import datetime

import telegram
from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler
from telegram.ext import CallbackContext, CommandHandler
from telegram.ext import CommandHandler, ConversationHandler
from data import db_session
from data.citati import Citat
from data.notes import Note
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
import random
import requests
import logging

db_session.global_init("db/notes.db")
# db_session.global_init("db/citati.db")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)


# Stages
FIRST, SECOND = range(2)
# Callback data
ONE, TWO, THREE, FOUR = range(4)


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
        entry_points=[CommandHandler('read_all_notes', read_all_notes)],
        states={
            FIRST: [
                CallbackQueryHandler(open, pattern='^' + "open" + '$'),
                CallbackQueryHandler(open, pattern='^' + "back" + '$')
            ],
        },
        fallbacks=[CommandHandler('read_all_notes', read_all_notes)],
    )
    dp.add_handler(conv_handler)
    dp.add_handler(conv_handler2)
    dp.add_handler(conv_handler3)
    dp.add_handler(conv_handler4)
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
    base = list(db_sess.query(Note.text, Note.date).filter(Note.username == update.message.from_user["username"]))
    print(base)
    context.user_data['base'] = base
    c = len(base)
    if c == 0:
        update.message.reply_text("у вас нет записей")
    elif c == 1:
        update.message.reply_text(f"Запись от {base[0][1].strftime('%d/%m/%Y, %H:%M')}\n"
                                  f"{base[0][0]}")
    elif c <= 4:
        keyboard = [[]]
        for i in range(1, c + 1):
            keyboard[0].append(InlineKeyboardButton(str(i), callback_data="open"))
    elif c >= 4:
        pass
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Send message with text and appended InlineKeyboard
    update.message.reply_text("Выберите запись", reply_markup=reply_markup)
    # Tell ConversationHandler that we're in state `FIRST` now
    return FIRST


def open(update, context):
    """Show new choice of buttons"""
    print("---------------------------------")
    query = update.callback_query
    print()
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
    return FIRST


def read_note(update, context):
    date = [int(x) for x in context.args[0].split('.')]
    dt = datetime.datetime(date[2], date[1], date[0], 0, 0, 0)
    dtm = datetime.datetime(date[2], date[1], date[0], 23, 59, 59, 0)
    db_sess = db_session.create_session()
    base = list(db_sess.query(Note.text, Note.date).filter(Note.username == update.message.from_user["username"], Note.date >= dt, Note.date >= dt))
    for i in range(len(base)):
        context.bot.send_message(
            text=f"""_Запись от {base[i][1].strftime('%d.%m.%Y, %H:%M')}_
            \n-----------------------------\n{base[i][0]}""",
            parse_mode=telegram.ParseMode.MARKDOWN, chat_id=update.message.chat_id
        )


def settings(update, context):
    update.message.reply_text("функция  разработке")


if __name__ == '__main__':
    main()
