# Find minimum number using if condition
a,b,c = map(int, input().split())

if a < b:
    if a < c:
        print(a)
    else: # a > c
        print(c)
else: # a > b
    if b < c:
        print(b)
    else: # b > c
        print(c)