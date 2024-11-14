from bauhaus import Encoding, proposition, constraint
from nnf import Var

from example import example2

CELLS = []
ENDPOINTS = []
CONNECTIONS = []

e = Encoding()

def gridTranslate(grid):
    mydict = {}
    colors = set()  # <-- Add a set to collect unique colors
    for row in grid:
        for cell in row:
            if len(cell) == 3:
                color = cell[2]
                colors.add(color)  # <-- Add color to the set
                if color in mydict:
                    ENDPOINTS.append(endpoint(mydict[color], e_cell(cell[0], cell[1]), color))
                else:
                    mydict[color] = e_cell(cell[0], cell[1])
            CELLS.append(e_cell(cell[0], cell[1]))
    return colors  # <-- Return the set of colors

@proposition(e)
class endpoint(object):
    def __init__(self, cell_1, cell_2, color) -> None:
        self.cell_1 = cell_1
        self.cell_2 = cell_2
        self.color = color

    def _prop_name(self):
         return f"{self.color}: {self.cell_1} -> {self.cell_2}"

@proposition(e)
class e_cell(object):
    def __init__(self, x, y) -> None:
        self.x = x
        self.y = y

    def _prop_name(self):
         return f"{self.x , self.y}"

@proposition(e)  # <-- Add a new proposition class for CellColor
class CellColor(object):
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color

    def __repr__(self):
        return f"Cell({self.x}, {self.y}) is {self.color}"
    def _prop_name(self):  # <-- Define _prop_name method
        return f"CellColor({self.x}, {self.y}, {self.color})"

def add_paths_cannot_cross_constraint():
    colors = set(endpoint.color for endpoint in ENDPOINTS)  # <-- Collect all colors from ENDPOINTS
    for cell in CELLS:
        vars = [CellColor(cell.x, cell.y, color) for color in colors]  # <-- Create CellColor variables
        constraint.add_exactly_one(e, *vars)  # <-- Exactly one color per cell
        

def connections(e_cell_instance):
    x = e_cell_instance.x
    y = e_cell_instance.y

    neighbors = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
    
    for nx, ny in neighbors:
        for cell in CELLS:
            if cell.x == nx and cell.y == ny:
                CONNECTIONS.append(f"{(x, y)} -> {(nx, ny)}")
                break  
    

gridTranslate(example2)
for cell in CELLS: 
     connections(cell)

print(CELLS)
print("----------------------------")
print(ENDPOINTS)
print("----------------------------")
connections(e_cell(1,2))
print(CONNECTIONS)