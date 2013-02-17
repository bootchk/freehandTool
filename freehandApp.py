#!/usr/bin/env python


'''
Qt app demonstrating freehand drawing tool.

Copyright 2012 Lloyd Konneker

This is free software, covered by the GNU General Public License.
'''     

from PySide.QtCore import *
from PySide.QtGui import *
import sys

from freehand import FreehandTool
from ghostLine import PointerTrackGhost
from segmentString import SegmentString


class DiagramScene(QGraphicsScene):
  def __init__(self, *args):
    QGraphicsScene.__init__(self, *args)
    self.addItem(QGraphicsTextItem("Freehand drawing with pointer"))
    
    self.freehandTool = FreehandTool()


  ''' Delegate events to FreehandTool. '''
    
  def mouseMoveEvent(self, event):
    ''' Tell freehandTool to update its SegmentString. '''
    self.freehandTool.pointerMoveEvent(position=event.scenePos())
  
  
  def mousePressEvent(self, event):
    '''
    On mouse button down, create a new (infinitesmal) SegmentString and PointerTrackGhost.
    freehandTool remembers and updates SegmentString.
    '''
    freehandCurve = SegmentString()
    headGhost = PointerTrackGhost()
    self.addItem(freehandCurve)
    self.addItem(headGhost)
    self.freehandTool.setSegmentString(segmentString=freehandCurve, 
                                       pathHeadGhost=headGhost, 
                                       position=event.scenePos())
    self.freehandTool.pointerPressEvent(event.scenePos())

    
  def mouseReleaseEvent(self, event):
    self.freehandTool.pointerReleaseEvent(position=event.scenePos())
  
  
  def keyPressEvent(self, event):
    self.freehandTool.keyPressEvent(event)
    
    
    
class GraphicsView(QGraphicsView):
  def __init__(self, parent=None):
      super(GraphicsView, self).__init__(parent)
      
      assert self.dragMode() is QGraphicsView.NoDrag
      self.setRenderHint(QPainter.Antialiasing)
      self.setRenderHint(QPainter.TextAntialiasing)
      self.setMouseTracking(True);  # Enable mouseMoveEvent
      
      

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
