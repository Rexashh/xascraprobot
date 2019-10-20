#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Shrimadhav U K


import logging
import json

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, ParseMode)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)

from config import Development as Config

from helper_funcs.step_one import request_tg_code_get_random_hash
from helper_funcs.step_two import login_step_get_stel_cookie
from helper_funcs.step_three import scarp_tg_existing_app
from helper_funcs.step_four import create_new_tg_app


# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)


INPUT_PHONE_NUMBER, INPUT_TG_CODE = range(2)
GLOBAL_USERS_DICTIONARY = {}


def start(update, context):
    update.message.reply_text(
        'Hi! '
        'Thank you for using me 😬 \n'
        'Enter your Telegram Phone Number, to get the APP ID from my.telegram.org',
        parse_mode=ParseMode.HTML
    )
    return INPUT_PHONE_NUMBER


def input_phone_number(update, context):
    user = update.message.from_user
    logger.info("Received Input of %s: %s", user.first_name, update.message.text)
    input_text = update.message.text
    random_hash = request_tg_code_get_random_hash(input_text)
    GLOBAL_USERS_DICTIONARY.update({
        user.id: {
            "input_phone_number": input_text,
            "random_hash": random_hash
        }
    })
    update.message.reply_text(
        'I see! now please send the Telegram code that you received from Telegram! ',
        parse_mode=ParseMode.HTML
    )
    return INPUT_TG_CODE


def input_tg_code(update, context):
    user = update.message.from_user
    logger.info("Tg Code of %s: %s", user.first_name, update.message.text)
    current_user_creds = GLOBAL_USERS_DICTIONARY.get(user.id)
    s, c = login_step_get_stel_cookie(
        current_user_creds.get("input_phone_number"),
        current_user_creds.get("random_hash"),
        update.message.text
    )
    if s:
        update.message.reply_text('recieved code. Scarpping web page ...')
        t, v = scarp_tg_existing_app(c)
        if not t:
            create_new_tg_app(
                c,
                v.get("tg_app_hash"),
                "usetgbot",
                "usetgbot"
                "https%3A%2F%2Ftelegram.dog%2FGetMyTGAppBot",
                "other",
                "created+using+https%3A%2F%2Ftelegram.dog%2FGetMyTGAppBot"
            )
        t, v = scarp_tg_existing_app(c)
        if t:
            me_t = json.dumps(v, sort_keys=True, indent=4)
            me_t += "\n\n❤️ @SpEcHlDe"
            update.message.reply_text(
                me_t,
                parse_mode=ParseMode.HTML
            )
        else:
            update.message.reply_text("something wrongings. failed to get app id. ")
    else:
        update.message.reply_text(c)
    return ConversationHandler.END


def cancel(update, context):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('Bye! I hope we can talk again some day.',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(Config.TG_BOT_TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add conversation handler with the states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            INPUT_PHONE_NUMBER: [MessageHandler(Filters.text, input_phone_number)],

            INPUT_TG_CODE: [MessageHandler(Filters.text, input_tg_code)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()