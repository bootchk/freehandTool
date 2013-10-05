'''
Copyright 2013 Lloyd Konneker

This is free software, covered by the GNU General Public License.

Ghost line for head of being-drawn freehand curve.
With a pipeline, the head is not known precisely, but needs to be drawn
so that there is no gap between the pointer and the freehand curve.

This is one alternative.
Another alternative is keep the head in the SegmentString, updating it.
'''

from PyQt5.QtGui import QGraphicsLineItem
from PyQt5.QtCore import QLineF, QPoint



class PointerTrackGhost(QGraphicsLineItem):
  '''
  A ghost for freehand drawing.
  Line between current PointerPosition and last PointerTrack path segment generated, which lags.
  Finally replaced by a path segment.
  Hidden when user not using freehand tool.
  
  Implementation: extend QGraphicsLineItem.
  See alternate implementation: freehandHead.py
  
  This presents a simplified API to FreehandTool,
  to reduce coupling between FreehandTool and Qt.
  '''
  def __init__(self, **kwargs):
    super(PointerTrackGhost,self).__init__(**kwargs)
    self.start = None
    self.end = None
    # ensure is hidden, not in scene
  
  def showAt(self, initialPosition):
    self.start = initialPosition
    self.end = initialPosition
    self.setLine(QLineF(self.start, self.end))
    self.show()
    
  def updateStart(self, pointVCS):
    ''' !!! start point from FreehandTool is in View CS. '''
    pointViewInt = QPoint(pointVCS.x(), pointVCS.y())
    pointSceneFloat = self.scene().views()[0].mapToScene(pointViewInt)
    self.start = pointSceneFloat
    self.setLine(QLineF(self.start, self.end))
    
  def updateEnd(self, point):
    self.end = point
    self.setLine(QLineF(self.start, self.end))
    
  # hide() is inherited