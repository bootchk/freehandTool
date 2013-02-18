'''
'''

from PySide.QtCore import QEvent, QPointF
from PySide.QtGui import QGraphicsView

class PointerEvent(object):
  '''
  Packet of data about a graphics pointing device event.
  '''
  
  def __init__(self, event, mapper):
    assert isinstance(mapper, QGraphicsView)
    assert isinstance(event, QEvent)
    self.scenePos = mapper.mapToScene(event.x(), event.y())
    # !!! Convert event coords from int to float
    self.viewPos = QPointF(event.x(), event.y())
    