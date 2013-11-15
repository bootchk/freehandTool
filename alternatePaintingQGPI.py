'''
Copyright 2012, 2013 Lloyd Konneker

This is free software, covered by the GNU General Public License.
'''
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QPainterPath



class AlternateColorPaintingQGPI(object):
  '''
  Mixin behaviour for testing SegmentString
  
  Reimplement paint() to help see segments.  Not necessary for production use.
  
  SegmentString multiply inherit this class for testing.
  '''
  def paint(self, painter, styleOption, widget):
    ''' Reimplemented to paint elements in alternating colors '''
    path = self.path()  # alias
    pathEnd = None
    i = 0
    while True:
      try:
        element = path.elementAt(i)
        #print type(element), element.type
        if element.isMoveTo():
          pathEnd = QPointF(element.x, element.y)
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
          """
          TODO: if SegmentStringss contain lines (w/o Direction ControlPoints)
          !!! We don't use QPathElements of type Line
          elif element.isLineTo():
            newEnd = QPointF(element.x, element.y)
            painter.drawLine(pathEnd, newEnd)
            pathEnd = newEnd
            i+=1
          """
        if i >= path.elementCount():
          break
      except Exception as inst:
        print inst
        break
        
      # Alternate colors
      if i%2 == 1:
        painter.setPen(Qt.green)
      else:
        painter.setPen(Qt.red)
