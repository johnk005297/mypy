#   git commit <file_name> -m "<Message text>"


def fact(x):
    tot = 1
    while x > 0:
        tot *= x
        x -= 1
    return tot

def fact_rec(x):
    if x > 0:         
        if x == 1:
            print(f"I'm here!!!!  X is: {x}")
            return 1
        else:            
            new_var = fact_rec(x-1)
            print(f"I'm here!!!!  X is: {x}, and new_var is {new_var}")
            return new_var*x
    else:
        return "It's negative"

# print(fact_rec(2))

def factorial_2(x):
    if x == 1:
        return 1
    else:
        # print(f"I'm here!! X is {x}")
        return x * factorial_2(x - 1)

# print(factorial_2(5))


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
    A_sorted = [1, 2, 5, 8, 23, 58, 74, 99, 334, 9867]
    print("testcase #1: ",end='')    
    sort_algorithm(A)
    print('OK' if A == A_sorted else 'FAIL')
    


if __name__ == "__main__":
    test_sort(insert_sort)
    test_sort(choice_sort)
    test_sort(bubble_sort)
    
