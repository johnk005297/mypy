### Show day of the week based on week number
x = int(input()) - 1

if x%7 == 0:
    print("Понедельник")
elif x%7 == 1:
    print("Вторник")
elif x%7 == 2:
    print("Среда")
elif x%7 == 3:
    print("Четверг")
elif x%7 == 4:
    print("Пятница")
elif x%7 == 5:
    print("Суббота")
else:
    print("Воскресенье")    


### second variant

# week_days = ["Понедельник","Вторник","Среда","Четверг","Пятница","Суббота","Воскресенье"]
# x = int(input()) - 1
# print(week_days[x%7])

