import copy


'''
NOTE: This function is taken straight from
https://stackoverflow.com/questions/45471152/how-to-create-a-sudoku-puzzle-in-python
This was not part of the scope that I wanted to practise but I still wanted to generate a new puzzle every time to 
reduce risk of having bugs.
'''
def createBoard(base):
    side = base * base

    # pattern for a baseline valid solution
    def pattern(r, c): return (base * (r % base) + r // base + c) % side

    # randomize rows, columns and numbers (of valid base pattern)
    from random import sample
    def shuffle(s): return sample(s, len(s))

    rBase = range(base)
    # g is 0,1,2 randomised order --> g*base = 0,3,6 randomized order + 0,1,2 randomized order
    rows = [g * base + r for g in shuffle(rBase) for r in shuffle(rBase)]
    cols = [g * base + c for g in shuffle(rBase) for c in shuffle(rBase)]
    nums = shuffle(range(1, base * base + 1))

    # produce board using randomized baseline pattern
    board = [[nums[pattern(r, c)] for c in cols] for r in rows]

    squares = side * side
    empties = squares * 3 // 4
    for p in sample(range(squares), empties):
        board[p // side][p % side] = 0
    return board


def test(colIndex, rowIndex, num, board):
    if num in board[rowIndex]:
        return False
    if num in [row[colIndex] for row in board]:
        return False
    # Find left corner in current square
    squareRowStart = rowIndex - rowIndex % 3
    squareColStart = colIndex - colIndex % 3
    # Loop from left corner of current square to left corner+3 using slicing
    for row in board[squareRowStart:squareRowStart + 3]:
        if num in row[squareColStart:squareColStart + 3]:
            return False
    return True


def findEmptySpace(board):
    for rowIndex, row in enumerate(board):
        for colIndex, colValue in enumerate(row):
            if board[rowIndex][colIndex] == 0:
                return [rowIndex, colIndex]
    return [-1, -1]


# The solver function, using recursion and backtracking
def solve(board):
    emptyCoordinates = findEmptySpace(board)
    # if no more empty coordinates we are done
    if emptyCoordinates == [-1, -1]:
        return True
    rowIndex, colIndex = emptyCoordinates[0], emptyCoordinates[1]
    for num in range(1, 10):
        if test(colIndex, rowIndex, num, board):
            board[rowIndex][colIndex] = num
            '''Try to solve the board recursively with our new cells, when the next one could not find a number 
            (returned False) we try with the next number in the loop. If none of the numbers led to a solution we set
             the index to 0 and return False to trigger the backtracking'''
            if solve(board):
                return True
    board[rowIndex][colIndex] = 0
    return False


def getSolvedBoard(_board):
    # So both boards in UI doesn't get solved when we call this function
    board = copy.deepcopy(_board)
    solve(board)
    return board
