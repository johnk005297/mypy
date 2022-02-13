## 
## **************** GREEDY ALTORITHM ******************
lst: list = [1,2,4,8,16,32,64]
n = int(input())
a: list = []

while True:
    if sum(a) >= n:
        break
    for x in lst[::-1]:
        while x <= (n - sum(a)):            
            a.append(x)
            
        
print(*a)