#!/usr/bin/env python


'''
Qt app demonstrating freehand drawing tool.

Copyright 2012 Lloyd Konneker

This is free software, covered by the GNU General Public License.
'''     

from PySide.QtCore import *
from PySide.QtGui import *
import sys

from pointerEvent import PointerEvent
from freehand import FreehandTool
from ghostLine import PointerTrackGhost
from segmentString import SegmentString


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
      
      self.freehandTool = FreehandTool()



  ''' Delegate events to FreehandTool. '''
    
  def mouseMoveEvent(self, event):
    ''' Tell freehandTool to update its SegmentString. '''
    self.freehandTool.pointerMoveEvent(PointerEvent(mapper=self, event=event))
  
  
  def mousePressEvent(self, event):
    '''
    On mouse button down, create a new (infinitesmal) SegmentString and PointerTrackGhost.
    freehandTool remembers and updates SegmentString.
    '''
    pointerEvent = PointerEvent(mapper=self, event=event) # massage event
    
    '''
    freehandCurve as QGraphicsItem positioned at event in scene.
    It keeps its internal data in its local CS
    '''
    freehandCurve = SegmentString()
    self.scene().addItem(freehandCurve)
    freehandCurve.setPos(pointerEvent.scenePos)

    '''
    headGhost at (0,0) in scene
    it keeps its local data in CS equivalent to scene
    '''
    headGhost = PointerTrackGhost()
    self.scene().addItem(headGhost)
    
    self.freehandTool.setSegmentString(segmentString=freehandCurve, 
                                       pathHeadGhost=headGhost, 
                                       scenePosition=pointerEvent.scenePos)
    self.freehandTool.pointerPressEvent(pointerEvent)

    
  def mouseReleaseEvent(self, event):
    self.freehandTool.pointerReleaseEvent(PointerEvent(mapper=self, event=event))
  
  
  def keyPressEvent(self, event):
    self.freehandTool.keyPressEvent(event)
    
  
      
      

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
