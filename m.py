class tclass:
    def __init__(self):        
        self.x = int(input("enter first num: "))
        self.y = int(input("enter sec num: "))

    def __str__(self):
        return "{} and {}".format(self.x, self.y)

    def summingUp(self):
        try:
            # if isinstance(self.x or self.y, (int, float)):
            #     print("The obj is a number!")
            # elif isinstance(self.x or self.y, str):
            #     print("The obj is a string")
            # else:
            #     raise TypeError("Not a number: {} or {}".format(type(self.x), type(self.y)))

            if self.x == self.y:
                return "They are even"
            else:
                return print("The result off summing: {}".format(self.x + self.y))
        except Exception as err:
            print("There is an error: {}".format(err))

if __name__ == "__main__":

    c = tclass()    
    print(c.summingUp())
    
    
    
    
