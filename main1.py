from telegram.ext import Updater, MessageHandler, Filters
from telegram.ext import CallbackContext, CommandHandler
from telegram.ext import CommandHandler, ConversationHandler, CallbackQueryHandler
from data import db_session, db_session_settings
from data.citati import Citat
from data.settings import Settings
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
import random
import requests
import logging
from sqlalchemy import func

db_session.global_init("db/citati.db")
db_session_settings.global_init("db/settings.db")

db_sess = db_session_settings.create_session()
dat = db_sess.query(func.count(Settings.id)).scalar()
db_sess.close()
if dat == 0:
    db_sess = db_session_settings.create_session()
    quote_settings = Settings(quote_author=True)
    db_sess.add(quote_settings)
    db_sess.commit()
    db_sess.close()


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)


def quote_author():
    db_sess = db_session_settings.create_session()
    settings = db_sess.query(Settings).filter(Settings.id == 1).first()
    print(settings.quote_author)
    return settings.quote_author


def bot_settings():
    db_sess = db_session_settings.create_session()
    settings = db_sess.query(Settings).filter(Settings.id == 1).first()
    if settings.quote_author:
        settings.quote_author = False
        db_sess.commit()
    else:
        settings.quote_author = True
        db_sess.commit()
    db_sess.close()




def main():
    updater = Updater('5103219044:AAGIibAfCpvXjLp8el1qy9T67bctCZj84iQ', use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CallbackQueryHandler(button))
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
            3: [MessageHandler(Filters.text & ~Filters.command, add_author, pass_user_data=True)],
        },
        fallbacks=[CommandHandler('menu', menu)]
    )
    dp.add_handler(conv_handler)
    dp.add_handler(conv_handler2)
    dp.add_handler(CommandHandler("weather", weather))
    updater.start_polling()
    updater.idle()
