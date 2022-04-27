def citati(update, context):
    keyboard = [[
        InlineKeyboardButton("в меню", callback_data='menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.user_data['locality'] = update.message.text
    print(context.user_data['locality'])
    if context.user_data['locality'] == 'текст':
        db_sess = db_session.create_session()
        base = list(db_sess.query(Citat.name).all())
        print(base)
        update.message.reply_text(random.choice(base)[0], reply_markup=reply_markup)
    elif context.user_data['locality'] == 'картинка':
        jp = open('images/c1.jpg', 'rb')
        context.bot.send_photo(
            update.message.chat_id,
            jp)
        update.message.reply_text('вернуться в меню', reply_markup=reply_markup)
    else:
        update.message.reply_text('что-то пошло не так, попробуйте еще раз;)', reply_markup=reply_markup)
        citati()
    context.user_data.clear()
    return ConversationHandler.END