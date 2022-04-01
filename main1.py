from telegram.ext import Updater, MessageHandler, Filters
from telegram.ext import CallbackContext, CommandHandler
from telegram.ext import CommandHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup
import random


def main():
    updater = Updater('5103219044:AAGIibAfCpvXjLp8el1qy9T67bctCZj84iQ', use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("settings", settings))
    dp.add_handler(CommandHandler("help", help))
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('motivation', motivation)],
        states={
            1: [MessageHandler(Filters.text & ~Filters.command, citati, pass_user_data=True)],
        },
        fallbacks=[CommandHandler('menu', menu)]
    )
    dp.add_handler(conv_handler)
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


def settings(update, context):
    update.message.reply_text("функция  разработке")


if __name__ == '__main__':
    main()