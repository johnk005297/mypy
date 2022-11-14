############### CHECK if there are any 1 around other 1 except 0 in lst array #####################
import sys

def solution1():
    lst = [[0,0,0,0,0],[0,0,0,0,0],[0,0,1,0,0],[0,0,0,0,0],[1,1,0,0,0]]
    # display the array ##
    for x in lst:
        for y in x:
            print(y,end=' ')
        print()

    for x in lst:
        x.insert(0,0)
        x.append(0)

    lst.insert(0,[0]*7)
    lst.append([0]*7)

    for x,y in enumerate(lst[1:-1],1):
        for a,b in enumerate(y[1:-1],1):
            if b == 1:
                if y[a-1] or y[a+1] == 1 or 1 in lst[x-1][a-1:a+2] + lst[x+1][a-1:a+2]:                              
                    sys.exit(print("There are neighbors as 1! (solution one)"))
                            
    print("No neighbors as 1! (solution one)")

#######################################################################################################################
################################    THE SECOND VARIANT    #############################################################

def solution2():
    lst = [[1,0,0,0,0],[0,0,0,0,0],[0,0,1,0,0],[0,0,0,0,0],[1,0,0,0,0]]
    ## display the array ##
    for x in lst:
        for y in x:        
            print(y,end=' ')
        print()

    for x in lst:
        x.insert(0,0)
        x.append(0)

    lst.insert(0,[0]*7)
    lst.append([0]*7)

    n, result = len(lst), "\nNo neighbors as 1! (solution two)"
    for i in range(1, n):
        for j in range(1, n):
            if lst[i - 1][j - 1] + lst[i - 1][j] + lst[i][j - 1] + lst[i][j] > 1:
                sys.exit(print("\nThere are neighbors as 1! (solution two)"))
                
    print(result)

solution2()