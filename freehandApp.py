#!/usr/bin/env python


'''
Qt app demonstrating freehand drawing tool
'''     

from PySide.QtCore import *
from PySide.QtGui import *
import sys

from freehand import FreehandTool

class DiagramScene(QGraphicsScene):
    def __init__(self, *args):
        QGraphicsScene.__init__(self, *args)
        self.addItem(QGraphicsTextItem("Freehand drawing with pointer"))
        
class GraphicsView(QGraphicsView):
  def __init__(self, parent=None):
      super(GraphicsView, self).__init__(parent)
      
      assert self.dragMode() is QGraphicsView.NoDrag
      
      self.setRenderHint(QPainter.Antialiasing)
      self.setRenderHint(QPainter.TextAntialiasing)

      self.setMouseTracking(True);  # Enable mouseMoveEvent
      self.freehandTool = FreehandTool(self.scene(), self)


  ''' Delegate events to FreehandTool. '''
  def mouseMoveEvent(self, event):
    # print "GV mouse moved"
    self.freehandTool.pointerMoveEvent(event)
  
  def mousePressEvent(self, event):
    # print "GV mouse pressed"
    self.freehandTool.pointerPressEvent(event)
    
  def mouseReleaseEvent(self, event):
    self.freehandTool.pointerReleaseEvent(event)
    
    

class MainWindow(QMainWindow):
    def __init__(self, *args):
        QMainWindow.__init__(self, *args)
        self.scene = DiagramScene()
        self.view = GraphicsView(self.scene)
        rect =QRect(-500, -500, 500, 500)
        self.view.fitInView(rect)
        self.view.setSceneRect(rect)
        self.setCentralWidget(self.view)

        
def main(args):
    app = QApplication(args)
    mainWindow = MainWindow()
    mainWindow.setGeometry(100, 100, 500, 500)
    mainWindow.show()

    sys.exit(app.exec_()) # Qt Main loop


if __name__ == "__main__":
    main(sys.argv)
