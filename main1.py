# Импортируем необходимые классы.
from telegram.ext import Updater, MessageHandler, Filters
from telegram.ext import CallbackContext, CommandHandler
from telegram.ext import CommandHandler
from telegram import ReplyKeyboardMarkup


def start(update, context):
    reply_keyboard = [['/motivation', '/settings'],
                      ['/help']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
    update.message.reply_text(
        "Я бот-помощник, выберите интересующую вас функцию",
        reply_markup=markup
    )

def main():
    updater = Updater('5103219044:AAGIibAfCpvXjLp8el1qy9T67bctCZj84iQ', use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("motivation", motivation))
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("settings", settings))
    dp.add_handler(text_handler)
    updater.start_polling()
    updater.idle()


def help(update, context):
    update.message.reply_text(
        "функция  разработке")


def motivation(update, context):
    update.message.reply_text(
        "функция  разработке")


def settings(update, context):
    update.message.reply_text("функция  разработке")


# Запускаем функцию main() в случае запуска скрипта.
if __name__ == '__main__':
    main()