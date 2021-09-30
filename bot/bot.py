from telegram.ext import Updater

def main():
    mybot = Updater("api_key",use_context=True)

    mybot.start_polling()
    mybot.idle()

main()