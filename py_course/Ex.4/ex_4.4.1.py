# 
# ******** Pascal's triangle ************

lst: list = []

for y in range(10):
    row = [1] * (y + 1)    
    for x in range(y + 1):           
        if x != 0 and x != y:
            row[x] = lst[y-1][x-1] + lst[y-1][x]

    lst.append(row)

for x in lst:
    print(x)
    




    

