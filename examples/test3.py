class Descriptor(object):

    def __init__(self, name=''):
        self.name = name
        self.t = 5

    def __get__(self, obj, objtype):
        return "{}for{}".format(self.name, self.name)

    def __set__(self, obj, name):
        if isinstance(name, str):
            self.name = name
        else:
            raise TypeError("Name should be string")


class GFG(object):
    name = Descriptor()


g = GFG()
g.name = "Geeks"
print(g.name)
