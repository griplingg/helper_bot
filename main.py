import datetime
import telegram
from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler
from telegram.ext import CallbackContext, CommandHandler
from telegram.ext import CommandHandler, ConversationHandler, CallbackQueryHandler
from data.citati import Citat
from data.notes import Note
from data.habits import Habit
from data.tracking import Tracking
import random
import requests
import logging
from telegram_bot_pagination import InlineKeyboardPaginator
from data import db_session, db_session_settings
from data.settings import Settings
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import func

db_session.global_init("db/citati.db")
db_session_settings.global_init("db/settings.db")
db_session.global_init("db/notes.db")

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
    dp.add_handler(CallbackQueryHandler(button, pattern="^button#"))
    dp.add_handler(CommandHandler("settings", settings))
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("check_habit_week", check_habit_week))
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
    dp.add_handler(CallbackQueryHandler(tracking, pattern="^answer#"))
    dp.add_handler(CommandHandler('read_all_notes', read_all_notes))
    dp.add_handler(CommandHandler('menu', menu))
    dp.add_handler(CallbackQueryHandler(note_page_callback, pattern='^note#'))
    dp.add_handler(CommandHandler("weather", weather))
    dp.add_handler(CommandHandler("read_note", read_note))
    updater.start_polling()
    updater.idle()


