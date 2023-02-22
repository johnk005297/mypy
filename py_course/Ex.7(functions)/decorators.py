#
# 
def decorator(func):  # Сюда передаём функцию которую нужно декорировать
    def wrapper(*args, **kwargs):  # Сюда передаём аргументы декорированной функции
        print(f'{func.__name__} started')  # декорирующие действия 1
        result = func(*args, **kwargs)  # *args -чтобы работать с разным кол-вом аргументов
        print(f'{func.__name__} finished')  # декорирующие действия 2
        return result  # возвращаем результат

    return wrapper  # передаём ссылку на вложенную функцию


@decorator  # сахар для вызова декоратора (навешиваем декоратор)
def summ(a, b):  # функция которую нужно декорировать в этот момент: wrapper запустит summ
    return a + b


# print(summ(2, 3))



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