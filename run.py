from bauhaus import Encoding, proposition, constraint, And, Or
from nnf import config
config.sat_backend = "kissat"

# Encoding
E = Encoding()

# Board dimensions
ROWS = 3
COLS = 3

# Colors and initial positions for paths
COLORS = ["red", "blue"]
INITIAL_POSITIONS = {
    "red": [(1, 1), (1, 3)],  # Start and end points for red
    "blue": [(2, 1), (3, 3)]  # Start and end points for blue
}

# All cells on the board
CELLS = [f"c{r}{c}" for r in range(1, ROWS + 1) for c in range(1, COLS + 1)]


def get_adjacent_cells(row, col):
    """Return valid neighbors of a cell."""
    neighbors = []
    if row > 1: neighbors.append(f"c{row - 1}{col}")  # Up
    if row < ROWS: neighbors.append(f"c{row + 1}{col}")  # Down
    if col > 1: neighbors.append(f"c{row}{col - 1}")  # Left
    if col < COLS: neighbors.append(f"c{row}{col + 1}")  # Right
    return neighbors


# Propositions
@proposition(E)
class Path(object):
    """Cell is part of a path of a given color."""
    def __init__(self, color, cell):
        assert color in COLORS, f"Invalid color: {color}"
        assert cell in CELLS, f"Invalid cell: {cell}"
        self.color = color
        self.cell = cell

    def _prop_name(self):
        return f"Path({self.color}, {self.cell})"


@proposition(E)
class Connection(object):
    """Connection between two cells for a specific color."""
    def __init__(self, color, cell1, cell2):
        assert color in COLORS, f"Invalid color: {color}"
        assert cell1 in CELLS and cell2 in CELLS, f"Invalid cells: {cell1}, {cell2}"
        self.color = color
        self.cell1 = cell1
        self.cell2 = cell2

    def _prop_name(self):
        return f"Connection({self.color}, {self.cell1}, {self.cell2})"


# Constraints
def add_path_constraints():
    """Ensure valid paths for all colors."""
    for color in COLORS:
        start, end = INITIAL_POSITIONS[color]
        start_cell = f"c{start[0]}{start[1]}"
        end_cell = f"c{end[0]}{end[1]}"

        # Start and end cells must connect to exactly one neighbor
        start_neighbors = [Connection(color, start_cell, n) for n in get_adjacent_cells(*start)]
        end_neighbors = [Connection(color, end_cell, n) for n in get_adjacent_cells(*end)]

        constraint.add_exactly_one(E, *start_neighbors)
        constraint.add_exactly_one(E, *end_neighbors)

def add_continuity_constraints():
    """Ensure path continuity (2 neighbors for path cells, 1 for endpoints)."""
    for color in COLORS:
        for cell in CELLS:
            row, col = int(cell[1]), int(cell[2])
            neighbors = get_adjacent_cells(row, col)
            connections = [Connection(color, cell, neighbor) for neighbor in neighbors]
            
            # Check if this is an endpoint
            is_endpoint = cell in [f"c{pos[0]}{pos[1]}" for pos in INITIAL_POSITIONS[color]]
            
            if is_endpoint:
                continue  # Skip endpoints as they're handled in add_path_constraints
            
            # For cells that are part of this color's path, they must have exactly two connections
            # We'll use a combination of at_least_one and at_most_one constraints
            # to ensure exactly two connections
            
            # If cell is part of path, must have at least two connections
            pairs = []
            for i in range(len(connections)):
                for j in range(i+1, len(connections)):
                    pairs.append(And(connections[i], connections[j]))
            
            E.add_constraint(Path(color, cell) >> Or(pairs))
            
            # Cannot have more than two connections
            if len(connections) >= 3:
                for i in range(len(connections)):
                    for j in range(i+1, len(connections)):
                        for k in range(j+1, len(connections)):
                            E.add_constraint(~(connections[i] & connections[j] & connections[k]))
            
            # A cell with any connection must be part of the path
            for neighbor in neighbors:
                E.add_constraint(Connection(color, cell, neighbor) >> Path(color, cell))

def add_connection_constraints():
    """Ensure valid connections between neighboring cells."""
    for color in COLORS:
        for cell in CELLS:
            row, col = int(cell[1]), int(cell[2])
            neighbors = get_adjacent_cells(row, col)

            # If a cell is part of a path, it must connect to at least one neighbor
            E.add_constraint(Path(color, cell) >> Or([Connection(color, cell, neighbor) for neighbor in neighbors]))
            # Connection implies both cells are part of the path
            for neighbor in neighbors:
                E.add_constraint(Connection(color, cell, neighbor) >> (Path(color, cell) & Path(color, neighbor)))

def add_exclusivity_constraints():
    """Ensure cells belong to at most one path."""
    for cell in CELLS:
        path_membership = [Path(color, cell) for color in COLORS]
        constraint.add_at_most_one(E, *path_membership)


# This method is considerd redundant.
def add_bidirectional_constraints():
    """Ensure connections are symmetric."""
    for color in COLORS:
        for cell1 in CELLS:
            for cell2 in get_adjacent_cells(int(cell1[1]), int(cell1[2])):
                E.add_constraint(
                    Connection(color, cell1, cell2) >> Connection(color, cell2, cell1)
                )
                E.add_constraint(
                    Connection(color, cell2, cell1) >> Connection(color, cell1, cell2)
                )

def add_completeness_constraints():
    """Ensure every cell is part of some path."""
    for cell in CELLS:
        path_membership = [Path(color, cell) for color in COLORS]
        constraint.add_exactly_one(E, *path_membership)

# Visualization Method
def visualize_solution(solution):
    """Print the board with colored paths."""
    for row in range(1, ROWS + 1):
        line = ""
        for col in range(1, COLS + 1):
            cell = f"c{row}{col}"
            cell_char = "."
            connections = []
            
            # Find which color this cell belongs to
            for color in COLORS:
                if solution[Path(color, cell)]:
                    cell_char = color[0].upper()
                    # Check if it's an endpoint
                    if any(pos[0] == row and pos[1] == col for pos in INITIAL_POSITIONS[color]):
                        cell_char = f"({cell_char})"
            line += f"{cell_char:3}"
        print(line)



# Main Encoding
def flow_free_theory():
    add_path_constraints()
    add_connection_constraints()
    add_continuity_constraints()
    add_exclusivity_constraints()
    add_bidirectional_constraints()
    add_completeness_constraints()
    
    return E

# Solve the problem
if __name__ == "__main__":
    T = flow_free_theory().compile()
    solution = T.solve()
    if solution:
        print("Solution found:")
        visualize_solution(solution)
    else:
        print("No solution!")