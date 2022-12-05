'''
    Сформировать последовательность Фиббоначи, количество значений в которой
    лимитировано вводимым натруральным числом N.
'''

def fib_rec(N=7, f=[]):

    count = 1
    if N > count:
        fib_rec(N-1)
    if N <= 2:
        f.append(1)
    else:
        f.append(f[N-3] + f[N-2])

    return f
    

def fib_rec2(N=2, f=[]):

    f.append(f[-1] + f[-2]) if len(f) > 1 else f.append(1)
    return f if len(f) == N else fib_rec2(N, f)




def fib_rec3(N=7, f=[1, 1]):
    if len(f) < N:
        f.append(f[-1] + f[-2])
        fib_rec3(N, f)

    return f


'''
    Имеется следующий многомерный список: d = [1, 2, [True, False], ["Москва", "Уфа", [100, 101], ['True', [-2, -1]]], 7.89]
    С помощью рекурсивной функции get_line_list создать на его основе одномерный список из значений элементов списка d. 
    Функция должна возвращать новый созданный одномерный список.
'''

d = [1, 2, [True, False], ["Москва", "Уфа", [100, 101], ['True', [-2, -1]]], 7.89]
def get_line_list(d,a=[]):

    for item in d:
        if isinstance(item, list):
            get_line_list(item)
        else:
            a.append(item)
    return a

f = get_line_list(d)
