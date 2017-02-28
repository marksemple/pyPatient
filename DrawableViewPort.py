# DrawableViewPort.py

# Third-parties
import pyqtgraph as pg

class DrawablePlotWidget(pg.PlotWidget):

    def __init__(self, fileList=None, *args, **kwargs):
        super().__init__(*args, **kwargs)


        # self.plotWidge.keyPressEvent = lambda x: self.PlotKeyPress(x)
        # self.plotWidge.keyReleaseEvent = lambda x: self.PlotKeyRelease(x)
