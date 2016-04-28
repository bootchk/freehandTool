'''
'''


try:
  from PyQt5.QtCore import QEvent, QPointF, QPoint
  from PyQt5.QtWidgets import QGraphicsView
except ImportError:
  from PySide.QtCore import QEvent, QPointF, QPoint
  from PySide.QtGui import QGraphicsView
from .type.pointerPoint import PointerPoint


class PointerEvent(object):
  '''
  Packet of data about a graphics pointing device event.
  
  Passed from app to freehand tool.
  
  Augments raw framework event with scene coordinates, and float view coordinates (from int pixel coords.)
  '''
  
  def __init__(self):
    self.scenePos = None
    self.viewPos = None
    
  # Multiple creation procedures
  def makeFromEvent(self, event, mapper):
    assert isinstance(mapper, QGraphicsView)
    assert isinstance(event, QEvent)
    self.scenePos = mapper.mapToScene(event.x(), event.y())
    # !!! Do NOT convert event coords from int to float, until later
    self.viewPos = PointerPoint(event.x(), event.y())
    
  
  
  def makeFromPoints(self, scenePoint, viewPoint):
    assert isinstance(scenePoint, QPointF)
    assert isinstance(viewPoint, QPoint), str(viewPoint)
    self.scenePos = scenePoint
    self.viewPos = PointerPoint(viewPoint.x(), viewPoint.y())