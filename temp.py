# from string import ascii_lowercase as letters

# key = {}
# # for x in range(len(letters)):
# #     key[letters[x]] = x+1

# num = list(range(1,29))

# key = dict(zip(num, letters))
# print(key)


# with open("C:\\Users\\johnk\\Desktop\\sizes.txt", "r",encoding='utf-8') as file:
#     f = file.read()
# f = f.split()

# book = {}

# for word in f:
#     if word not in book:
#         book[word] = 1
#     else:
#         book[word] += 1

# print(book)

# def phone_number():
#     x = input("Enter your phone number: ")
#     print(f'({x[:3]})-{x[3:6]}-{x[6:8]}-{x[8:]}')

# phone_number()




# students = ['polly', 'bob', 'jack', 'roberta']
# s_dict = {student[0].upper(): student for student in students}
# print(s_dict)

from datetime import datetime

def not_during_the_night(func):
    # print("I'm here!")
    def wrapper():        
        if 7 <= datetime.now().hour < 22:
            func()         
        else:
            print(f'It\'s {datetime.now().hour}')
    return wrapper


# @not_during_the_night       # It's the same way as <anyLink = not_during_the_night(poop)>, but only using decorators!
# def poop():
#     print('ONe poop man')

def wrapper(f):    
    def upper_func():
        return f().upper()
    print(upper_func())

# @wrapper
def hi():
    return 'hi'

