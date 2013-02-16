'''
Copyright 2013 Lloyd Konneker

This is free software, covered by the GNU General Public License.

Ghost line for head of being-drawn freehand curve.
With a pipeline, the head is not known precisely, but needs to be drawn
so that there is no gap between the pointer and the freehand curve.

This is one alternative.
Another alternative is keep the head in the SegmentString, updating it.
'''

from PySide.QtGui import QGraphicsLineItem
from PySide.QtCore import QLineF



class GraphicsLine(QGraphicsLineItem):
  '''
  GraphicsItem that is a line.
  
  Used for ghosting the trailing end while freehandDrawing.
  Initially a zero length line at (0,0).
  Implemented as QGraphicsLineItem.
  
  This is an interface, so that freehand.py does not depend on Qt.Gui
  '''
  pass


class PointerTrackGhost(object):
  '''
  A ghost for freehand drawing.
  Line between current PointerPosition and last PointerTrack path segment generated, which lags.
  Finally replaced by a path segment.
  Hidden when user not using freehand tool.
  '''
  def __init__(self, scene):
    self.lineItem = GraphicsLine()
    self.lineItem.hide()
    self.start = None
    self.end = None
    scene.addItem(self.lineItem)
  
  def showAt(self, initialPosition):
    self.start = initialPosition
    self.end = initialPosition
    self.lineItem.setLine(QLineF(self.start, self.end))
    self.lineItem.show()
    
  def updateStart(self, point):
    self.start = point
    self.lineItem.setLine(QLineF(self.start, self.end))
    
  def updateEnd(self, point):
    self.end = point
    self.lineItem.setLine(QLineF(self.start, self.end))
    
  def hide(self, point):
    self.lineItem.hide()
