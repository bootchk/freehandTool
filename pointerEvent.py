'''
'''

from PySide.QtCore import QEvent, QPointF
from PySide.QtGui import QGraphicsView

class PointerEvent(object):
  '''
  Packet of data about a graphics pointing device event.
  '''
  
  def __init__(self):
    self.scenePos = None
    self.viewPos = None
    
  # Multiple creation procedures
  def makeFromEvent(self, event, mapper):
    assert isinstance(mapper, QGraphicsView)
    assert isinstance(event, QEvent)
    self.scenePos = mapper.mapToScene(event.x(), event.y())
    # !!! Convert event coords from int to float
    self.viewPos = QPointF(event.x(), event.y())
    
    
  def makeFromPoints(self, scenePoint, viewPoint):
    assert isinstance(scenePoint, QPointF)
    assert isinstance(viewPoint, QPointF)
    self.scenePos = scenePoint
    self.viewPos = viewPoint