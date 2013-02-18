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



FIXME:
======

Using indexes into QPainterPath as ID of Segment instances is fragile.
It currently depends on all segments being the same type having the same count of elements in QPP.

Cuspness deserialized.
'''

from PySide.QtGui import QGraphicsPathItem, QPainterPath
from PySide.QtCore import QPointF, QPoint

from segment import CurveSegment
from relations import Relations
from segmentActions import segmentStringActions
from cuspness import Cuspness
from alternatePaintingQGPI import AlternateColorPaintingQGPI

  
# For testing use: class SegmentString(AlternateColorPaintingQGPI, QGraphicsPathItem):
class SegmentString(QGraphicsPathItem):
  '''
  GraphicsItem that is a sequence of Segments.
  
  Segments are line-like curves.

  Segments don't have their own transform.
  Change their appearance by moving their control points.
  When user drags control points, comes here as segmentChanged().
  
  Responsibilities:
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
  
  def __init__(self):
    super(SegmentString, self).__init__()
    self.actions = segmentStringActions # singleton
    
    # The following are not necessarily serialized, but usually reconstructable upon deserialize.
    # They are only needed when GUI is displaying ControlPoints as Controls
    self.relations = Relations()
    self.cuspness = Cuspness()
    self.controlPointSet = None
    
    self.setPath(QPainterPath(self.origin()))
    # ensure: path has been set, self.path() returns "MoveTo(0,0)"
  
  
  # Inherits path()

  '''
  Responsibility: 1. know end points.
  
  !!! Note two different CS.
  '''

  def origin(self):
    '''
    Where the internal path starts, in Local CS.
    Conventionally, 0,0.
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
    
    
  def getEndPoint(self):
    ''' 
    End point of a SegmentString is:
    - coordinates of its last element, in VCS
    - OR startingPoint if has no Segments
    '''
    return self._pointForPathElement(element = self.path().elementAt(self.path().elementCount() - 1))
  
  def getStartPoint(self):
    ''' 
    Start point of a SegmentString is:
    - first element, regardless if has any Segments
    - in VCS
    '''
    return self._pointForPathElement(element = self.path().elementAt(0))

  
  
  '''
  Responsibility: 7. map between representations
  '''
  def _pointForPathElement(self, element):
    '''
    Return  QPointF in VCS for QPathElements.
    QPathElements don't have x(); calling it gives symptom "Exception: reverse not implemented"
    
    Also map from Local CS (of the QGraphicsItem) to View CS (of the tool)
    '''
    return self._mapFromLocalToDevice(self._unmappedPointForPathElement(element))
  
  def _unmappedPointForPathElement(self, element):
    ''' Point in LCS for element. '''
    return QPointF(element.x, element.y)
  
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
  
  
  def appendInternalRepr(self, path, pointsLCS):
    '''
    Append internal repr of segment for given pointsLCS.
    
    !!! This is the only place where we know that internal repr is cubicTo (even for straight lines.)
    !!! The fact that cubicTo has 3 points and Segment has 4 points is spread in the code.
    '''
    path.cubicTo(*pointsLCS)
  
  
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
    
    !!! All segments encoded by QPathElement of ElementType:cubic i.e. curve
    !!! Cubic only wants the final three ControlPoints.
    '''
    pointsVCS = segment.asPoints()[1:]
    # !!! Python map() and Qt 'map' meaning transform between coordinate systems
    pointsLCS = map(self._mapFromDeviceToLocal, pointsVCS)
    self.appendInternalRepr(path, pointsLCS)
    
  
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
    pointsLCS = self._pointsLCSInPathForSegment(sourcePath,segmentIndex)
    self.appendInternalRepr(path=destinationPath, pointsLCS=pointsLCS)
  
  
  def _pointsLCSInPathForSegment(self, path, segmentIndex):
    ''' 
    Return list of QPointF for QPathElements of segment.
    Points are in LCS
    !!! This is a 3-tuple, not for creating Segment, only for creating internal repr
    '''
    result = []
    for i in range(0, SegmentString.ELEMENTS_PER_SEGMENT):
      result.append(self._unmappedPointForPathElement(element = path.elementAt(segmentIndex + i)))
    return result
    
  def _pointsVCSInPathForSegment(self, path, segmentIndex):
    return map(self._mapFromLocalToDevice, self._pointsLCSInPathForSegment(path, segmentIndex))
  
    
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
      startPoint = self._lastPointOfPriorSegment(segmentIndex)
    pointsFromPath = self._pointsVCSInPathForSegment(self.path(), segmentIndex)
    # assert points are VCS
    segment = CurveSegment(startPoint, *pointsFromPath)
    # assert ControlPoints were created and refer to segment
    segment.setIndexInParent(parent=self, indexOfSegmentInParent = segmentIndex)
    return segment
  
  def _lastPointOfPriorSegment(self, segmentIndex):
    return self._pointsVCSInPathForSegment(self.path(), segmentIndex - SegmentString.ELEMENTS_PER_SEGMENT)[-1]
  
  
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


  
