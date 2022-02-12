### Show day of the week based on day number
x = int(input()) - 1

 
if x >= 7 or x == -1:
    print("There are 7 days in a week!")
elif x%7 == 0:
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
elif x%7 == 6:
    print("Воскресенье")
else:
    print("Smth went wrong!")   


### second variant

# week_days = ["Понедельник","Вторник","Среда","Четверг","Пятница","Суббота","Воскресенье"]
# x = int(input()) - 1
# print(week_days[x%7])

