import sys

from crossword import *
from operator import itemgetter
import copy


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        for variable in self.crossword.variables:
            for word in copy.deepcopy(self.domains[variable]):
                if len(word) != variable.length:
                    self.domains[variable].remove(word)

        return

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        revised = False
        overlap = self.crossword.overlaps[x, y]

        for wordX in copy.deepcopy(self.domains[x]):

            satisfied = 0
            for wordY in self.domains[y]:
                if wordX[overlap[0]] == wordY[overlap[1]]:
                    satisfied += 1

            if satisfied == 0:
                self.domains[x].remove(wordX)
                revised = True

        return revised

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """

        if arcs == None:
            arcs = list()
            for x in self.domains:
                for y in self.crossword.neighbors(x):
                    if (x, y) not in arcs or (y, x) not in arcs:
                        arc = (x, y)
                        arcs.append(arc)

        i = 0

        while i < len(arcs):
            arc = arcs[i]
            x = arc[0]
            y = arc[1]
            if self.revise(x, y):
                if len(self.domains[x]) == 0:
                    return False
                for z in self.crossword.neighbors(x):
                    if z != y and (x, z) not in arcs or (z, x) not in arcs:
                        arcs.append(x, z)
            i += 1

        return True

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        for var in self.domains:
            if var not in assignment:
                return False
        
        return True

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """

        if assignment == None:
            return False

        for var_a in assignment:

            for var_b in assignment:
                # Check for repeated words
                if assignment[var_a] == assignment[var_b] and var_a != var_b:
                    return False
            
                # Check for correct word overlap
                if var_b in self.crossword.neighbors(var_a):
                    overlap = self.crossword.overlaps[var_a, var_b]
                    word_a = assignment[var_a]
                    word_b = assignment[var_b]
                    if word_a[overlap[0]] != word_b[overlap[1]]:
                        return False

            # Check for correct length
            if len(assignment[var_a]) != var_a.length:
                return False

        return True

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """

        tuples = list()

        for word in self.domains[var]:
            n = 0

            for neighbor in self.crossword.neighbors(var):
                if neighbor not in assignment:
                    overlap = self.crossword.overlaps[var, neighbor]
                    for neighbor_word in self.domains[neighbor]:
                        if word[overlap[0]] != neighbor_word[overlap[1]]:
                            n += 1

            tuples.append((word, n))

        sorted(tuples, key=itemgetter(1))

        return [value[0] for value in tuples]

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """

        unassigned = list()

        for variable in self.domains:
            if variable not in assignment:
                unassigned.append((variable, len(self.domains[variable]), len(self.crossword.neighbors(variable))))

        sorted(unassigned, key=itemgetter(1))

        minimum_heuristic = [unassigned[0]]

        for tuple in unassigned:
            if tuple[1] == minimum_heuristic[0][1] and tuple != minimum_heuristic[0]:
                minimum_heuristic.append(tuple)
        
        sorted(minimum_heuristic, key=itemgetter(2))

        return minimum_heuristic[-1][0]

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """

        complete = True

        for var in self.domains:
            if var not in assignment:
                complete = False
        
        if complete:
            return assignment
        
        variable = self.select_unassigned_variable(assignment)
        for value in self.order_domain_values(variable, assignment):
            temp_assignment = copy.deepcopy(assignment)
            temp_assignment[variable] = value
            if self.consistent(temp_assignment):
                assignment[variable] = value
                result = self.backtrack(assignment)
                if self.consistent(result):
                    return result
                else:
                    del assignment[variable]
                    
        return None


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