def start(update, context):
    keyboard = [[
            InlineKeyboardButton("о боте", callback_data='about'),
            InlineKeyboardButton("помощь", callback_data='help'),
            InlineKeyboardButton("список функций", callback_data='function_list')]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Я бот-помощник, выберите интересующую вас функцию', reply_markup=reply_markup)


def button(update, CallbackContext):
    keyboard = [[
        InlineKeyboardButton("в меню", callback_data='menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    callback = update.callback_query
    callback.answer()
    if callback.data == 'author_change':
        bot_settings()
        callback.message.reply_text('успешно!',
                                    reply_markup=reply_markup)
    if callback.data == 'about':
        callback.message.reply_text('этот бот умеет выполнять многие полезные задачи, '
                                    'подробнее о его функциях можно прочитать в разделе "помощь"',
                                    reply_markup=reply_markup)
    if callback.data == 'help':
        keyboard3 = [[
            InlineKeyboardButton("погода", callback_data='help_weather'),
            InlineKeyboardButton("заметки", callback_data='help_notes'),
            InlineKeyboardButton("мотивация", callback_data='help_motivation'),
            InlineKeyboardButton("добавить цитату", callback_data='help_quote')]]
        reply_markup3 = InlineKeyboardMarkup(keyboard3)
        callback = update.callback_query
        callback.answer()
        callback.message.reply_text('Выберите функцию c которой нужна помощь:', reply_markup=reply_markup3)
    if callback.data == 'help_weather':
        callback.message.reply_text("для вызова функции напишите: '/weather ваш город',\n"
                                    "например:  '/weather Владимир' \n"
                                    "если функция не отвечает убедитесь, что вы ввели название города \n"
                                    "если функция не отвечает убедитесь в правильности вызова",
                                    reply_markup=reply_markup)
    if callback.data == 'help_notes':
        callback.message.reply_text("описание скоро появится", reply_markup=reply_markup)
    if callback.data == 'help_motivation':
        callback.message.reply_text("для вызова функции напишите: '/motivation'  и следуйте дальнейшим инструкциям,\n"
                                    "если функция не отвечает убедитесь в правильности вызова\n"
                                    "возможные причины ошибок:\n"
                                    "-неправильный ввод команды\n"
                                    "- слова, написанные не по образцу\n"
                                    "-кавычки при вводе\n",
                                    reply_markup=reply_markup)
    if callback.data == 'help_quote':
        callback.message.reply_text("для вызова функции напишите: '/quote',\n"
                                    "если не работает вызов функции, убедитесь, что она вызывается правильно\n"
                                    "если функция не добавляет цитату убедитесь в верности формата записи",
                                    reply_markup=reply_markup)
    if callback.data == 'function_list':
        keyboard2 = [[
            InlineKeyboardButton("погода", callback_data='list_weather'),
            InlineKeyboardButton("заметки", callback_data='list_notes'),
            InlineKeyboardButton("мотивация", callback_data='list_motivation'),
            InlineKeyboardButton("добавить цитату", callback_data='list_quote'),
            InlineKeyboardButton("меню", callback_data='list_menu'),
            InlineKeyboardButton("настройки", callback_data='list_settings')]]
        reply_markup2 = InlineKeyboardMarkup(keyboard2)
        callback = update.callback_query
        callback.answer()
        callback.message.reply_text('Выберите функцию о которой хотите узнать:',
                                    reply_markup=reply_markup2)
    if callback.data == 'list_weather':
        callback.message.reply_text("Функция позволит узнать о погоде и подскажет как сегодня одеться\n"
                                    "для вызова функции напишите: '/weather ваш город',\n"
                                    "например:  '/weather Владимир'",
                                    reply_markup=reply_markup)
    if callback.data == 'list_notes':
        callback.message.reply_text("описание скоро появится",
                                    reply_markup=reply_markup)
    if callback.data == 'list_motivation':
        callback.message.reply_text("Функция выдает случайную цитату из списка\n"
                                    "для вызова функции напишите: '/motivation'  и следуйте дальнейшим инструкциям,\n"
                                    "вы можете получить текстовую цитату или цитату с"
                                    " картинкой",
                                    reply_markup=reply_markup)
    if callback.data == 'list_quote':
        callback.message.reply_text("Функция позволяет добавить свою текстовую цитату\n"
                                    "для вызова функции напишите: '/quote',\n",
                                    reply_markup=reply_markup)
    if callback.data == 'list_settings':
        callback.message.reply_text("Функция изменяет настройки показа автора при выводе цитат\n"
                                    "для вызова функции напишите: '/settings'  и следуйте дальнейшим инструкциям",
                                    reply_markup=reply_markup)
    if callback.data == 'list_menu':
        callback.message.reply_text("Функция возвращения в основное меню\n"
                                    "для вызова функции напишите: '/menu',\n",
                                    reply_markup=reply_markup)
    if callback.data == 'menu':
        keyboard1 = [[
            InlineKeyboardButton("о боте", callback_data='about'),
            InlineKeyboardButton("помощь", callback_data='help'),
            InlineKeyboardButton("список функций", callback_data='function_list')]]
        reply_markup1 = InlineKeyboardMarkup(keyboard1)
        callback = update.callback_query
        callback.answer()
        callback.message.reply_text('Я бот-помощник, выберите интересующую вас функцию', reply_markup=reply_markup1)


def help(update, context):
    update.message.reply_text(
        "Привет! я бот-помощник, во мне собрано множество функций,\n"
        "которые помогут тебе в распределении времени и дел")


def menu(update, context):
    keyboard = [[
        InlineKeyboardButton("о боте", callback_data='about'),
        InlineKeyboardButton("помощь", callback_data='help'),
        InlineKeyboardButton("список функций", callback_data='function_list')]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Я бот-помощник, выберите интересующую вас функцию', reply_markup=reply_markup)


def citati(update, context):
    keyboard = [[
        InlineKeyboardButton("в меню", callback_data='menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.user_data['locality'] = update.message.text
    print(context.user_data['locality'])
    if context.user_data['locality'] == 'текст':
        db_sess = db_session.create_session()
        base = list(db_sess.query(Citat.name, Citat.author).all())
        newbase = random.choice(base)
        if quote_author():
            update.message.reply_text(newbase[0] + '\n ' + newbase[1], reply_markup=reply_markup)
        else:
            update.message.reply_text(newbase[0], reply_markup=reply_markup)
    elif context.user_data['locality'] == 'картинка':
        numb = str(random.randint(1, 4))
        jp = open('images/с' + numb + '.jpg', 'rb')
        context.bot.send_photo(
            update.message.chat_id,
            jp)
        update.message.reply_text('вернуться в меню', reply_markup=reply_markup)
    else:
        update.message.reply_text('что-то пошло не так, попробуйте еще раз;)', reply_markup=reply_markup)
        citati()
    context.user_data.clear()
    return ConversationHandler.END


def motivation(update, context):
    keyboard = [[
        InlineKeyboardButton("в меню", callback_data='menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "Если хотите получить текстовую цитату, то введите 'текст',\n"
        "если хотите получить картинку, то введите 'картинка'", reply_markup=reply_markup)
    return 1


def quote(update, context):
    keyboard = [[
        InlineKeyboardButton("в меню", callback_data='menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Пришлите текст цитаты, чтобы добавить ее в базу',
                              reply_markup=reply_markup)
    return 2


def add_quote(update, context):
    try:
        context.user_data['locality'] = update.message.text
        db_sess = db_session.create_session()
        newquote = Citat(name=context.user_data['locality'])
        db_sess.add(newquote)
        db_sess.commit()
        update.message.reply_text('введите автора')
        return 3
    except Exception:
        update.message.reply_text('Попробуйте снова')
        add_quote()


def add_author(update, context):
    try:
        context.user_data['locality'] = update.message.text
        db_sess = db_session.create_session()
        author = db_sess.query(Citat).order_by(Citat.id)[-1]
        author.author = context.user_data['locality']
        db_sess.commit()
        update.message.reply_text('Успешно!')
        return ConversationHandler.END
    except Exception:
        update.message.reply_text('Попробуйте снова')


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


def settings(update, context):
    keyboard = [[
        InlineKeyboardButton("в меню", callback_data='menu'),
        InlineKeyboardButton("изменить", callback_data='author_change')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    db_sess = db_session_settings.create_session()
    settings = db_sess.query(Settings).filter(Settings.id == 1).first()
    if settings.quote_author:
        settings_quote_author = 'отображать автора'
    else:
        settings_quote_author = 'не отображать автора'
        db_sess.commit()
    db_sess.close()
    update.message.reply_text("изменить отображение автора при выводе цитат:\n"
                              'текущая настройка: ' + settings_quote_author,
                              reply_markup=reply_markup)


if __name__ == '__main__':
    main()
