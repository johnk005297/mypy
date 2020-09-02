class myMath:
    def __init__(self):                      
        self.a = 155
        self.b = 962    
        self.d = "Description of the instance"

    def summingUp(self, x, y):
        
        try:
            if x == y:
                return "They are even: {} = {}".format(x, y)

            else:
                return "The result off summing: {}".format(x + y)
        except Exception as err:
            print("There is an error!")
            print("Type: ", type(err))
            print(err)
        
    # def __str__(self):
    #     return "\nYour object are: {0}({1}) and {2}({3}) \n{4}".format(self.x,type(self.x), self.y, type(self.y), self.d)
    # def __str__(self):
    #     return "{}. {} {} ".format(self.d, self.a, self.b)
        

if __name__ == "__main__":
       
    c = myMath()    
    print(c)    
    print(c.summingUp(27.60,13.74))
    print(myMath.summingUp(c,5,7))

    
    
    
    
    
    
