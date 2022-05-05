##
N = 4
# lst: list = []
# for x in range(1,N+1):
#     lst.append([x]*N)


# lst: list = [[x for y in range(1,N+1)] for x in range(1,N+1)]    

# for x in lst:
#     for y in x:
#         print(y,end=' ')
#     print()

               
a: list = ['Москва', '15000', 'Уфа', '1200', 'Самара', '1090', 'Казань', '1300']
## List comprehantion example ##
lst: list = [  [a[x-1]] + [int(a[x])]
                for x in range(1, len(a), 2) ]

print(lst)
