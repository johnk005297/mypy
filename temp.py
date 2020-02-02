db = [
    {
        "name": "Иванов Иван",
        "birthday": "04/05/1994",
        "height": 170,
        "weight": 70.5,
        "car": True,
        "languages": ["С#", "Ruby"]
    },
    {
        "name": "Петров Алексей",
        "birthday": "14/09/2000",
        "height": 178,
        "weight": 77,
        "car": False,
        "languages": ["С++", "Python"]
    },
    {
        "name": "Кириллов Вадим",
        "birthday": "01/12/1980",
        "height": 180,
        "weight": 90.5,
        "car": True,
        "languages": ["JavaScript", "Python"]
    }
    
]

while True:
    print("\n-----")
    print("Меню")
    print("-----")
    print("1. Список сотрудников.")
    print("2. Фильтр по языку программирования.")
    print("3. Средний рост сотрудников, моложе указанного г.р.")
    print("\nВыберите пункт меню или нажмите ENTER для выхода: ", end="")

    answer = input()

    if answer == "1":
        print("Содержимое базы данных ({}):".format(len(db)))
        for i, item in enumerate(db, start=1):
            print("{}.".format(i))
            print("Имя: {}".format(item["name"]))

            

    elif answer == "2":
        lang = input("Введите язык программирования: ")
        # "Нормализация" наименования языка на случай ошибки при вводе
        lang = lang.capitalize()

        # res - копия db, с сотрудниками, удовлетворяющими условию по языку
        res = []
        for item in db:
            if lang in item["languages"]:
                res.append(item)

        if len(res) > 0:
            print("Список сотрудников со знанием "
                  "языка программирования {} ({}):".format(lang, len(res)))
            for i, item in enumerate(res, start=1):
                print("{}.".format(i))
                print("Имя: {}".format(item["name"]))

                
        else:
            print("Таких сотрудников нет.")

    elif answer == "3":
        younger_than = int(input("Введите год рождения сотрудника: "))

        r_sum = 0
        r_col = 0
        for item in db:
            year = int(item["birthday"][-4:])
            if year >= younger_than:
                r_sum += item["height"]
                r_col += 1

        if r_col > 0:
            print("Средний рост сотрудников, {} г.р. и моложе: ({:.1f}) см.".
                  format(younger_than, r_sum / r_col))
        else:
            print("Таких сотрудников нет.")

    else:
        break

print("smth to reveal the changes")