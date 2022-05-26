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

#----------------------------End of Task 6.1.1----------------------------------------------


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


#----------------------------End of Task 6.1.2----------------------------------------------



