from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
# MessageHandler - это широкий обработчик, который может реагировать на большой тип сообщений.
# CommandHendler - это узко-нишевой обработчик, который реагирует только на команды.
import logging
import settings


logging.basicConfig(filename="bot.log", level=logging.INFO)

def greet_user(update, context):    
    update.message.reply_text("Hello, user!")

def talk_to_me(update,context):
    text = update.message.text    
    update.message.reply_text(text)

def main():
    mybot = Updater(settings.API_KEY,use_context=True)

    disp = mybot.dispatcher
    disp.add_handler(CommandHandler("start", greet_user))
    disp.add_handler(MessageHandler(Filters.text, talk_to_me))
    logging.info("Bot has started...")
    
    mybot.start_polling()
    mybot.idle()


if __name__ == "__main__":
    main()