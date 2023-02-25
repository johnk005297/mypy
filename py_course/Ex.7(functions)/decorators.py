#
# 
### Pattern ###
def decorator(func):  # Сюда передаём функцию, которую нужно декорировать
    def wrapper(*args, **kwargs):  # Сюда передаём аргументы декорированной функции
        print(f'{func.__name__} started')  # декорирующие действия 1
        result = func(*args, **kwargs)  # *args - чтобы работать с разным кол-вом аргументов
        print(f'{func.__name__} finished')  # декорирующие действия 2
        return result  # возвращаем результат

    return wrapper  # передаём ссылку на вложенную функцию


@decorator  # сахар для вызова декоратора (навешиваем декоратор)
def summ(a, b):  # функция, которую нужно декорировать в этот момент: wrapper = summ
    return a + b

# print(summ(2, 3))
### The end ###


def func_show(func):
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)
        print("Площадь прямоугольника:", res)
        return res
    return wrapper

@func_show
def get_sq(width, height):
    return width*height


# get_sq(5,5)


def show_menu(func):
    def wrapper(s):
        res = func(s)
        for x in res:
            print(x)
    return wrapper
        
@show_menu
def get_menu(s:str):
    lst = s.split()
    return lst

inp = '123 asdf ttt'
# get_menu(inp)


# put your python code here
def decorator(fn):
    def wrapper(*args, **kwargs):
        res = fn(*args, **kwargs)
        res.sort()
        return res
    return wrapper

@decorator
def get_list(*args, **kwargs):
    lst:list = [int(x) for x in args[0].split()]
    return lst

# lst = get_list(input())
# print(*lst)

''' 
Подвиг 7.11.4 
Вводятся две строки из слов (слова записаны через пробел). Объявите функцию, которая преобразовывает эти две строки в два списка слов и возвращает эти списки.
Определите декоратор для этой функции, который из двух списков формирует словарь, в котором ключами являются слова из первого списка, а значениями - соответствующие элементы из второго списка. 
Полученный словарь должен возвращаться при вызове декоратора.
Примените декоратор к первой функции и вызовите ее для введенных строк. Результат (словарь d) отобразите на экране командой:
print(*sorted(d.items()))
'''

# Option 1
# a = input()
# b = input()
def decorator(fn):
    def wrapper(a,b):
        data = fn(a,b)
        d = {}
        for x in range(len(data[0])):
            d[data[0][x]] = data[1][x]
        return d
    return wrapper


@decorator
def return_list(a:str,b:str):
    l1 = a.split()
    l2 = b.split()
    return l1,l2

# d = return_list(a,b)
# print(*sorted(d.items()))


# Option 2
def show_sorted(func): 
    return lambda *args, **kwards: dict(zip(*func(*args, **kwards)))

@show_sorted
def get_lists(s1, s2):
    return s1.split(), s2.split()

# print(*sorted(get_lists(input(), input()).items()))


# Option 3
def show_sorted(func): 
    return lambda *args, **kwards: dict(zip(*func(*args, **kwards)))

@show_sorted
def get_lists(s1, s2):
    return s1.split(), s2.split()

# print(*sorted(get_lists(input(), input()).items()))




'''
Подвиг 7.11.5
Объявите функцию, которая принимает строку на кириллице и преобразовывает ее в латиницу, используя следующий словарь для замены русских букв на соответствующее латинское написание:
Функция должна возвращать преобразованную строку. Замены делать без учета регистра (исходную строку перевести в нижний регистр - малые буквы). 
Все небуквенные символы ": ;.,_" превращать в символ '-' (дефиса).

Определите декоратор для этой функции, который несколько подряд идущих дефисов, превращает в один дефис. Полученная строка должна возвращаться при вызове декоратора.
(Сам декоратор на экран ничего выводить не должен).
'''
t = {'ё': 'yo', 'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ж': 'zh',
     'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p',
     'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'c', 'ч': 'ch', 'ш': 'sh',
     'щ': 'shch', 'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'}



# Option 1

    # Пояснение: 
    #   добавляем знаки препинания ': ;.,_' в словарь dict.fromkeys(': ;.,_', '-') распаковкой словарей
    #   методы строк maketrans и translate для шифрования/дешифрования
    #   регулярка для удаления лишних дефисов
    #   лямда функция в качестве вложенной функции декоратора.

import re
def hyphenator(func):    
    return lambda *args, **kwards: re.sub(r'-+', '-', func(*args, **kwards))

@hyphenator
def transliterate(s):
    return s.lower().translate(str.maketrans({**t, **dict.fromkeys(': ;.,_', '-')}))    
    
# print(transliterate(input()))


# Option 2

def del_dash(fn):
    def wrapper(s):
        s = fn(s)
        while '--' in s:
            s = s.replace('--', '-')
        return s
    return wrapper

@del_dash
def ru_en(s):
    st = ''
    for i in s:
        if i in t:
            st += t[i]
        elif i in ": ;.,_":
            st += '-'
        else:
            st += i          
    return st

# s = input().lower()
# d = ru_en(s)
# print(d)


