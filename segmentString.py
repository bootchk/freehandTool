'''
Copyright 2012 Lloyd Konneker

This is free software, covered by the GNU General Public License.



SegmentString, a connected sequence of Segments.

AKA a polyline, multiline, polycurve, etc.

Meaning of Segment and String
======
String: end point of one segment is coincident with start point of next segment.
Segment: abstraction of line, arc, curve (which differ in their count of ControlPoints: 2, 3, 4, ...)

See Shapely and GEOS, where segments are only lines or arcs (LineStrings or CurveStrings.) 
Here, segments are only cubic splines.

Displayable
===========
Only a SegmentString is a Displayable/Composeable 
(see Designing Object Oriented Software by Wirfs-Brock.)
Segments and ControlPoints are models, not view/controllers.

Lifetimes
=========
SegmentString instances are created by freehandTool when user draws, or when unserialized.
References to them are kept in a scene.
SegmentString instances are serialized in a different format (say SVG), than is modeled here.

ControlPointSets, ControlPoints, Segments, Relations instances 
are created when a SegmentString is an operand of an Editor,
when the editor calls SegmentString.getControlPoints(),
and usually the editor makes those ControlPoints visible via Displayable controls.
SegmentString does not store Segment instances.
A user using an editor manipulates ControlPoints, which propagates changes to Segments to SegmentStrings.
See notes below.

Cuspness is populated as a SegmentString is created.

FIXME:
======

Using indexes into QPainterPath as ID of Segment instances is fragile.
It currently depends on all segments being the same type having the same count of elements in QPP.

Cuspness deserialized.
'''


from PySide.QtGui import QGraphicsLineItem, QGraphicsPathItem, QPainterPath
# Qt constants only needed for testing with colored segments
from PySide.QtCore import QPointF, Qt


from segment import CurveSegment
from relations import Relations
from segmentActions import segmentStringActions
from cuspness import Cuspness


class GraphicsLine(QGraphicsLineItem):
  '''
  GraphicsItem that is a line.
  
  Used for ghosting the trailing end while freehandDrawing.
  Initially a zero length line at (0,0).
  Implemented as QGraphicsLineItem.
  
  This is an interface, so that freehand.py does not depend on Qt.Gui
  '''
  pass
  
  
