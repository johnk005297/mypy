class myMath:
    def __init__(self):
        try:                
            self.x = float(input("enter first num: "))
            self.y = float(input("enter sec num: "))
        except Exception as err:
            print("Not float, error: {}".format(err))            
            raise

    

    def summingUp(self):
               
        if self.x == self.y:
            return "They are even: {} = {}".format(self.x, self.y)

        else:
            return "The result off summing: {}".format(self.x + self.y)
        # else:
        #     raise TypeError("Not a number: {} or {}".format(type(self.x), type(self.y)))
        
    def __str__(self):
        return "\nYour numbers are: {} and {}".format(self.x, self.y)

if __name__ == "__main__":

    c = myMath()    
    print(c)
    print(c.summingUp())
    
    
    
    
    
