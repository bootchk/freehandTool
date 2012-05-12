
'''
PolySegment, a connected sequence of Segments.
AKA a polyline, multiline, polycurve, etc.

Displayable
===========
Only a PolySegment is a Displayable/Composeable 
(see Designing Object Oriented Software by Wirfs-Brock.)
Segments and ControlPoints are models, not view/controllers.

Lifetimes
=========
PolySegment instances are created by freehandTool when user draws, or when unserialized.
References to them are kept in the scene.
PolySegment instances are serialized in a different format (say SVG.)

ControlPointSets, ControlPoints, Segments, Relations instances 
are created when a PolySegment is an operand of an editor,
when the editor calls PolySegment.getControlPoints(),
and usually the editor makes those ControlPoints visible via Displayable controls.
PolySegment does not actually store Segment instances.
IOW, a user using an editor manipulates ControlPoints,
which propagates changes to Segments to PolySegments.
See notes below.
'''

from PySide.QtGui import QGraphicsLineItem, QGraphicsPathItem, QPainterPath
# Qt constants only needed for testing with colored segments
from PySide.QtCore import QPointF, Qt

from segment import CurveSegment


class GraphicsLine(QGraphicsLineItem):
  '''
  GraphicsItem that is a line.
  
  Used for ghosting line in freehandDrawing
  Initially a zero length line at (0,0).
  Implemented as QGraphicsLineItem.
  
  This is an interface, so that freehand.py does not depend on Qt.Gui
  '''
  pass
  
  
