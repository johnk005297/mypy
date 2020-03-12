class t:
    def __init__(self, a, b):        
        self.x = a
        self.y = b
           
    def some_func(self):
        if self.x == self.y:
            return "They are even"
        else:
            return self.x + self.y

if __name__ == "__main__":
    c = t(5,578)
    c2 = t(33, 22)
    print(c.some_func())
    print()