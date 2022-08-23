#

'''
Patterns to create dictionary using dict() function:

  #1  dict(one=1, two=2)
  #2  dict({'one': 1, 'two': 2})
  #3  dict(zip(('one', 'two'), (1, 2)))
  #4  dict([ ['two', 2], ['one', 1] ])

'''


'''
Task 6.1.1
    Input value: one=1 two=2 three=3. 
    Need to make Output -> ('one', 1) ('three', 3) ('two', 2) using dict() function.
'''

#--------------------------------------- Solution 1 ---------------------------------------
# input = one=1 two=2 three=3

def solution1():

    inp = input().replace(' ',',').replace('=',',').split(',')    # Output: ['one', '1', 'two', '2', 'three', '3']

    ab: list = [ [inp[x-1]] + [int(inp[x])]
                    for x in range(1, len(inp), 2) ]              # Output: {'one': 1, 'two': 2, 'three': 3}

    ab = dict(ab)
    print(*sorted(ab.items()))
    


#--------------------------------------- Solution 2 ---------------------------------------
# input = one=1 two=2 three=3


def solution2():

    inp = input().split()         # ['one=1', 'two=2', 'three=3']
    d = [[i.split('=')[0], int(i.split('=')[1])] 
                            for i in inp]

    d = dict(d)
    print(*sorted(d.items()))
    

#--------------------------------------- Solution 3 ---------------------------------------
# input = one=1 two=2 three=3

def solution3():
    i = input().split()
    b=[x.split("=") for x in i]     # [['one', '1'], ['two', '2'], ['three', '3']]

    for i in b:
        i[1]=int(i[1])
    d=dict(b)
    print(*sorted(d.items()))

''' End of Task 6.1.1 '''


'''
Task 6.1.2
    Input value: ['5=отлично', '4=хорошо', '3=удовлетворительно']
    Need to make Output as (3, 'удовлетворительно') (4, 'хорошо') (5, 'отлично'), without using dict() function.
    
'''
# import sys

#--------------------------------------- Solution 4 ---------------------------------------
def solution4():
    
    # считывание списка из входного потока
    # lst_in = list(map(str.strip, sys.stdin.readlines()))
    lst_in = ['5=отлично', '4=хорошо', '3=удовлетворительно']
    d = {}
    for x in lst_in:        
        d[int(x.split('=')[0])] = x.split('=')[1]
            
    print(*sorted(d.items()))


#--------------------------------------- Solution 5 ----------------------------------------

def solution5():

    lst_in = ['5=отлично', '4=хорошо', '3=удовлетворительно']
    lst = [i.split('=') for i in lst_in]
    d = {int(x): y for x,y in lst}
    print(d)


''' End of Task 6.1.2 '''



'''
Task 6.1.3
    Вводятся данные в формате ключ=значение в одну строчку через пробел. 
    Необходимо на их основе создать словарь d, затем удалить из этого словаря ключи 'False' и '3', если они существуют. 
    Ключами и значениями словаря являются строки. Вывести полученный словарь на экран.

    Input: лена=имя дон=река москва=город False=ложь 3=удовлетворительно True=истина
'''
#--------------------------------------- Solution 6 ----------------------------------------

def solution6():
    d = dict( x.split('=') for x in input().split())

    if 'False' in d.keys(): del d['False']
    if '3' in d.keys(): del d['3']  
    print(*sorted(d.items()))

#--------------------------------------- Solution 7 ----------------------------------------

def solution7():
    d = {i.split('=')[0]: i.split('=')[1] for i in input().split() if i.split('=')[0] not in ['False', '3']}
    print(*sorted(d.items()))

''' End of Task 6.1.3 '''    



'''
Task 6.1.4
    Вводятся номера телефонов в формате:
    номер_1 имя_1
    номер_2 имя_2
    ...
    номер_N имя_N

    Необходимо создать словарь d, где ключами будут имена, а значениями - список номеров телефонов для этого имени. Обратите внимание, что одному имени может принадлежать несколько разных номеров.

    Input: +71234567890 Сергей, +71234567810 Сергей, +51234567890 Михаил, +72134567890 Николай

    import sys
    # считывание списка из входного потока
    lst_in = list(map(str.strip, sys.stdin.readlines()))

'''
def solution8():

    d = dict()
    lst_in = ['+71234567890 Сергей', '+71234567810 Сергей', '+51234567890 Михаил', '+72134567890 Николай']    
    for x in lst_in:
        d[x.split()[1]] = d.get(x.split()[1], []) + [x.split()[0]]
        

    
    ## .get method above is an equivalent for this construction
    # for x in lst_in:
    #     if x.split()[1] not in d.keys():
    #         d[x.split()[1]] = [x.split()[0]]
    #     else:                           
    #         d[x.split()[1]] += [x.split()[0]]
    
    return d

''' End of Task 6.1.4 '''


'''
Task 6.1.5
    Дни рождений и имена могут повторяться. На их основе сформировать словарь и вывести его в формате:
    день рождения 1: имя1, ..., имяN1
    день рождения 2: имя1, ..., имяN2
'''
def solution9():    
    
    lst = ['3 Сергей', '5 Николай', '4 Елена', '7 Владимир', '5 Юлия', '4 Светлана']
    d: dict = {}

    # First variant of solution for this task
    '''
    for x in lst:
        if x.split()[0] in d:
            d[x.split()[0]] += [x.split()[1]]
        else:
            d[x.split()[0]] = [x.split()[1]]
    
    for k,v in d.items():
        print(k + ":", ", ".join(v))
    '''

    # Second variant of solution for this task
    '''
    d2 = {}
    for i in lst:
        key, value = i.split()
        d2.setdefault(key, []).append(value)
    
    [print(f'{key}: {", ".join(value)}') for key, value in d2.items()]
    '''

    # Third variant of solution for this task
    '''
    d3 = {}
    for i in lst:
        key, value = i.split()
        d3[key] = d3.get(key, []) + [value]

    for key, value in d3.items():
        print(f'{key}: ', end='')
        print(*value, sep=', ')

    '''

''' End of Task 6.1.5 '''



def solution10():

    '''
        Имеется словарь с наименованиями предметов и их весом (в граммах):
        Сергей собирается в поход и готов взвалить на свои хрупкие плечи максимальный вес в N кг (вводится с клавиатуры). Он решил класть в рюкзак предметы в порядке убывания их веса (сначала самые тяжелые, затем, все более легкие) так, чтобы их суммарный вес не превысил значения N кг. Все предметы даны в единственном экземпляре. Выведите список предметов (в строчку через пробел), которые берет с собой Сергей в порядке убывания их веса.
    '''
    things = {'карандаш': 20, 'зеркальце': 100, 'зонт': 500, 'рубашка': 300, 
            'брюки': 1000, 'бумага': 200, 'молоток': 600, 'пила': 400, 'удочка': 1200,
            'расческа': 40, 'котелок': 820, 'палатка': 5240, 'брезент': 2130, 'спички': 10}

    N = 10000
    sum = 0
    srt = sorted(things.values(), reverse=True)
    # for k,v in things.items():
    #     if sum < N+1:
    #         print(k,end=' ')
    #         sum += v
    #     else:
    #         continue

    markdict = {"Tom":67, "Tina": 54, "Akbar": 87, "Kane": 43, "Divya":73}
# marklist=sorted((value, key) for (key,value) in markdict.items())
# sortdict=dict([(k,v) for v,k in marklist])
# print(sortdict)

solution10()


