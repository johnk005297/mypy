from emoji import emojize           # used in send_emoji function
from glob import glob               # used in send_picture function
import logging                      # used in take_logs function
from random import randint, choice  # used in play_random_number function and send_picture function
import settings
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
# MessageHandler - это широкий обработчик, который может реагировать на большой тип сообщений.
# CommandHendler - это узко-нишевой обработчик, который реагирует только на команды.

def take_logs():    
    logging.basicConfig(filename="bot.log", format="%(asctime)s  %(levelname)s: %(name)s    %(message)s", level=logging.INFO, datefmt="%Y-%b-%d %H:%M:%S") 
        

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
    else:
        message = "Something went wrong! Check logs!"
    return message

def guess_number(update, context):
    if context.args:
        try:
            user_number = int(context.args[0])  # context.args is a list, so taking 1st element by index            
            message = play_random_number(user_number)
        except(TypeError, ValueError):
            message = "Need to enter integer!"
    else:
        message = "Enter a number!"    
    update.message.reply_text(message)

def show_update_data(update, context):    
    #update.message.reply_text(f"{update}")
    pass
    
def help(update, context):
    options_dict = {
            "/start": "Greetin user", "/guess": "Guess number game", "/send_pic": "Receive a picture", 
            "/show_update": "update data"
                    }    
    update.message.reply_text(options_dict)
    

def send_picture(update, context):
    photo_list = glob("images/c*.*")
    photo_file_name = choice(photo_list)
    chat_id_var = update.effective_chat.id
    context.bot.send_photo(chat_id=chat_id_var, photo=open(photo_file_name, "rb"))

def send_emoji():
    pass

def main():
    mybot = Updater(settings.API_KEY,use_context=True)

    disp = mybot.dispatcher
    disp.add_handler(CommandHandler("start", greet_user))
    disp.add_handler(CommandHandler("guess", guess_number))
    disp.add_handler(CommandHandler("send_pic", send_picture))
    disp.add_handler(CommandHandler("show_update", show_update_data))
    disp.add_handler(CommandHandler("help", help))
    disp.add_handler(MessageHandler(Filters.text, talk_to_me))    
    
    mybot.start_polling()
    mybot.idle()


if __name__ == "__main__":    
    take_logs()
    main()
    
    
    