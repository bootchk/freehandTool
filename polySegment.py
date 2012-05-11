
'''
Models of a polysegment.
Also known as a polyline, multiline, polycurve, etc.

Lifetimes:
Model instances are created when user draws, or when unserialized.
Model instances are serialized in a different format (say SVG.)
Relations between model instances are created only when a polysegment is an operand
(when the control points become visible to the user.)
'''

from PySide.QtGui import QGraphicsLineItem, QGraphicsPathItem, QPainterPath
# Qt constants only needed for testing with colored segments
from PySide.QtCore import QPointF, Qt


class GraphicsLine(QGraphicsLineItem):
  '''
  GraphicItem that is a line.
  
  Used for ghosting line in freehandDrawing
  Initially a zero length line at (0,0).
  Implemented as QGraphicsLineItem.
  '''
  pass
  
  
class PolySegment(QGraphicsPathItem):
  '''
  GraphicItem that is a sequence of segments.
  
  Segments are line-like curves.
  Segments can NOT be moved independently (don't have their own transform.)
  
  Responsibilities:
  - maintain structure (add, delete segments)
  - know endPoint
  
  Specific to Qt GUI toolkit.
  '''
  def __init__(self, startingPoint):
    super(PolySegment, self).__init__()
    path = QPainterPath(startingPoint)
    self.setPath(path)
    self.endPoint = startingPoint


  def getEndPoint(self):
    return self.endPoint
  
  
  def addSegments(self, segments):
    ''' 
    Add sequence of segments to my path. 
    
    FUTURE might be faster to union existing path with new path.
    '''
    # print segments
    
    # copy current path
    path = self.path()
    for segment in segments:
      # !!! Note all segments represented by cubic curve
      # !!! Note cubic only wants the final three points
      path.cubicTo(*segment.asPoints()[1:])
      self.endPoint = segment.getEndPoint()
      
    # !!! path is NOT an alias for self.path() now, they differ.  Hence:
    self.setPath(path)
    # No need to invalidate or update display, at least for Qt
  
  
  
  
  # TESTING: helps see segments.  Not necessary for production use.
  def paint(self, painter, styleOption, widget):
    ''' Reimplemented to paint elements in alternating colors '''
    path = self.path()  # alias
    pathEnd = None
    i = 0
    while True:
      try:
        element = path.elementAt(i)
        # print type(element), element.type
        if element.isMoveTo():
          pathEnd = QPointF(element.x, element.y)
          i+=1
        elif element.isLineTo():
          newEnd = QPointF(element.x, element.y)
          painter.drawLine(pathEnd, newEnd)
          pathEnd = newEnd
          i+=1
        elif element.isCurveTo():
          # Gather curve data, since is spread across elements of type curveElementData
          cp1 = QPointF(element.x, element.y)
          element = path.elementAt(i+1)
          cp2 = QPointF(element.x, element.y)
          element = path.elementAt(i+2)
          newEnd = QPointF(element.x, element.y)
          # create a subpath, since painter has no drawCubic method
          subpath=QPainterPath()
          subpath.moveTo(pathEnd)
          subpath.cubicTo(cp1, cp2, newEnd)
          painter.drawPath(subpath)
          
          pathEnd = newEnd
          i+=3
        else:
          print "unhandled path element", element.type
          i+=1
        if i >= path.elementCount():
          break
      except Exception as inst:
        print inst
        break
        
      # Alternate colors
      if i%2 == 1:
        painter.setPen(Qt.blue)
      else:
        painter.setPen(Qt.red)