class SegmentString(QGraphicsPathItem):
  '''
  GraphicsItem that is a sequence of Segments.
  
  Segments are line-like curves.

  Segments don't have their own transform,
  so they are moved by changing their control points.
  
  Responsibilities:
  1. know endPoint, startPoint, countSegments
  2. maintain structure (add segment, update segment, delete(FIXME))
  3. get ControlPointSet (so user can manipulate them.)
  4. maintain relations between ControlPoints in ControlPointSet
  5. move control points
  6. maintain cusps and return cuspness of a segment
  
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
  
  ControlPoint Roles and Types
  ============================
  
  ControlPoints play roles.
  The role of a ControlPoint is not explicitly modeled, 
  only modeled by relations between ControlPoints and other conditions.
  
  The relations of ControlPoints to each other are:
  - TiedTo: coincident with a Anchor CP of another segment
  - OppositeTo: is a Anchor CP paired with Anchor CP at opposite end of segment
  - ArmTo: is a CP of an arm between a Direction CP and an Anchor CP
  
  We do it this way for flexibility of design:
  the relations form a network or graph that helps define the behavior when user drags ControlPoints.
  A drag behavior is defined by a traversal method (specialization of walk()) of the relations network.
  
  Cusps
  =====
  
  Cusp-ness is a property between two segments.
  EG two curves form a cusp if their Anchor-Direction arms are NOT colinear.
  It is dynamic, changing as a user moves ControlPoints and thus Segments.
  When segments are added, their cuspness can be declared (but it is not checked.)
  When segments change, cuspness is checked.
  Cuspness is not stored in most serialized formats like SVG.
  Cuspness supports user friendly GUI: cusp points move differently.
  '''
  
  ELEMENTS_PER_SEGMENT = 3
  
  def __init__(self, startingPoint):
    super(SegmentString, self).__init__()
    self.setPath(QPainterPath(startingPoint))
    self.actions = segmentStringActions # singleton
    
    # The following are not necessarily serialized, but usually reconstructable upon deserialize.
    # They are only needed when GUI is displaying ControlPoints as Controls
    self.relations = Relations()
    self.cuspness = Cuspness()
    self.controlPointSet = None
  
  
  # Inherits path()

  '''
  Responsibility: 1. know end points.
  '''

  def getEndPoint(self):
    ''' 
    End point of a SegmentString is:
    - coordinates of its last element
    - OR startingPoint if has no Segments
    '''
    return self._pointForPathElement(element = self.path().elementAt(self.path().elementCount() - 1))
  
  def getStartPoint(self):
    ''' 
    Start point of a SegmentString is:
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
  
  
  
  '''
  Responsibililty: 2. maintain structure.
  '''
  
  def appendSegments(self, segments, segmentCuspness):
    ''' 
    Append segments sequentially to end of self. 
    
    cuspness is [Bool,] equal in length to segments and tells whether each segment is a cusp.
    
    !!! The QPainterPath instance returned by QGraphicsPathItem.path() is a copy
    and when appended to does not change the display.
    IOW QGraphicsPathItem keeps a copy when you call setPath()
    
    FUTURE might be faster to union existing path with new path.
    '''
    # print segments
    
    # copy current path
    pathCopy = self.path()
    segmentOrdinal = 0
    for segment in segments:
      indexOfSegmentInParent=pathCopy.elementCount()
      self._appendSegmentToPath(segment, pathCopy)
      if segmentCuspness[segmentOrdinal]:
        self.cuspness.setCuspness(indexOfSegmentInParent)
      segmentOrdinal += 1
      
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
    # Assert SegmentString.getEndPoint is correct even case last segment updated
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
      yield i * SegmentString.ELEMENTS_PER_SEGMENT + 1
  
  
  def segmentCount(self):
    return self.path().elementCount()/SegmentString.ELEMENTS_PER_SEGMENT
  
  def _copySegmentPathToPath(self, sourcePath, destinationPath, segmentIndex):
    ''' Use elements of a segment from sourcePath to append a segment to destinationPath. '''
    destinationPath.cubicTo(*self._pointsInPathForSegment(sourcePath,segmentIndex))
  
  
  def _pointsInPathForSegment(self, path, segmentIndex):
    ''' 
    Return list of QPointF for QPathElements of segment.
    !!! This is a 3-tuple, not sufficient for creating Segment
    '''
    result = []
    for i in range(0, SegmentString.ELEMENTS_PER_SEGMENT):
      result.append(self._pointForPathElement(element = path.elementAt(segmentIndex + i)))
    return result
    
    
    
  '''
  Responsibility: 
  3. Get getControlPointSet so user can manipulate them
  4. maintain relations between ControlPoints in ControlPointSet
  '''
  def getControlPointSet(self):
    '''
    Instantiate for self:
    - ControlPoints
    - Segments
    - Relations (among ControlPoints)
    Returns list of ControlPoint.
    '''
    # NOT assert self.controlPointSet is None
    self.relations.clear()
    result = []
    previousEndControlPoint = None
    for segmentIndex in self._segmentIndexIter():
      segment = self._createSegmentAt(segmentIndex)
      for controlPoint in segment.controlPointIter():
        result.append(controlPoint)
      segment.createRelations(relations=self.relations, previousEndAnchor=previousEndControlPoint)
      previousEndControlPoint = segment.getEndControlPoint()
    self.controlPointSet = result # Remember my own ControlPoint set
    # FIXME: above does NOT allow for many views of same SegmentString
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
      startPoint = self._pointsInPathForSegment(self.path(), segmentIndex - SegmentString.ELEMENTS_PER_SEGMENT)[-1]
    pointsFromPath = self._pointsInPathForSegment(self.path(), segmentIndex)
    segment = CurveSegment(startPoint, *pointsFromPath)
    # assert ControlPoints were created and refer to segment
    segment.setIndexInParent(parent=self, indexOfSegmentInParent = segmentIndex)
    return segment
  
  
  def clearTraversal(self):
    ''' Clear traversal flags to prepare for new traversal. '''
    for controlPoint in self.controlPointSet:
      controlPoint.setTraversed(False)
  
  
  '''
  Responsibility:  5. move control points
  '''
  
  def moveRelated(self, controlPoint, deltaCoordinate, alternateMode):
    ''' Move (translate) controlPoint and set of related controlPoints. '''
    self.clearTraversal() # movement by traversal of relations
    # delegate to strategy/policy
    self.actions.moveRelated(self.relations, controlPoint, deltaCoordinate, alternateMode)
  
  
  '''
  6. maintain cusps and return cuspness of a segment
  '''
  def isSegmentCusp(self, segmentIndex):
    return self.cuspness.isCusp(segmentIndex)
    
  def setSegmentCuspness(self, segmentIndex):
    self.cuspness.setCuspness(segmentIndex)


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
        painter.setPen(Qt.blue)
      else:
        painter.setPen(Qt.red)