def start(update, context):
    keyboard = [[
            InlineKeyboardButton("о боте", callback_data='button#about'),
            InlineKeyboardButton("помощь", callback_data='button#help')],
            [InlineKeyboardButton("список функций", callback_data='button#function_list')]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Я бот-помощник, выберите интересующую вас функцию', reply_markup=reply_markup)


def button(update, CallbackContext):
    keyboard = [[
        InlineKeyboardButton("в меню", callback_data='button#menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    callback = update.callback_query
    callback.answer()
    a = callback.data.split('#')[1]
    if a == 'author_change':
        bot_settings()
        callback.message.reply_text('успешно!',
                                    reply_markup=reply_markup)
    if a == 'about':
        callback.message.reply_text('этот бот умеет выполнять многие полезные задачи, '
                                    'подробнее о его функциях можно прочитать в разделе "помощь"',
                                    reply_markup=reply_markup)
    if a == 'help':
        keyboard3 = [[
            InlineKeyboardButton("погода", callback_data='button#help_weather'),
            InlineKeyboardButton("заметки", callback_data='button#help_notes')],
            [
             InlineKeyboardButton("мотивация", callback_data='button#help_motivation')],
             [InlineKeyboardButton("прочитать все заметки", callback_data='button#help_read_all_notes')],
             [InlineKeyboardButton("заметки", callback_data='button#help_notes')],
            [
             InlineKeyboardButton("трекер привычек", callback_data='button#help_tracker')],
             [InlineKeyboardButton("добавить цитату", callback_data='button#help_quote')]]
        reply_markup3 = InlineKeyboardMarkup(keyboard3)
        callback = update.callback_query
        callback.answer()
        callback.message.reply_text('Выберите функцию c которой нужна помощь:', reply_markup=reply_markup3)
    if a == 'help_read_all_notes':
        callback.message.reply_text("Функция позволит прочесть все заметки\n"
                                    "для вызова функции напишите: '/read_all_notes',\n"
                                    "если функция не отвечает, убедитесь, что вы вводили заметки",
                                    reply_markup=reply_markup)
    if a == 'help_notes':
        callback.message.reply_text("Функция позволит создать новую заметку\n"
                                    "для вызова функции напишите: '/new_note',\n"
                                    "следуйте дальнейшим инструкциям"
                                    "для сохранения заметки вызовите /save_note",
                                    reply_markup=reply_markup)
    if a == 'help_tracker':
        callback.message.reply_text("Функция позволит создать трекер привычек\n"
                                    "для вызова функции напишите: '/add_tracker',\n"
                                    "следуйте дальнейшим инструкциям"
                                    "если функция не работает, убедитесь, что ввели верный часовой формат",
                                    reply_markup=reply_markup)
    if a == 'help_weather':
        callback.message.reply_text("для вызова функции напишите: '/weather ваш город',\n"
                                    "например:  '/weather Владимир' \n"
                                    "если функция не отвечает убедитесь, что вы ввели название города \n"
                                    "если функция не отвечает убедитесь в правильности вызова",
                                    reply_markup=reply_markup)
    if a == 'help_motivation':
        callback.message.reply_text("для вызова функции напишите: '/motivation'  и следуйте дальнейшим инструкциям,\n"
                                    "если функция не отвечает убедитесь в правильности вызова\n"
                                    "возможные причины ошибок:\n"
                                    "-неправильный ввод команды\n"
                                    "- слова, написанные не по образцу\n"
                                    "-кавычки при вводе\n",
                                    reply_markup=reply_markup)
    if a == 'help_quote':
        callback.message.reply_text("для вызова функции напишите: '/quote',\n"
                                    "если не работает вызов функции, убедитесь, что она вызывается правильно\n"
                                    "если функция не добавляет цитату убедитесь в верности формата записи",
                                    reply_markup=reply_markup)
    if a == 'function_list':
        keyboard2 = [[
            InlineKeyboardButton("погода", callback_data='button#list_weather'),
            InlineKeyboardButton("заметки", callback_data='button#list_notes')],
            [
            InlineKeyboardButton("трекер привычек", callback_data='button#list_tracker')],
            [InlineKeyboardButton("прочитать все заметки", callback_data='button#list_read_all_notes')],
            [InlineKeyboardButton("мотивация", callback_data='button#list_motivation')],
            [
            InlineKeyboardButton("добавить цитату", callback_data='button#list_quote')],
            [InlineKeyboardButton("меню", callback_data='button#list_menu')],
            [InlineKeyboardButton("настройки", callback_data='button#list_settings')]]
        reply_markup2 = InlineKeyboardMarkup(keyboard2)
        callback = update.callback_query
        callback.answer()
        callback.message.reply_text('Выберите функцию о которой хотите узнать:',
                                    reply_markup=reply_markup2)
    if a == 'list_weather':
        callback.message.reply_text("Функция позволит узнать о погоде и подскажет как сегодня одеться\n"
                                    "для вызова функции напишите: '/weather ваш город',\n"
                                    "например:  '/weather Владимир'",
                                    reply_markup=reply_markup)
    if a == 'list_read_all_notes':
        callback.message.reply_text("Функция позволит прочесть все заметки\n"
                                    "для вызова функции напишите: '/read_all_notes',\n",
                                    reply_markup=reply_markup)
    if a == 'list_notes':
        callback.message.reply_text("Функция позволит создать новую заметку\n"
                                    "для вызова функции напишите: '/new_note',\n"
                                    "следуйте дальнейшим инструкциям"
                                    "для сохранения заметки вызовите /save_note",
                                    reply_markup=reply_markup)
    if a == 'list_tracker':
        callback.message.reply_text("Функция позволит создать трекер привычек\n"
                                    "для вызова функции напишите: '/add_tracker',\n"
                                    "следуйте дальнейшим инструкциям",
                                    reply_markup=reply_markup)
    if a == 'list_motivation':
        callback.message.reply_text("Функция выдает случайную цитату из списка\n"
                                    "для вызова функции напишите: '/motivation'  и следуйте дальнейшим инструкциям,\n"
                                    "вы можете получить текстовую цитату или цитату с"
                                    " картинкой",
                                    reply_markup=reply_markup)
    if a == 'list_quote':
        callback.message.reply_text("Функция позволяет добавить свою текстовую цитату\n"
                                    "для вызова функции напишите: '/quote',\n",
                                    reply_markup=reply_markup)
    if a == 'list_settings':
        callback.message.reply_text("Функция изменяет настройки показа автора при выводе цитат\n"
                                    "для вызова функции напишите: '/settings'  и следуйте дальнейшим инструкциям",
                                    reply_markup=reply_markup)
    if a == 'list_menu':
        callback.message.reply_text("Функция возвращения в основное меню\n"
                                    "для вызова функции напишите: '/menu',\n",
                                    reply_markup=reply_markup)
    if a == 'menu':
        keyboard1 = [[
            InlineKeyboardButton("о боте", callback_data='button#about'),
            InlineKeyboardButton("помощь", callback_data='button#help')],
            [InlineKeyboardButton("список функций", callback_data='button#function_list')]]
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
        InlineKeyboardButton("о боте", callback_data='button#about'),
        InlineKeyboardButton("помощь", callback_data='button#help'),
        InlineKeyboardButton("список функций", callback_data='button#function_list')]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Я бот-помощник, выберите интересующую вас функцию', reply_markup=reply_markup)


def citati(update, context):
    keyboard = [[
        InlineKeyboardButton("в меню", callback_data='button#menu')]]
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
        InlineKeyboardButton("в меню", callback_data='button#menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "Если хотите получить текстовую цитату, то введите 'текст',\n"
        "если хотите получить картинку, то введите 'картинка'", reply_markup=reply_markup)
    return 1


def quote(update, context):
    keyboard = [[
        InlineKeyboardButton("в меню", callback_data='button#menu')]]
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
    city = " ".join(context.args)
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
            wind_speed = json_response_w["wind"]["speed"]
            wind_dgr = json_response_w["wind"]["deg"]
            weather_id = json_response_w["weather"][0]['id']
            icon = json_response_w["weather"][0]['icon']
            wind_direction = ''
            if 337 <= wind_dgr <= 22:
                wind_direction = "Северный"
            elif 23 <= wind_dgr <= 67:
                wind_direction = "Северо-восточный"
            elif 68 <= wind_dgr <= 112:
                wind_direction = "Восточный"
            elif 113 <= wind_dgr <= 157:
                wind_direction = "Юго-восточный"
            elif 158 <= wind_dgr <= 202:
                wind_direction = "Южный"
            elif 203 <= wind_dgr <= 247:
                wind_direction = "Юго-западный"
            elif 248 <= wind_dgr <= 292:
                wind_direction = "Западный"
            elif 293 <= wind_dgr <= 336:
                wind_direction = "Северо-западный"
            context.bot.send_photo(
                update.message.chat_id,
                f"http://openweathermap.org/img/wn/{icon}@2x.png",
                caption=f"За окном {weather}\n"
                        f"Температура воздуха {round(temp, 1)}°C, ощущается как {round(temp_f, 1)}°C\n"
                        f"{wind_direction} ветер {round(wind_speed, 1)} м/с")
            if weather_id // 100 == 2:
                update.message.reply_text("Лучше остаться дома в такую погоду")
            elif weather_id // 100 == 3 or weather_id // 100 == 5:
                update.message.reply_text("Не забудьте зонтик - он точно вам пригодиться")
            elif weather_id // 100 == 6:
                update.message.reply_text("Не забудьте взять шапку, если захотите выйти из дома")
            elif weather_id == 800:
                update.message.reply_text("Вам могут понадобиться солнечные очки")
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
        InlineKeyboardButton("в меню", callback_data='button#menu'),
        InlineKeyboardButton("изменить", callback_data='button#author_change')]]
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


def read_note(update, context):
    date = [int(x) for x in context.args[0].split('.')]
    dt = datetime.datetime(date[2], date[1], date[0], 0, 0, 0)
    dtm = datetime.datetime(date[2], date[1], date[0], 23, 59, 59, 0)
    db_sess = db_session.create_session()
    base = list(db_sess.query(Note.text, Note.date).filter(Note.username == update.message.from_user["username"], Note.date >= dt, Note.date <= dtm))
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
        InlineKeyboardButton("Да", callback_data=f'answer#{n}/1'),
        InlineKeyboardButton("Нет", callback_data=f'answer#{n}/0')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(job.context, text=data, reply_markup=reply_markup)


def tracking(update, context):
    callback = update.callback_query
    callback.answer()
    db_sess = db_session.create_session()
    now = datetime.date.today()
    a = callback.data.split('#')[1]
    answ = int(a.split('/')[1])
    if answ == 1:
        new = Tracking(date=now, done=True, habit_id=int(a[0]))
        db_sess.add(new)
        db_sess.commit()
    else:
        new = Tracking(date=now, done=False, habit_id=int(a[0]))
        db_sess.add(new)
        db_sess.commit()


def unset(update, context):
    """Удаляет задачу, если пользователь передумал"""
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = 'Таймер отменен!' if job_removed else 'У вас нет активных таймеров'
    update.message.reply_text(text)


def check_habit_week(update, context):
    dates = []
    td = datetime.datetime.today()
    td = td.replace(hour=0, minute=0, second=0, microsecond=0)
    timed = datetime.timedelta(hours=23, minutes=59, seconds=59)
    for i in range(7):
        day = td - datetime.timedelta(i)
        dates.append(day)
    dates = dates[::-1]
    r = ''
    db_sess = db_session.create_session()
    base = list(db_sess.query(Habit.habit, Habit.id).filter(Habit.username == update.message.from_user["username"]))
    for x in base:
        r += x[0]
        r += '\n'
        dates_str = [x.strftime('%d.%m') for x in dates]
        r = r + '\t'.join(dates_str) + '\n  '
        for y in dates:
            done = list(db_sess.query(Tracking.done).filter(Tracking.habit_id == x[1],
                                                            Tracking.date >= y, Tracking.date <= y + timed))
            print(done)
            if done == []:
                r += "&#11036;"
            elif done[0][0]:
                r += "&#10004;"
            elif not done[0][0]:
                r += "&#10006;"
            r += "      "
        r += '\n'
    update.message.reply_text(r, parse_mode="HTML")


def stop():
    pass


if __name__ == '__main__':
    main()
