def ask_user(prompt, retries=3, hint="Ответьте, ДА или НЕТ?"):
    while True:
        retries -= 1
        ok = input(prompt + " -> ").upper()

        if ok in ("Д", "ДА"):
            return True
        elif ok in ("Н", "НЕТ"):
            return False

        if retries <= 0:
            print("Не смог получить нужный ответ, считаю за отказ.")
            return False
        print(hint)

if ask_user("Сохранить файл?"):
    print("Сохранил!")
else:
    print("Не сохранил.")