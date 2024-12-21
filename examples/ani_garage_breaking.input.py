class Garage(Module):
    def locals(self):
        self.num_cars = Integer()

    def init(self):
        self.num_cars = 0
    
    def next(self):
        if enter_car:
            self.num_cars = self.num_cars + 1
        if leave_car:
            self.num_cars = self.num_cars - 1
    
    def inputs(self):
        self.enter_car = Boolean()
        self.leave_car = Globally(self.num_cars >= 0)
    
    def specification(self):
        return (Globally(self.num_cars >= 0) and Globally(self.num_cars >= 1))

