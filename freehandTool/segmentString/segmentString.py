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

Coordinate systems
==================

Coordinates of incoming segments in View CS.
Segments stored internally in Local CS of QGraphicsPathItem.


FIXME:
======

Using indexes into QPainterPath as ID of Segment instances is fragile.
It currently depends on all segments being the same type having the same count of elements in QPP.

Cuspness deserialized.
'''

try:
  from PyQt5.QtGui import QPainterPath
  from PyQt5.QtCore import QPointF
  from PyQt5.QtWidgets import QGraphicsPathItem
except ImportError:
  from PySide.QtCore import QPointF
  from PySide.QtGui import QPainterPath, QGraphicsPathItem

from .segment import CurveSegment
from .relations import Relations
from .segmentActions import segmentStringActions
from .cuspness import Cuspness


'''
For testing, inherit mixin AlternateColorPaintingQGPI, that paints alternate segments different colors.
Then you can distinguish segments, and see when the head collapses due to pauses and flushes.
'''
## For testing (so you can visually distinguish segments) use: 
##from alternatePaintingQGPI import AlternateColorPaintingQGPI
##class SegmentString(AlternateColorPaintingQGPI, QGraphicsPathItem):

## For production use:
class SegmentString(QGraphicsPathItem):
  '''
  GraphicsItem that is a sequence of Segments.
  
  Segments are line-like curves.

  Segments don't have their own transform.
  Change their appearance by moving their control points.
  When user drags control points, comes here as segmentChanged().
  
  Responsibilities:
  0. know internal representation
  1. know endPoint, startPoint, countSegments
  2. maintain structure (add segment, update segment, delete(FIXME))
  3. get ControlPointSet (so user can manipulate them.)
  4. maintain relations between ControlPoints in ControlPointSet
  5. move control points
  6. maintain cusps and return cuspness of a segment
  7. map between representations: external (Segment in View CS View) and internal (QPathElement in Local CS)
  
  Specific to Qt GUI toolkit.
  
  Lifetime
  ========
  
  !!! Note that appendSegments() doesn't store references to Segments passed as parameters.
  This stores segments in an internal format (currently QPainterPath), not as Segment instances.
  getControlPointSet() returns ControlPoint instances which refer to Segment instances,
  and all those persist as long as you keep the ControlPointSet.
  
  Internal format using QPainterPath
  ==================================
  A QPainterPath is a sequence of QPathElements having a PathElementType.
  For a cubic curve, there are three consecutive QPathElements of type CubicTo.
  QPainterPath is not updateable, only appendable.
  
  !!! Here, the first QPathElement is type MoveTo, followed by 3-tuples of PathElements of type CubicTo.
  !!! Currently, no support for other PathElementTypes (i.e. no LineTo)
  !!! Our segment is extracted as a 4-tuple comprising the last PathElement (the endPoint)
  of one 3-tuple and three PathElements of the next 3-tuple.
  
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
  
  # !!! All Segments are cubic but internally, a segment is THREE PathElement types ofCubicTo
  ELEMENTS_PER_SEGMENT = 4
  ENCODED_ELEMENTS_PER_SEGMENT = 3
  
  def __init__(self):
    super(SegmentString, self).__init__()
    self.actions = segmentStringActions # singleton
    
    # The following are not necessarily serialized, but usually reconstructable upon deserialize.
    # They are only needed when GUI is displaying ControlPoints as Controls
    self.relations = Relations()
    self.cuspness = Cuspness()
    self.controlPointSet = None
    
    self.cachedEndFreehandPoint = None
    
    self.setPath(QPainterPath(self.origin()))
    # ensure: path has been set, self.myPath() returns "MoveTo(0,0)"
  
  
  '''
  Responsibility 0. know internal representation
  '''
  def myPath(self):
    '''
    QPainterPath i.e. internal representation.
    
    Explicitly calls QGraphicsPathItem.path(), since a class that inherits this class
    may reimplement path(), and then a call from this module to self.path() would
    find the reimplemented method via the MRO.
    (For example, a class that inherits may redefine path() to return a one pixel larger path, etc.)
    
    !!! Do not use self.path() in this module.
    
    Public since importers of this module (library) may want it,
    but note that it is a copy, not updateable to any effect.
    '''
    return super(SegmentString, self).path()


  '''
  Responsibility: 1. know end points.
  
  !!! Note two different CS.
  '''

  def origin(self):
    '''
    Origin of the local CS.  Conventionally, 0,0.
    Where the internal path initially starts, in Local CS.
    !!! Note the user can change the initial segment,
    and then this is NOT the startPoint of the SegmentString.
    '''
    return QPointF(0,0)
  
  '''
  Formerly:
  def setStartPoint(self, startPoint):
    self.setPath(QPainterPath(startPoint))
    
    # !!! This should work, but doesn't?: self.setPath(QPainterPath(startPoint=startPoint))
    # It cost many hours finding that fact out.
    # Before we changed to VCS, this was: 
  '''
    
    
  """
  Not used
  
  def getEndFreehandPoint(self):
    '''
    End point of segment in same frame as it was created from (frame used by CurveGenerator.)
    
    The implementation is: cached.
    So as to avoid possible loss of precision from inverse transformation. (Probably not important.)
    
    
    End point of a SegmentString is:
    - coordinates of its last element, in VCS
    - OR startingPoint if has no Segments
    
    The implementation is an optimization.  Roughly equivalent code is:
    if self.countSegments() < 1:
       return self.getStartPoint()
    else:
       return self._pointVCSForPathElement(self.segmentAt(self._indexOfLastSegment())[-1])
    '''
    return self._pointVCSForPathElement(element = self.myPath().elementAt(self.myPath().elementCount() - 1))
  
  
  def getStartPointVCS(self):
    ''' 
    Start point of a SegmentString is:
    - first element, regardless if has any Segments
    - in VCS
    '''
    return self._pointVCSForPathElement(element = self.myPath().elementAt(0))
  """

  def getStartPointLCS(self):
    '''
    Start QPointF of self.
    
    Note elementAt returns type Element in PyQt, and PyQt complains later (PySide did not.)
    Convert to QPointF.  Note Element.x is a property, not a method.
    '''
    startElement = self.myPath().elementAt(0)
    return QPointF(startElement.x, startElement.y)
  
  
  '''
  Responsibility: 7. map between frames (coordinate systems)
  
  Self is a QGraphicsItem which knows how to map from Local to Scene.
  '''
  def _mapFromSceneToLocal(self, pointSCS):
    return self.mapFromScene(pointSCS)
  
  def _mapFromLocalToScene(self, pointLCS):
    return self.mapToScene(pointLCS)
    
    
    
  """ 
  Not used CRUFT from before int/float and View/Scene/Local CS were fixed.
  
  def _pointVCSForPathElement(self, element):
    '''
    Return  QPointF in VCS for QPathElements.
    QPathElements don't have x(); calling it gives symptom "Exception: reverse operator not implemented"
    
    Also map from Local CS (of the QGraphicsItem) to View CS (of the tool)
    '''
    return self._mapFromLocalToDevice(self._unmappedPointForPathElement(element))
  
  def _mapFromLocalToDevice(self, pointLCS):
    pointSCS = self.mapToScene(pointLCS)
    # !!! Loss of precision
    intPointVCS = self.scene().views()[0].mapFromScene(pointSCS)
    return QPointF(intPointVCS)
  
  def _mapFromDeviceToLocal(self, pointVCS):
    '''
    Map from freehandTool internal coordinate in View CS float
    to QGraphicsItem Local CS float.
    '''
    # !!! Loss of precision
    intPointVCS = QPoint(round(pointVCS.x()), round(pointVCS.y()))
    pointSCS = self.scene().views()[0].mapToScene(intPointVCS)
    return self.mapFromScene(pointSCS)
  """
  

  
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
    ##print "Append segments", segments
    
    '''
    For robustness, check this call is effective.
    assert no segment is null (checked by Segment __init__() )
    If for any reason a null segment is passed to Qt, Qt quietly omits it from QPainterPath.
    And then segmentCuspness is not one-to-one with segments.
    '''
    if len(segments) <= 0:
      return

    pathCopy = self.myPath()
    inSegmentOrdinal = 0
    previousSegmentCount = self.countSegments()
    for segment in segments:
      self._appendSegmentToPath(segment, pathCopy)
      newSegmentCount = self.countSegments()
      if  newSegmentCount == previousSegmentCount + 1 :
        # was effective, remember cuspness
        if segmentCuspness[inSegmentOrdinal]:
          # !!! Store cuspness indexed by segment ordinal, NOT index
          self.cuspness.setCuspness(self.countSegments() - 1)
      else:
        '''
        SegmentString refused a Null segment (after coordinate conversion.)
        It doesn't matter visually, or to the generators.
        '''
        pass
      previousSegmentCount = newSegmentCount
      inSegmentOrdinal += 1
      
    # !!! pathCopy is NOT an alias for self.myPath() now, they differ.  Hence:
    self.setPath(pathCopy)
    
    '''
    NOT ensure self.countSegments() == previousSegmentCount + len(segments)
		since SegmentString may have refused to append a segment.
		'''
    
    # TEST try to alter the path: has no effect, QPathElements are constants??
    #pathCopy.elementAt(1).x += 20
    #self.setPath(pathCopy)


  def _appendSegmentToPath(self, segment, path):
    ''' 
    Append Segment instance to path, converting to Local CS.
    
    assert Segment in VCS !!!
    Not assert Segment coordinates are integers, since freehand works in float.
    assert not segment.isNull(), provable since Segment constructor methods have this assertion.
    '''
    
    # !!! Python map() and Qt 'map' meaning transform between coordinate systems
    ## WAS pointsLCS = map(self._mapFromDeviceToLocal, segment.asPointsScene())
    pointsLCS = list(map(self._mapFromSceneToLocal, segment.asPointsScene()))
    
    '''
    !!! Now the segment might be null, due to floating point errors.
    So this may not be effective: may not append anything.
    If caller requires effectiveness, caller must check that path is increased.
    '''
    self.appendInternalRepr(path, pointsLCS)
    
    
  def appendInternalRepr(self, path, pointsLCS):
    '''
    Append internal repr of segment for given pointsLCS.
    
    !!! This should be the only place where we know that internal repr is cubicTo (even for straight lines.)
    !!! and cubicTo has 3 points of Segment's 4 points.
    '''
    assert len(pointsLCS) == SegmentString.ELEMENTS_PER_SEGMENT
    #print "appendInternalRep", pointsLCS
    path.cubicTo(*pointsLCS[1:])
  
  
  def segmentChanged(self, segment, indexOfSegmentInString):
    ''' 
    User changed control points of segment (i.e. model.)
    Propagate change to path (i.e. view.) 
    '''
    ##print "Segment changed"
    self.updateSegment(segment, indexOfSegmentInString)
  
  
  def updateSegment(self, segment, indexOfSegmentInString):
    '''
    Update drawable with changed segment.
    
    Understands that internal format self.myPath() is not updateable.
    Thus it is copy into new, with one changed segment in the middle.
    IE copies prefix, appends changed Segment, copies suffix.
    '''
    # startingPoint same as existing path, NOT origin()
    '''
    Wierdness: Qt docs not show constructor QPainterPath(QPainterPathElement) 
    but QPainterPathElement is duck-typed to QPointF.
    '''

    # !!! TODO check that appending is effective.
    # The updated segment may be null to its predecessor or successor.
    # Then cuspness is whack
    startPoint = self.getStartPointLCS()
    newPath = QPainterPath(startPoint)  # self.myPath().elementAt(0))
    for segmentIndex in self._segmentIndexGenerator():
      if segmentIndex == indexOfSegmentInString:
        self._appendSegmentToPath(segment, newPath)
      else:
        self._copySegmentPathToPath(sourcePath=self.myPath(), destinationPath=newPath, segmentIndex=segmentIndex)
    # Invariant: SegmentString.getEndPoint is correct even case last segment updated
    self.setPath(newPath)
        
      
  def _segmentIndexGenerator(self):
    ''' 
    Generate indexes of segments.
    An index is NOT the ordinal.
    An index is the ordinal of the QPathElement of the first QPathElement for segment.
    EG 0, 3, 6, ...
    First QPathElement for a Segment is either the leading MoveTo, or the last of a 3-tuple of preceding cubicTo.
    Next three QPathElements are from a 3-tuple for a cubicTo.
    
    !!! Relies on all segments (except the first MoveTo) represented as 3-tuple curves.
    '''
    for i in range(0, self.countSegments()):
      yield i * SegmentString.ENCODED_ELEMENTS_PER_SEGMENT
  
  
  def countSegments(self):
    '''
    Notes: 
    countSegments  elementCount  segmentIndex
    0              1              None
    1              4              0
    2              7              3
    3              10             6
    '''
    # Truncate float
    result = int(self.myPath().elementCount()/SegmentString.ENCODED_ELEMENTS_PER_SEGMENT)
    return result
  
  
  def _indexOfLastSegment(self):
    # assert self.countSegments() > 0
    result = self.myPath().elementCount() - SegmentString.ELEMENTS_PER_SEGMENT
    if result < 0:
      return None
    else:
      return result
    
    
  def approximatingLineLCSGenerator(self):
    '''
    Generate lines that approximate each segment.
    Where a line is described by a tuple (point1, point2)
    Used for example to approximately graphics pick a segment.
    '''
    for index in self._segmentIndexGenerator():
      segmentPoints = self._pointsLCSInPathForSegment(self.myPath(), index)
      # First and last points are start and end
      yield segmentPoints[0], segmentPoints[3]
      
  
  def _copySegmentPathToPath(self, sourcePath, destinationPath, segmentIndex):
    ''' Use elements of a segment from sourcePath to append a segment to destinationPath. '''
    pointsLCS = self._pointsLCSInPathForSegment(sourcePath,segmentIndex)
    self.appendInternalRepr(path=destinationPath, pointsLCS=pointsLCS)
  
  
  def _pointsLCSInPathForSegment(self, path, segmentIndex):
    ''' 
    Return list of QPointF for QPathElements of segment.
    Points are in LCS
    !!! This is a 4-tuple, for creating Segment, one extra for creating internal repr
    '''
    result = []
    for i in range(0, SegmentString.ELEMENTS_PER_SEGMENT):
      result.append(self._unmappedPointForPathElement(element = path.elementAt(segmentIndex + i)))
    return result
    
  def _unmappedPointForPathElement(self, element):
    ''' Point in LCS for element. '''
    return QPointF(element.x, element.y)
  
  def _pointsSCSInPathForSegment(self, path, segmentIndex):
    return map(self._mapFromLocalToScene, self._pointsLCSInPathForSegment(path, segmentIndex))
  
    
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
    for segmentIndex in self._segmentIndexGenerator():
      segment = self._getSegmentAt(segmentIndex)
      for controlPoint in segment.controlPointIter():
        result.append(controlPoint)
      segment.createRelations(relations=self.relations, previousEndAnchor=previousEndControlPoint)
      previousEndControlPoint = segment.getEndControlPoint()
    self.controlPointSet = result # Remember my own ControlPoint set
    # FIXME: above does NOT allow for many views of same SegmentString
    return result
  
  
  def _getSegmentAt(self, segmentIndex):
    ''' 
    Segment instance for what is described in path at segmentIndex. 
    
    !!! Expand the run-encoding of QPainterPath
    (last point of previous segment shared with first point of next segment.)
    E.G. CurveSegment requires four points from three in the path.
    '''
    #print "SegmentIndex", segmentIndex
    assert segmentIndex >= 0 and segmentIndex <= self._indexOfLastSegment()
    assert self.countSegments() > 0
    
    pointsFromPath = self._pointsSCSInPathForSegment(self.myPath(), segmentIndex)
    # assert points are Scene CS
    segment = CurveSegment(*pointsFromPath)
    # assert ControlPoints were created and refer to segment
    segment.setIndexInString(parentString=self, indexOfSegmentInString = segmentIndex)
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
    # FIXME index are confused with ordinals
    assert segmentIndex >= 0 and segmentIndex < self.countSegments()
    return self.cuspness.isCusp(segmentIndex)
    
  def setSegmentCuspness(self, segmentIndex):
    self.cuspness.setCuspness(segmentIndex)


  
