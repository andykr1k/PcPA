from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMainWindow
import matplotlib.pyplot as plt

class MatplotlibWidget(QMainWindow):
    def __init__(self):
        super().__init__()

        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        central_widget = QWidget(self)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def showRewardPlot(self, x, y):
        self.ax.cla()
        self.ax.plot(x, y)
        self.ax.set_xlabel("Episode")
        self.ax.set_ylabel("Total Reward")
        self.ax.set_title("Total Reward per Episode")
        self.canvas.draw()
