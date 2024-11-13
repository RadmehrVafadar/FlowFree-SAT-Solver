from bauhaus import Encoding, proposition, constraint
from nnf import Var
from typing import List, Tuple

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

    def __repr__(self):
        return f"{self.color}: {self.cell_1} -> {self.cell_2}"

@proposition(e)
class e_cell(object):
    def __init__(self, x, y) -> None:
        self.x = x
        self.y = y

    def __repr__(self):
        return f"Cell({self.x}, {self.y})"

@proposition(e)  # <-- Add a new proposition class for CellColor
class CellColor(object):
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color

    def __repr__(self):
        return f"Cell({self.x}, {self.y}) is {self.color}"

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


@proposition(e)
class colored_cell(object):
    # Represents a cell having a specific color
    def __init__(self, cell: e_cell, color: str) -> None:
        self.cell = cell
        self.color = color
    
    def __repr__(self):
        return f"ColoredCell({self.cell}, {self.color})"

@proposition(e)
class path_exists(object):
    # Represents that there exists a path from one cell to another
    def __init__(self, from_cell: tuple, to_cell: tuple, color: str) -> None:
        self.from_cell = from_cell
        self.to_cell = to_cell
        self.color = color
    
    def __repr__(self):
        return f"Path({self.from_cell}->{self.to_cell}, {self.color})"

def build_comes_from_somewhere_constraint():
    # For each cell
    for cell in CELLS:
        cell_coord = (cell.x, cell.y)
        
        # Get neighbors for this cell
        connections(cell)
        
        # For each endpoint color
        for endpoint in ENDPOINTS:
            # Skip if this cell is an endpoint
            if any(ep for ep in ENDPOINTS if 
                  (ep.color == endpoint.color and 
                   ((ep.cell_1.x == cell.x and ep.cell_1.y == cell.y) or 
                    (ep.cell_2.x == cell.x and ep.cell_2.y == cell.y)))):
                continue
            
            # Create path propositions for this cell to its neighbors
            neighbor_paths = []
            for connection in CONNECTIONS:
                from_cell, to_cell = connection.split(" -> ")
                from_cell = eval(from_cell)  # converts string "(x,y)" to tuple
                to_cell = eval(to_cell)
                neighbor_paths.append(path_exists(from_cell, to_cell, endpoint.color))
            
            # If this cell has this color, then at least one path must exist to a neighbor with the same color
            colored_cell_prop = colored_cell(cell, endpoint.color)
            constraint.add_implies_at_least_one(e, colored_cell_prop, neighbor_paths)



print(CELLS)
print("----------------------------")
print(ENDPOINTS)
print("----------------------------")
connections(e_cell(1,2))
print(CONNECTIONS)
