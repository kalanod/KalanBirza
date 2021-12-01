class Stock_d:
    def __init__(self, id, price):
        self.id = id
        self.price = price

    def __str__(self):
        return  (f"stock id={self.id} price={self.price}")