'''
    Подвиг 7.12.1. 
    Вводится строка целых чисел через пробел. Напишите функцию, которая преобразовывает эту строку в список чисел и возвращает их сумму.
    Определите декоратор для этой функции, который имеет один параметр start - начальное значение суммы.
    Примените декоратор со значением start=5 к функции и вызовите декорированную функцию для введенной строки s:
    s = input()
    Результат отобразите на экране.
'''

# Option 1
def summ_value_decor(start=0):
    def decorator(fn):
        def wrapper(s):
            res = fn(s) + start
            return res
        return wrapper
    return decorator

@summ_value_decor(start=0)
def summ(s:str):
    lst = sum(int(x) for x in s.split())
    return lst

# s = input()
# summ_value_decor = summ(s)
# print(summ_value_decor)

# Option 2
def my_decorator(start):
    def sum_list(fn):
        def wrapper(*args):
            return start + fn(*args)
        return wrapper
    return sum_list

@my_decorator(start=5)
def get_list(s:str):
    return sum(list(map(int, s.split())))

# s = input()
# summ = get_list(s)
# print(summ)


'''
    Подвиг 7.12.2.
    Объявите функцию, которая возвращает переданную ей строку в нижнем регистре (с малыми буквами). 
    Определите декоратор для этой функции, который имеет один параметр tag, определяющий строку с названием тега и начальным значением "h1". 
    Этот декоратор должен заключать возвращенную функцией строку в тег tag и возвращать результат.
    Пример заключения строки "python" в тег h1: <h1>python</h1>
    Примените декоратор со значением tag="div" к функции и вызовите декорированную функцию для введенной строки s:
    s = input()
    Результат отобразите на экране.
'''

# Option 1
def tag_decor(tag=''):
    def decorator(fn):
        def wrapper(*args):
            res = f'<{tag}>{fn(*args)}</{tag}>'
            return res
        return wrapper
    return decorator

@tag_decor(tag='div')
def make_lower(s):
    return s.lower()

# s = input()
# print(make_lower(s))

# Option 2
def tag_encloser(tag='h1'):
    return lambda func: lambda *args, **kwards: f'<{tag}>{func(*args, **kwards)}</{tag}>'

@tag_encloser(tag='div')
def make_lower(s:str):
    return s.lower()

# s = input()
# print(make_lower(s))


'''
    Подвиг 7.12.3.
    Объявите функцию, которая принимает строку на кириллице и преобразовывает ее в латиницу.
    Функция должна возвращать преобразованную строку. Замены делать без учета регистра (исходную строку перевести в нижний регистр - малые буквы). 

    Определите декоратор с параметром chars и начальным значением " !?", который данные символы преобразует в символ "-" и, кроме того, 
    все подряд идущие дефисы (например, "--" или "---") приводит к одному дефису. Полученный результат должен возвращаться в виде строки.
    Примените декоратор с аргументом chars="?!:;,. " к функции и вызовите декорированную функцию для введенной строки s:
    s = input()
    Результат отобразите на экране.
'''

# Option 1
def transform_symbols(chars=''):
    def decorator(fn):
        def wrapper(*args):
            res = fn(*args)
            modified = ''
            for x in res:
                if x in chars:
                    modified += '-'
                else:
                    modified += x
            while '--' in modified:
                modified = modified.replace('--', '-')
            return modified
            
        return wrapper
    return decorator

@transform_symbols(chars='?!:;,. ')
def transform(s):
    res = ''
    for x in s:
        if x in t:
            res += t[x]
        else:
            res += x
    return res

# s = input().lower()
# print(transform(s))


# Option 2
import re

def code(s:str, cipher):
    return s.translate(str.maketrans(cipher))

def punctuator(chars='!?'):
    def hyphenator(func):   
        def wrapper(*args, **kwards):
            return re.sub(r'-+', '-', code(func(*args, **kwards), dict.fromkeys(chars, '-')))
        return wrapper
    return hyphenator

@punctuator(chars='?!:;,. ')
def transliterator(s:str):
    return code(s.lower(), t)    

# s = input()
# print(transliterator(s))



'''
Подвиг 7.12.4.
Объявите функцию с именем get_list и следующим описанием в теле функции:
 # Функция для формирования списка целых значений

Сама функция должна формировать и возвращать список целых чисел, который поступает на ее вход в виде строки из целых чисел, записанных через пробел.
Определите декоратор, который выполняет суммирование значений из списка этой функции и возвращает результат.
Внутри декоратора декорируйте переданную функцию get_list с помощью команды @wraps (не забудьте сделать импорт: from functools import wraps). 
Такое декорирование необходимо, чтобы исходная функция get_list сохраняла свои локальные свойства: __name__ и __doc__.

Примените декоратор к функции get_list, но не вызывайте ее.
'''



from functools import wraps

# здесь продолжайте программу
def summ_values_in_list(fn):
    @wraps(fn)
    def wrapper(*args):
        res = sum(fn(*args))
        return res
    return wrapper

@summ_values_in_list
def get_list(inp):
    '''Функция для формирования списка целых значений'''
    lst = [int(x) for x in inp.split()]
    return lst