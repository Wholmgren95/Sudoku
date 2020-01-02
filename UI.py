from PyQt5.QtWidgets import QMessageBox, QApplication, QWidget, QGridLayout, QPushButton, QToolButton, QSizePolicy
import sys
import Logic
from PyQt5.QtCore import *


class Button(QPushButton):
    def __init__(self, name):
        super().__init__()
        self.setText(name)
        self.setMinimumSize(182, 50)
        # Only want buttons to expand horizontally
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        self.setStyleSheet('background-color: rgb(200, 200, 200);''color: rgb(0, 0, 0);''font-size: 15pt;')

    def setTextColor(self, color):
        if color == "black":
            self.setStyleSheet('background-color: rgb(200, 200, 200);''color: rgb(0, 0, 0);''font-size: 15pt;')
        if color == "red":
            self.setStyleSheet('background-color: rgb(200, 200, 200);''color: rgb(220, 0, 0);''font-size: 15pt;')


class Cell(QToolButton):
    helpRequested = pyqtSignal()
    updateSignal = pyqtSignal()

    def __init__(self, coordinates, board, value=0):
        super().__init__()
        self.board = board
        self.boardSolved = False
        self.coordinates = coordinates
        self.rowIndex = coordinates[0]
        self.colIndex = coordinates[1]
        self.value = value
        self.setStyleSheet('background-color: rgb(200, 200, 200);''color: rgb(0, 0, 0);''font-size: 25pt;')
        self.setMinimumSize(60, 60)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.setCheckable(True)
        self.setFocusPolicy(Qt.ClickFocus)

    def setTextColor(self, color):
        if color == "black":
            self.setStyleSheet('background-color: rgb(200, 200, 200);''color: rgb(0, 0, 0);''font-size: 25pt;')
        if color == "blue":
            self.setStyleSheet('background-color: rgb(200, 200, 200);''color: rgb(0, 191, 255);''font-size: 25pt;')
        if color == "red":
            self.setStyleSheet('background-color: rgb(200, 200, 200);''color: rgb(220, 0, 0);''font-size: 25pt;')
        if color == "green":
            self.setStyleSheet('background-color: rgb(200, 200, 200);''color: rgb(0, 220, 0);''font-size: 25pt;')

    def getCoordinates(self):
        return self.coordinates

    def focusOutEvent(self, *args, **kwargs):
        self.setChecked(False)

    def setValue(self, val):
        self.value = int(val)
        if val == 0:
            self.setText("")
        else:
            self.setText(str(val))
        self.updateSignal.emit()

    def keyReleaseEvent(self, event):
        if Qt.Key_1 <= event.key() <= Qt.Key_9:
            # Turn color to normal if we previously entered invalid or a guess
            if self.value is not 0:
                self.setTextColor("black")
            self.setValue(event.text())
            # CTRL+KEY --> Blue, so user can make a "guess" and keep track of guesses and which one is known
            if event.modifiers() and Qt.CTRL:
                self.setTextColor("blue")
            # Not valid value --> Red
            if not Logic.test(self.colIndex, self.rowIndex, self.value, self.board):
                self.setTextColor("red")
            self.board[self.rowIndex][self.colIndex] = self.value
        elif event.key() == Qt.Key_Backspace or event.key() == Qt.Key_Delete:
            self.board[self.rowIndex][self.colIndex] = 0
            self.setTextColor("black")
            self.setValue(0)
        # Send signal to hint function in GameWindow
        elif event.key() == Qt.Key_H:
            if self.boardSolved:
                self.helpRequested.emit()
        # Clear focus so we can't enter numbers when cell not checked
        self.clearFocus()

    def boardSolvedSignal(self):
        self.boardSolved = True

    def setBoard(self, board):
        self.board = board


# Signals in own class since only QObject can use the connect method
class WorkerSignals(QObject):
    finished = pyqtSignal(list)
    finish = pyqtSignal()


# Created a worker class that the threadpool can use to solve board without the player having to wait for it
class Worker(QRunnable):
    def __init__(self, board):
        super(Worker, self).__init__()
        self.board = board
        self.signals = WorkerSignals()

    def run(self):
        solvedBoard = Logic.getSolvedBoard(self.board)
        self.signals.finished.emit(solvedBoard)
        self.signals.finish.emit()


class GameWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sudoku")
        self.board = Logic.createBoard(3)
        self.solvedBoard = self.board
        self.cells = []
        self.grid_layout = QGridLayout()
        self.solveButton = Button("Solve puzzle")
        # Will be used to solve board
        self.threadpool = QThreadPool()
        # Set disabled while board is not solved
        self.solveButton.setDisabled(True)
        self.solveButton.setTextColor("red")
        # Background color, color of lines
        self.setStyleSheet('background-color: rgb(49, 65.9, 65.9);')
        self.initUI()

    def initUI(self):
        self.grid_layout.setSpacing(4)
        worker = Worker(self.board)
        worker.signals.finished.connect(self.solveFinished)
        # The grid gets a subgrid for each square in board, subgrid has thinner space between --> thinner lines
        for rowIndex in range(3):
            for colIndex in range(3):
                inner_layout = QGridLayout()
                inner_layout.setSpacing(1)
                self.grid_layout.addLayout(inner_layout, rowIndex, colIndex)
        # Initialize all the cells and give them values
        for rowIndex in range(9):
            tmpCellList = []
            for colIndex in range(9):
                inner_layout = self.grid_layout.itemAtPosition(rowIndex // 3, colIndex // 3)
                cell = Cell((rowIndex, colIndex), self.board)
                cell.helpRequested.connect(self.hint)
                cell.updateSignal.connect(self.show)
                worker.signals.finish.connect(cell.boardSolvedSignal)
                # User can't edit the initial cells
                if self.board[rowIndex][colIndex] is not 0:
                    cell.setValue(self.board[rowIndex][colIndex])
                    cell.setDisabled(True)
                tmpCellList.append(cell)
                inner_layout.addWidget(cell, rowIndex % 3, colIndex % 3)
            self.cells.append(tmpCellList)
        # start after both signal has been connected
        self.threadpool.start(worker)
        newGameButton = Button("New game")
        newGameButton.clicked.connect(self.newGame)
        self.solveButton.clicked.connect(self.solvePuzzle)
        helpButton = Button("Information")
        helpButton.clicked.connect(self.help)
        self.grid_layout.addWidget(newGameButton)
        self.grid_layout.addWidget(self.solveButton)
        self.grid_layout.addWidget(helpButton)
        self.setLayout(self.grid_layout)

    def hint(self):
        coordinates = self.sender().getCoordinates()
        rowIndex, colIndex = coordinates[0], coordinates[1]
        # Sender is the object that called the function, in this case cell through the signal
        self.sender().setValue(self.solvedBoard[rowIndex][colIndex])
        self.sender().setTextColor("green")

    def solvePuzzle(self):
        for rowIndex in range(9):
            for colIndex in range(9):
                cell = self.cells[rowIndex][colIndex]
                cell.setTextColor("black")
                cell.setValue(self.solvedBoard[rowIndex][colIndex])

    def newGame(self):
        self.board = Logic.createBoard(3)
        worker = Worker(self.board)
        worker.signals.finished.connect(self.solveFinished)
        self.solveButton.setDisabled(True)
        self.solveButton.setTextColor("red")
        for rowIndex in range(9):
            for colIndex in range(9):
                cell = self.cells[rowIndex][colIndex]
                # Remove old cell values, connect to new worker signal
                cell.setBoard(self.board)
                worker.signals.finish.connect(cell.boardSolvedSignal)
                cell.boardSolved = False
                cell.setTextColor("black")
                cell.setValue(self.board[rowIndex][colIndex])
                if self.board[rowIndex][colIndex] is not 0:
                    cell.setDisabled(True)
                else:
                    cell.setDisabled(False)
        self.threadpool.start(worker)

    def help(self):
        helpBox = QMessageBox()
        helpBox.information(helpBox, "Information window", "Select a cell and press 'h' to get the correct number "
            "marked in green. NOTE: This will not work if the board has not been solved yet (when \"Solve puzzle\" is "
            "red).\n\nIf you are unsure about a cell you can press CTRL+NUMBER to get it in blue.\n\n"
            "Every new entry will be checked if valid and marked red if not.", QMessageBox.Ok, QMessageBox.Cancel)

    def solveFinished(self, solvedBoard):
        self.solvedBoard = solvedBoard
        self.solveButton.setDisabled(False)
        self.solveButton.setTextColor("black")


if __name__ == '__main__':
    app = QApplication([])
    game_window = GameWindow()
    game_window.show()
    game_window.help()
    sys.exit(app.exec_())
