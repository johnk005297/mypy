from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
# MessageHandler - это широкий обработчик, который может реагировать на большой тип сообщений.
# CommandHendler - это узко-нишевой обработчик, который реагирует только на команды.
import logging
import settings


logging.basicConfig(filename="bot.log", level=logging.INFO)

def greet_user(update, context):        # every function must have two args: update and context
    update.message.reply_text("Hello, user!")

def talk_to_me(update,context):    
    text = update.message.text      # input from the user    
    update.message.reply_text(text) # bots reply message in telegram

def guess_number(update, context):
    print(context.args)
    if context.args:
        try:
            user_number = int(context.args[0])
            message = f"You number is {user_number}"
        except(TypeError, ValueError):
            message = "Need to enter integer!"
    else:
        message = "Enter a number!"    
    update.message.reply_text(message)



def main():
    mybot = Updater(settings.API_KEY,use_context=True)

    disp = mybot.dispatcher
    disp.add_handler(CommandHandler("start", greet_user))
    disp.add_handler(CommandHandler("guess", guess_number))
    disp.add_handler(MessageHandler(Filters.text, talk_to_me))
    logging.info("Bot has started...")
    
    mybot.start_polling()
    mybot.idle()


if __name__ == "__main__":
    main()