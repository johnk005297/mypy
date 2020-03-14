class t:
    def __init__(self, a, b):        
        self.x = a
        self.y = b

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
                return self.x + self.y
        except Exception as err:
            print("There is an error: {}".format(err))

if __name__ == "__main__":
    c = t(7,55)
    
    print(c.summingUp())
    
    
    
    