class PolySegment(QGraphicsPathItem):
  '''
  GraphicsItem that is a sequence of Segments.
  
  Segments are line-like curves.

  Segments don't have their own transform,
  so they are moved by changing their control points.
  
  Responsibilities:
  - maintain structure (add segment, update segment, delete(FIXME))
  - know endPoint, startPoint, countSegments
  - get ControlPointSet (so user can manipulate them.)
  
  Specific to Qt GUI toolkit.
  
  Lifetime
  ========
  
  !!! Note that appendSegments() doesn't store references to Segments passed as parameters.
  This stores segments in an internal format (currently QPainterPath), not as Segment instances.
  getControlPointSet() returns ControlPoint instances which refer to Segment instances,
  and all those persist as long as you keep the ControlPointSet.
  
  Internal format using QPainterPath
  ==================================
  A QPainterPath is a sequence of QPathElements having a type.
  For a cubic curve, there are three consecutive QPathElements of type CubicTo.
  QPainterPath is not updateable, only appendable.
  
  Here, the first QPathElement is type MoveTo, followed by 3-tuples of type CubicTo.
  '''
  ELEMENTS_PER_SEGMENT = 3
  
  def __init__(self, startingPoint):
    super(PolySegment, self).__init__()
    self.setPath(QPainterPath(startingPoint))


  # Inherits path()


  def getEndPoint(self):
    ''' 
    End point of a PolySegment is:
    - coordinates of its last element
    - OR startingPoint if has no Segments
    '''
    return self._pointForPathElement(element = self.path().elementAt(self.path().elementCount() - 1))
  
  def getStartPoint(self):
    ''' 
    Start point of a PolySegment is:
    - first element, regardless if has any Segments
    '''
    return self._pointForPathElement(element = self.path().elementAt(0))
  
  
  def _pointForPathElement(self, element):
    '''
    Return  QPointF for QPathElements.
    QPathElements don't have a x() method
    Symptoms are "Exception: reverse not implemented"
    '''
    return QPointF(element.x, element.y)
  
  
  def appendSegments(self, segments):
    ''' 
    Append segments sequentially to end of self. 
    
    !!! The QPainterPath instance returned by QGraphicsPathItem.path() is a copy
    and when appended to does not change the display.
    IOW QGraphicsPathItem keeps a copy when you call setPath()
    
    FUTURE might be faster to union existing path with new path.
    '''
    # print segments
    
    # copy current path
    pathCopy = self.path()
    for segment in segments:
      #segment.setIndexInParent(parent=self, indexOfSegmentInParent=pathCopy.elementCount())
      self._appendSegmentToPath(segment, pathCopy)
    # !!! pathCopy is NOT an alias for self.path() now, they differ.  Hence:
    self.setPath(pathCopy)
    # No need to invalidate or update display, at least for Qt
    
    # TEST try to alter the path: has no effect, QPathElements are constants??
    #pathCopy.elementAt(1).x += 20
    #self.setPath(pathCopy)


  def _appendSegmentToPath(self, segment, path):
    ''' 
    Append internal representation of given Segment instance to given path. 
    
    !!! All segments represented by QPathElement of ElementType:cubic i.e. curve
    !!! Cubic only wants the final three ControlPoints.
    '''
    path.cubicTo(*segment.asPoints()[1:])
    
  
  def segmentChanged(self, segment, indexOfSegmentInParent):
    ''' Given segment has changed. Propagate change to self. '''
    self.updateSegment(segment, indexOfSegmentInParent)
  
  
  def updateSegment(self, segment, indexOfSegmentInParent):
    '''
    Update drawable with changed segment.
    
    Understands that internal format self.path() is not updateable.
    Thus it is copy into new, with one changed segment in the middle.
    IE copies prefix, appends changed Segment, copies suffix.
    '''
    # startingPoint same as existing path
    # FIXME: what if user changes the starting controlPoint???
    newPath = QPainterPath(self.path().elementAt(0))
    for segmentIndex in self._segmentIndexIter():
      if segmentIndex == indexOfSegmentInParent:
        self._appendSegmentToPath(segment, newPath)
      else:
        self._copySegmentPathToPath(sourcePath=self.path(), destinationPath=newPath, segmentIndex=segmentIndex)
    # Assert PolySegment.getEndPoint is correct even case last segment updated
    self.setPath(newPath)
        
      
  def _segmentIndexIter(self):
    ''' 
    Generate indexes of segments.
    An index is NOT the ordinal.
    An index is the ordinal of the QPathElement of the first QPathElement for segment.
    Starts at 1, since here zeroeth QPathElement is a MoveTo.
    EG 1, 4, 7, 10, ...
    
    !!! Relies on all segments represented as 3-tuple curves.
    '''
    for i in range(0, self.segmentCount()):
      yield i * PolySegment.ELEMENTS_PER_SEGMENT + 1
  
  
  def segmentCount(self):
    return self.path().elementCount()/PolySegment.ELEMENTS_PER_SEGMENT
  
  def _copySegmentPathToPath(self, sourcePath, destinationPath, segmentIndex):
    ''' Use elements of a segment from sourcePath to append a segment to destinationPath. '''
    destinationPath.cubicTo(*self._pointsInPathForSegment(sourcePath,segmentIndex))
  
  
  def _pointsInPathForSegment(self, path, segmentIndex):
    ''' 
    Return list of QPointF for QPathElements of segment.
    !!! This is a 3-tuple, not sufficient for creating Segment
    '''
    result = []
    for i in range(0, PolySegment.ELEMENTS_PER_SEGMENT):
      result.append(self._pointForPathElement(element = path.elementAt(segmentIndex + i)))
    return result
    
    
  def getControlPointSet(self):
    '''
    Instantiate ControlPoints and Segments for self.
    Returns list of ControlPoint.
    '''
    result = []
    for segmentIndex in self._segmentIndexIter():
      segment = self._createSegmentAt(segmentIndex)
      for controlPoint in segment.controlPointIter():
        result.append(controlPoint)
    return result
  
  
  def _createSegmentAt(self, segmentIndex):
    ''' Create Segment instance for what is described in path at segmentIndex. 
    
    !!! Expand the run-encoding of QPainterPath
    (last point of previous segment shared with first point of next segment.)
    E.G. CurveSegment requires four points from three in the path.
    '''
    # print "SegmentIndex", segmentIndex
    if segmentIndex == 1:
      # Only one prior element, a MoveTo
      startPoint = self.getStartPoint()
    else:
      # Last point of previous segment is first point of this segment
      startPoint = self._pointsInPathForSegment(self.path(), segmentIndex - PolySegment.ELEMENTS_PER_SEGMENT)[-1]
    pointsFromPath = self._pointsInPathForSegment(self.path(), segmentIndex)
    segment = CurveSegment(startPoint, *pointsFromPath)
    # assert ControlPoints were created and refer to segment
    segment.setIndexInParent(parent=self, indexOfSegmentInParent = segmentIndex)
    return segment
    
  '''
  TESTING: Reimplement paint() to help see segments.  Not necessary for production use.
  '''
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
        painter.setPen(Qt.blue)
      else:
        painter.setPen(Qt.red)
