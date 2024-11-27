from bauhaus import Encoding, proposition, constraint, And, Or
from bauhaus.utils import likelihood

# SAT Solver configuration
from nnf import config
config.sat_backend = "kissat"

# Encoding that will store all constraints
E = Encoding()

# Board dimensions
ROWS = 5
COLS = 5

# Colors and initial positions for paths
COLORS = ["red", "blue", "green"]
INITIAL_POSITIONS = {
    "red": [(1, 1), (5, 5)],   # Starting and ending positions for red path
    "blue": [(1, 5), (5, 1)],  # Starting and ending positions for blue path
    "green": [(3, 1), (3, 5)]  # Starting and ending positions for green path
}

# Create all cell identifiers
CELLS = [f"c{r}{c}" for r in range(1, ROWS + 1) for c in range(1, COLS + 1)]


# Helper to get adjacent cells for a given cell
def get_adjacent_cells(row, col):
    neighbors = []
    if row > 1: neighbors.append(f"c{row - 1}{col}")  # Up
    if row < ROWS: neighbors.append(f"c{row + 1}{col}")  # Down
    if col > 1: neighbors.append(f"c{row}{col - 1}")  # Left
    if col < COLS: neighbors.append(f"c{row}{col + 1}")  # Right
    return neighbors


# Propositions

@proposition(E)
class Path(object):
    """Indicates that a cell belongs to a path of a given color."""
    def __init__(self, color, cell):
        assert cell in CELLS, f"Invalid cell: {cell}"
        assert color in COLORS, f"Invalid color: {color}"
        self.color = color
        self.cell = cell

    def _prop_name(self):
        return f"Path({self.color}, {self.cell})"

@proposition(E)
class Connection(object):
    """Indicates a connection between two adjacent cells for a given color."""
    def __init__(self, color, cell1, cell2):
        assert cell1 in CELLS, f"Invalid cell: {cell1}"
        assert cell2 in CELLS, f"Invalid cell: {cell2}"
        assert color in COLORS, f"Invalid color: {color}"
        self.color = color
        self.cell1 = cell1
        self.cell2 = cell2

    def _prop_name(self):
        return f"Connection({self.color}, {self.cell1}, {self.cell2})"


# Constraints

def add_path_constraints():
    """Ensure valid paths are formed for each color."""
    for color in COLORS:
        # Each path starts and ends at its defined points
        start, end = INITIAL_POSITIONS[color]
        start_cell = f"c{start[0]}{start[1]}"
        end_cell = f"c{end[0]}{end[1]}"
        E.add_constraint(Path(color, start_cell))
        E.add_constraint(Path(color, end_cell))

        # Ensure all other cells on the board either belong to the path or not
        for cell in CELLS:
            E.add_constraint(Or(Path(color, cell), ~Path(color, cell)))

def add_adjacency_constraints():
    """Ensure paths are continuous and connected between adjacent cells."""
    for color in COLORS:
        for cell in CELLS:
            row, col = int(cell[1]), int(cell[2])
            neighbors = get_adjacent_cells(row, col)
            # If a cell belongs to a path, it must connect to at least one neighbor
            E.add_constraint(Path(color, cell) >> Or([Connection(color, cell, neighbor) for neighbor in neighbors]))
            # Ensure the connection implies both cells are part of the path
            for neighbor in neighbors:
                E.add_constraint(Connection(color, cell, neighbor) >> (Path(color, cell) & Path(color, neighbor)))

def add_reachability_constraints():
    """Ensure paths form a continuous connection from start to end points."""
    for color in COLORS:
        start, end = INITIAL_POSITIONS[color]
        start_cell = f"c{start[0]}{start[1]}"
        end_cell = f"c{end[0]}{end[1]}"

        # Use reachability to ensure a continuous connection
        @proposition(E)
        class Reachable(object):
            def __init__(self, cell, steps):
                self.cell = cell
                self.steps = steps

            def _prop_name(self):
                return f"Reachable({self.cell}, {self.steps})"

        E.add_constraint(Reachable(start_cell, 0))
        for step in range(1, ROWS * COLS):
            for cell in CELLS:
                row, col = int(cell[1]), int(cell[2])
                neighbors = get_adjacent_cells(row, col)
                reachable_prev = [Reachable(neighbor, step - 1) & Connection(color, neighbor, cell) for neighbor in neighbors]
                E.add_constraint(Reachable(cell, step) >> Or(reachable_prev))
                if cell == end_cell:
                    E.add_constraint(Reachable(cell, step))  # Enforce reachability at some step


def add_exclusivity_constraints():
    """Ensure each cell belongs to at most one path."""
    for cell in CELLS:
        path_membership = [Path(color, cell) for color in COLORS]
        constraint.add_at_most_one(E, path_membership)


# Main Encoding

def flow_free_theory():
    add_path_constraints()
    add_adjacency_constraints()
    add_reachability_constraints()
    add_exclusivity_constraints()
    return E


# Solve the Theory

if __name__ == "__main__":
    T = flow_free_theory().compile()
    solution = T.solve()
    if solution:
        print("Solution found:")
        for cell in CELLS:
            for color in COLORS:
                if solution[Path(color, cell)]:
                    print(f"{cell}: {color}")
    else:
        print("No solution!")
