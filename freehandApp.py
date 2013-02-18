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
    self.freehandTool.pointerMoveEvent(position=self.viewPosOfEvent(event))
  
  
  def mousePressEvent(self, event):
    '''
    On mouse button down, create a new (infinitesmal) SegmentString and PointerTrackGhost.
    freehandTool remembers and updates SegmentString.
    '''
    freehandCurve = SegmentString()
    self.scene().addItem(freehandCurve)
    freehandCurve.setPos(self.scenePosOfEvent(event))
    # freehandCurve as QGraphicsItem positioned at event in scene.
    # it keeps its internal data in its local CS
    
    headGhost = PointerTrackGhost()
    self.scene().addItem(headGhost)
    # headGhost at (0,0) in scene
    # it keeps its local data in CS equivalent to scene
    
    self.freehandTool.setSegmentString(segmentString=freehandCurve, 
                                       pathHeadGhost=headGhost, 
                                       scenePosition=self.scenePosOfEvent(event))
    self.freehandTool.pointerPressEvent(position=self.viewPosOfEvent(event))

    
  def mouseReleaseEvent(self, event):
    self.freehandTool.pointerReleaseEvent(position=self.viewPosOfEvent(event))
  
  
  def keyPressEvent(self, event):
    self.freehandTool.keyPressEvent(event)
    
  def scenePosOfEvent(self, event):
    return self.mapToScene(event.x(), event.y())
    
  def viewPosOfEvent(self, event):
    '''
    Event coords in View, as float !!! since freehandTool wants a float.
    '''
    result = QPointF(event.x(), event.y())
    #print "View pos", result
    return result
      
      

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
