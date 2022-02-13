#
############  CHECK IF ROWS AND COLUMNS ARE SIMMETRIC ###############
import sys
lst = [[2,3,4,5,6],[3,2,7,8,9],[4,7,2,0,4],[5,8,0,2,1],[6,9,4,1,2]]

for x in range(len(lst)):
    print(*lst[x])
print('---------')

      
for x in range(len(lst)):
    for y in range(x+1,len(lst)):
        if lst[x][y] != lst[y][x]:
            print(False)
            sys.exit()
print(True)            

     
    
    

    
    
