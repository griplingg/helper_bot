from telegram.ext import Updater, MessageHandler, Filters
from telegram.ext import CallbackContext, CommandHandler
from telegram.ext import CommandHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup
import random
import requests
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)


def main():
    updater = Updater('5103219044:AAGIibAfCpvXjLp8el1qy9T67bctCZj84iQ', use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("settings", settings))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("start", start))
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('motivation', motivation)],
        states={
            1: [MessageHandler(Filters.text & ~Filters.command, citati, pass_user_data=True)],
        },
        fallbacks=[CommandHandler('menu', menu)]
    )
    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler("weather", weather))
    updater.start_polling()
    updater.idle()


def start(update, context):
    reply_keyboard = [['/motivation', '/settings'],
                      ['/help']]
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
    update.message.reply_text(
        "функция  разработке")


def citati(update, context):
    context.user_data['locality'] = update.message.text
    print(context.user_data['locality'])
    if context.user_data['locality'] == 'текст':
        citat = ['Жизнь — это скульптура, которую вы создаете, когда делаете ошибки и учитесь на них',
                 'Секрет успеха — сделать первый шаг',
                 'Единственный способ найти выход — это пройти весь путь',
                 'Сколь высоких целей вы бы ни добились, нужно ставить новые ещё выше']
        update.message.reply_text(random.choice(citat))
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
    update.message.reply_text("функция  разработке")


if __name__ == '__main__':
    main()
