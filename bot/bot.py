from telegram.ext import Updater

def main():
    mybot = Updater("2021736250:AAEYroXQ5sbWIwaj0HukMVhwy6C7cNNdp04",use_context=True)

    mybot.start_polling()
    mybot.idle()

main()