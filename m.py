class myMath:
    def __init__(self):                      
        self.a = 155
        self.b = 962    
        self.d = "Description of the instance"

    def summingUp(self):
        
        try:
            if self.a == self.b:
                return "They are even: {} = {}".format(self.a, self.b)

            else:
                return "The result off summing: {}".format(self.a + self.b)
        except Exception as err:
            print("There is an error!")
            print("Type: ", type(err))
            print(err)
        
    # def __str__(self):
    #     return "\nYour object are: {0}({1}) and {2}({3}) \n{4}".format(self.x,type(self.x), self.y, type(self.y), self.d)
    # def __str__(self):
    #     return "{}. {} {} ".format(self.d, self.a, self.b)
        

#   git commit <file_name> -m "<Message text>"
if __name__ == "__main__":
       
    c = myMath()        
    print(c.summingUp())
    # print(myMath.summingUp(myMath()))
    print(myMath().summingUp())
    print('Smth for commit')

#   Need to get back real quick to classes!
    
    
    
    
    
