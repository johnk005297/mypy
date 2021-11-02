### The task is to print out previous and next date in #mm.dd format using if cond statements
m31 = [1,3,5,7,8,10,12]
m30 = [4,6,9,11]
m28 = [2]
m,d = map(int, input().split())
# mm.dd
if m in m31:
    if d == 1:
        prevd = '30'
        nextd = '02'
        prevm = str(m-1)
        if m == 1:
            print(str(m31[-1]) + '.' + '31', end=' ')
            print('0' + str(m) + '.' + nextd) 
        elif m == 3:
            print('0' + str(m-1) + '.' + '28', end=' ')
            print('0' + str(m) + '.' + nextd)
        elif m == 8:
            print('0' + str(m-1) + '.' + '31', end=' ')
            print('0' + str(m) + '.' + nextd)
        elif 1 < m <= 9:              
            print('0' + str(m-1) + '.' + prevd, end=' ')
            print('0' + str(m) + '.' + nextd)        
        else:
            print(str(m-1) + '.' + prevd, end=' ')
            print(str(m) + '.' + nextd)
    elif 2 <= d < 9:
        prevd = '0' + str(d-1)
        nextd = '0' + str(d+1)
        # month check for format [mm.dd]
        if 1 <= m <= 9:              
            print('0' + str(m) + '.' + prevd, end=' ')
            print('0' + str(m) + '.' + nextd)    
        else:
            print(str(m) + '.' + prevd, end=' ')
            print(str(m) + '.' + nextd)
    elif 9 <= d <= 10:
        prevd = str(0) + str(d - 1)
        nextd = str(d + 1)
        if 1 <= m <= 9:              
            print('0' + str(m) + '.' + prevd, end=' ')
            print('0' + str(m) + '.' + nextd)    
        else:
            print(str(m) + '.' + prevd, end=' ')
            print(str(m) + '.' + nextd)
    elif 11 <= d <= 30:
        prevd = str(d - 1)
        nextd = str(d + 1)
        if 1 <= m <= 9:              
            print('0' + str(m) + '.' + prevd, end=' ')
            print('0' + str(m) + '.' + nextd)    
        else:
            print(str(m) + '.' + prevd, end=' ')
            print(str(m) + '.' + nextd)
    elif d == 31:            
        prevd = '30'
        nextd = '01'        
        if 1 <= m <= 8:              
            print('0' + str(m) + '.' + prevd, end=' ')
            print('0' + str(m+1) + '.' + nextd)
        elif m == 12:
            print(str(m) + '.' + prevd, end=' ')
            print('01' + '.' + nextd)  
        else:
            print(str(m) + '.' + prevd, end=' ')
            print(str(m+1) + '.' + nextd)
    else:
        print("Wrong date!")
elif m in m30:
    if d == 1:
        prevd = '31'
        nextd = '02'        
        if 4 <= m <= 6:              
            print('0' + str(m-1) + '.' + prevd, end=' ')
            print('0' + str(m) + '.' + nextd)
        elif m == 9:
            print('0' + str(m-1) + '.'+ prevd, end=' ')
            print('0' + str(m) + '.' + nextd)
        else:
            print(str(m-1) + '.' + prevd, end=' ')
            print(str(m) + '.' + nextd)
    elif 2 <= d < 9:
        prevd = '0' + str(d-1)
        nextd = '0' + str(d+1)
        # month check for format [mm.dd]
        if 1 <= m <= 9:              
            print('0' + str(m) + '.' + prevd, end=' ')
            print('0' + str(m) + '.' + nextd)    
        else:
            print(str(m) + '.' + prevd, end=' ')
            print(str(m) + '.' + nextd)
    elif 9 <= d <= 10:
        prevd = str(0) + str(d - 1)
        nextd = str(d + 1)
        if 1 <= m <= 9:              
            print('0' + str(m) + '.' + prevd, end=' ')
            print('0' + str(m) + '.' + nextd)    
        else:
            print(str(m) + '.' + prevd, end=' ')
            print(str(m) + '.' + nextd)
    elif 11 <= d <= 29:
        prevd = str(d - 1)
        nextd = str(d + 1)
        if 1 <= m <= 9:              
            print('0' + str(m) + '.' + prevd, end=' ')
            print('0' + str(m) + '.' + nextd)    
        else:
            print(str(m) + '.' + prevd, end=' ')
            print(str(m) + '.' + nextd)
    elif d == 30:            
        prevd = '29'
        nextd = '01'        
        if 1 <= m < 9:              
            print('0' + str(m) + '.' + prevd, end=' ')
            print('0' + str(m+1) + '.' + nextd)
        elif m == 9:
            print('0' + str(m) + '.' + prevd, end=' ')
            print(str(m+1) + '.' + nextd)        
        else:
            print(str(m) + '.' + prevd, end=' ')
            print(str(m+1) + '.' + nextd)
    else:
        print("Wrong date!")
elif m in m28:
    if d == 1:
        prevd = '31'
        nextd = '02'
        print('0' + str(m-1) + '.' + prevd, end=' ')
        print('0' + str(m) + '.' + nextd)        
    elif 2 <= d < 9:
        prevd = '0' + str(d-1)
        nextd = '0' + str(d+1)
        # month check for format [mm.dd]
        if 1 <= m <= 9:              
            print('0' + str(m) + '.' + prevd, end=' ')
            print('0' + str(m) + '.' + nextd)    
        else:
            print(str(m) + '.' + prevd, end=' ')
            print(str(m) + '.' + nextd)
    elif 9 <= d <= 10:
        prevd = str(0) + str(d - 1)
        nextd = str(d + 1)
        if 1 <= m <= 9:              
            print('0' + str(m) + '.' + prevd, end=' ')
            print('0' + str(m) + '.' + nextd)    
        else:
            print(str(m) + '.' + prevd, end=' ')
            print(str(m) + '.' + nextd)
    elif 11 <= d <= 27:
        prevd = str(d - 1)
        nextd = str(d + 1)
        if 1 <= m <= 9:              
            print('0' + str(m) + '.' + prevd, end=' ')
            print('0' + str(m) + '.' + nextd)    
        else:
            print(str(m) + '.' + prevd, end=' ')
            print(str(m) + '.' + nextd)
    elif d == 28:            
        prevd = '27'
        nextd = '01'        
        if 1 <= m <= 9:              
            print('0' + str(m) + '.' + prevd, end=' ')
            print('0' + str(m+1) + '.' + nextd)    
        else:
            print(str(m) + '.' + prevd, end=' ')
            print('01' + '.' + nextd)
    else:
        print("Wrong date!")


### 10 times more concise solution except a couple of checks!

# mon, day = map(int, input().split())
# monT = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
# if mon == 1 and day == 1:
#     print(f'31 декабря, прошлого года! {mon:02}.02')
# elif mon == 12 and day == 31:
#     print(f'{mon:02}.{(monT[mon - 1] - 1):02} 1 января следующего года')
# elif day == monT[mon - 1]:
#     print(f'{mon:02}.{(monT[mon - 1] - 1):02} {(mon + 1):02}.01')
# elif day == 1:
#     print(f'{(mon - 1):02}.{monT[mon + 1]:02} {mon:02}.02')
# else:
#     print(f'{mon:02}.{(day - 1):02} {mon:02}.{(day + 1):02}')
