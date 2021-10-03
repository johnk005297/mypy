from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
# MessageHandler - это широкий обработчик, который может реагировать на большой тип сообщений.
# CommandHendler - это узко-нишевой обработчик, который реагирует только на команды.
import logging                      # used in take_logs function
import settings
from random import randint          # used in play_random_number function
from glob import glob               # used in send_picture function


def take_logs():    
    logging.basicConfig(filename="bot.log", format="%(asctime)s  %(levelname)s:%(name)s  %(message)s", level=logging.INFO, datefmt="%Y-%b-%d %H:%M:%S") 
        

def greet_user(update, context):        # every function must have two args: update and context
    update.message.reply_text("Hello, user!")

def talk_to_me(update,context):    
    text = update.message.text      # input from the user    
    update.message.reply_text(text) # bots reply message in telegram

def play_random_number(user_number):
    bot_number = randint(user_number - 10, user_number + 10)    
    if user_number > bot_number:
        message = f"Your number {user_number}, mine {bot_number}. You win!"
    elif user_number == bot_number:
        message = f"Your number {user_number}, mine {bot_number}. It's a draw!"
    elif user_number < bot_number:
        message = f"Your number {user_number}, mine {bot_number}. I win! Hehehe"
    else: pass
    return message

def guess_number(update, context):    
    if context.args:
        try:
            user_number = int(context.args[0])  # context.args is a list, so taking 1st element by index
            # message = f"You number is {user_number}"
            message = play_random_number(user_number)
        except(TypeError, ValueError):
            message = "Need to enter integer!"
    else:
        message = "Enter a number!"    
    update.message.reply_text(message)

def send_picture():
    pass

def main():
    mybot = Updater(settings.API_KEY,use_context=True)

    disp = mybot.dispatcher
    disp.add_handler(CommandHandler("start", greet_user))
    disp.add_handler(CommandHandler("guess", guess_number))
    disp.add_handler(CommandHandler("send_pic", send_picture))
    disp.add_handler(MessageHandler(Filters.text, talk_to_me))    
    
    mybot.start_polling()
    mybot.idle()


if __name__ == "__main__":    
    take_logs()
    main()
    
    