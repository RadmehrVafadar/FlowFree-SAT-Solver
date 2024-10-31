from bauhaus import Encoding, proposition, constraint, And, Or
from bauhaus.utils import count_solutions, likelihood
from nnf import config
config.sat_backend = "kissat"

@proposition(name='CellConnection')
class CellConnection:
    def __init__(self, x1=None, y1=None, x2=None, y2=None, color=None):
        # Initialize with default None values
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.color = color
    
    def __repr__(self):
        return f"{self.color}: ({self.x1},{self.y1}) -> ({self.x2},{self.y2})"

    def __hash__(self):
        return hash((self.x1, self.y1, self.x2, self.y2, self.color))

    def __eq__(self, other):
        if not isinstance(other, CellConnection):
            return False
        return (self.x1 == other.x1 and 
                self.y1 == other.y1 and 
                self.x2 == other.x2 and 
                self.y2 == other.y2 and 
                self.color == other.color)

class FlowFree:
    def __init__(self, filename):
        self.E = Encoding()
        self.grid, self.colors, self.size = self._read_input(filename)
        self.connections = self._create_propositions()
    
    def _read_input(self, filename):
        grid = []
        colors = set()
        with open(filename) as f:
            for line in f:
                grid.append(list(line.strip()))
        
        for row in grid:
            for cell in row:
                if cell != '.':
                    colors.add(cell)
        
        return grid, colors, len(grid)
    
    def _create_propositions(self):
        connections = []
        # Create possible connections between adjacent cells
        for i in range(self.size):
            for j in range(self.size):
                # Horizontal connections
                if j < self.size - 1:
                    for color in self.colors:
                        conn = CellConnection()
                        conn.x1 = i
                        conn.y1 = j
                        conn.x2 = i
                        conn.y2 = j+1
                        conn.color = color
                        connections.append(conn)
                # Vertical connections
                if i < self.size - 1:
                    for color in self.colors:
                        conn = CellConnection()
                        conn.x1 = i
                        conn.y1 = j
                        conn.x2 = i+1
                        conn.y2 = j
                        conn.color = color
                        connections.append(conn)
        return connections

def encode(self):
    # 1. Each cell must be used exactly once
    for i in range(self.size):
        for j in range(self.size):
            self.E.add_constraint(ExactlyOne([conn for conn in self.connections 
                if (conn.x1 == i and conn.y1 == j) or (conn.x2 == i and conn.y2 == j)]))

    # 2. Each colored endpoint connects to one matching-color neighbor
    for i in range(self.size):
        for j in range(self.size):
            if self.grid[i][j] != '.':
                color = self.grid[i][j]
                self.E.add_constraint(ExactlyOne([conn for conn in self.connections 
                    if conn.color == color and 
                    ((conn.x1 == i and conn.y1 == j) or (conn.x2 == i and conn.y2 == j))]))

    # 3. Intermediate cells connect to exactly two cells of same color
    for i in range(self.size):
        for j in range(self.size):
            if self.grid[i][j] == '.':
                for color in self.colors:
                    # For each color, either 0 or 2 connections
                    connected_cells = [conn for conn in self.connections 
                        if conn.color == color and 
                        ((conn.x1 == i and conn.y1 == j) or (conn.x2 == i and conn.y2 == j))]
                    self.E.add_constraint(Or(
                        And([Not(conn.active) for conn in connected_cells]),
                        ExactlyTwo(connected_cells)
                    ))

    # 4. Path continuity with color matching
    for conn in self.connections:
        color = conn.color
        # If connection is active, ensure continuation at both ends
        self.E.add_constraint(Implies(conn.active, And(
            Or([other.active for other in self.connections 
                if other != conn and other.color == color and
                ((other.x1 == conn.x2 and other.y1 == conn.y2) or 
                 (other.x2 == conn.x2 and other.y2 == conn.y2))]),
            Or([other.active for other in self.connections 
                if other != conn and other.color == color and
                ((other.x1 == conn.x1 and other.y1 == conn.y1) or 
                 (other.x2 == conn.x1 and other.y2 == conn.y1))])
        )))

    # 5. No shared cells between different colors
    for i in range(self.size):
        for j in range(self.size):
            for color1 in self.colors:
                for color2 in self.colors:
                    if color1 != color2:
                        conns1 = [conn for conn in self.connections 
                            if conn.color == color1 and 
                            ((conn.x1 == i and conn.y1 == j) or (conn.x2 == i and conn.y2 == j))]
                        conns2 = [conn for conn in self.connections 
                            if conn.color == color2 and 
                            ((conn.x1 == i and conn.y1 == j) or (conn.x2 == i and conn.y2 == j))]
                        for c1 in conns1:
                            for c2 in conns2:
                                self.E.add_constraint(Not(And(c1.active, c2.active)))

def solve(self):
    theory = self.encode()
    solution = theory.solve()
    if solution:
        active_conns = [conn for conn in self.connections if solution[conn]]
        return self._format_solution(active_conns)
    return None

def _format_solution(self, active_connections):
    paths = {}
    for conn in active_connections:
        if conn.color not in paths:
            paths[conn.color] = []
        paths[conn.color].append((conn.x1, conn.y1, conn.x2, conn.y2))
    return paths