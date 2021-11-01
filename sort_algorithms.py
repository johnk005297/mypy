                                ###### SOME ALGORITHMS #######



def factorial(x:int):
    tot = 1
    while x > 0:
        tot *= x
        x -= 1
    return tot


                                ####### Recursion examples #######

def pow(a:float, n:int):
    if n == 0:
        return 1
    elif n%2 == 1: # if n is odd
        return pow(a, n-1) * a
    else: # if n is even
        return pow(a**2, n//2)


def gcd(a:int, b:int):
    if b == 0:
        return a
    return gcd(b, a%b)


def factorial_rec(x):
    if x > 0:         
        if x == 1:            
            return 1
        else:            
            f = factorial_rec(x-1)
            return f*x
    else:
        return "Number should be greater than zero!"



################################################################################################


                                ####### SORT algorithms #######

def insert_sort(A):
    """ Insert sort"""  
    for top in range(1, len(A)):        
        while top > 0 and A[top-1] > A[top]:            
            A[top], A[top-1] = A[top-1], A[top]            
            top -= 1
    return A


def choice_sort(A):
    """ Choice sort"""    
    for pos in range(0, len(A)-1):
        for k in range(pos+1, len(A)):
            if A[k] < A[pos]:
                A[k], A[pos] = A[pos], A[k]
    return A


def bubble_sort(A):
    """ Bubble sort"""
    for bypass in range(1, len(A)):
        for k in range(0, len(A)-bypass):
            if A[k] > A[k+1]:
                A[k], A[k+1] = A[k+1], A[k]
    return A


def test_sort(sort_algorithm):
    print(f"Testing: {sort_algorithm.__doc__}")    
    A = [8,2,5,334,99,1,9867,23,74,58]  
    print(f"Was: {A}")
    A_sorted = [1, 2, 5, 8, 23, 58, 74, 99, 334, 9867]    
    print("testcase #1: ",end='')    
    sort_algorithm(A)
    print('OK' if A == A_sorted else 'FAIL')    
    print(f"Now: {A_sorted}\n")

####################################################################################################################


                                ####### Finding matches in array. #######
def KMP():
    """
        Knut-Morris-Pratt algorithm. Finding matches in array. 
    """    
    str_to_find = "lolo"    
    source = "sdsdfsdfsdflolo" 
    """ 1. Need to construct "pi" array.
       By default: pi[0] = 0; j = 0; i = 1;
    """
    pi = [0]*len(str_to_find)
    j = 0
    i = 1
    while i < len(str_to_find):
        if str_to_find[j] == str_to_find[i]:
            pi[i] = j + 1
            i += 1
            j += 1
        else:
            if j == 0:
                pi[i] = 0
                i += 1
            else:
                j = pi[j-1]
    
    
    """
        2. Main KMP algorithm itself.
    """    
    i = 0
    j = 0

    while i < len(source):
        if source[i] == str_to_find[j]:
            i += 1
            j += 1
            if j == len(str_to_find):
                print("Match is found!")
                break
        else:
            if j > 0:
                j = pi[j-1]
            else:
                i += 1
    
    if i == len(source) and j != len(str_to_find):
        print("No matches.")

##################################################################################################################################


if __name__ == "__main__":
    # test_sort(insert_sort)
    # test_sort(choice_sort)
    # test_sort(bubble_sort)
    KMP()
    # print(gcd(224,42))
    # print(pow(3,4))

