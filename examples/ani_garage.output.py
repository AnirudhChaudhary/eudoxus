class Garage(Module):
  def locals(self):
    self.num_cars = int

  def inputs(self):
    self.enter_car = bool
    self.leave_car = bool

  def init(self):
    self.num_cars = 0

  def next(self):
    if self.enter_car:
      self.num_cars = (self.num_cars + 1)
    if self.leave_car:
      self.num_cars = (self.num_cars - 1)

  def specification(self):
    return G((self.num_cars >= 0))