#
# Print simple numbers less input number

n = int(input())
a: list = list(range(2,n))
for x in range(2,n):
    for y in range(2,x):
        if x%y==0:
            a.remove(x)
            break
print(*a)

        
           
    
