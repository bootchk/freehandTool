'''
Copyright 2012 Lloyd Konneker

This is free software, covered by the GNU General Public License.


FreehandTool understands straight segments and curved segments.
That is, it wants an API that offers lines and curves.
These classes give that API.

However, SegmentString represents both lines and curves 
by the mathematical abstraction *curve* as represented by a cubic spline or Bezier.
(Although curves for straight lines are created straight.)
User can subsequently manipulate segments the same way,
regardless of their curvature (straight or curved.)
This is a UI design decision.
'''

from .controlPoint import ControlPoint
from ..exception import FreehandNullSegmentError


# Relation IDs
TIED_TO = 1
OPPOSITE_TO = 2
ARM_TO = 3


class Segment(object):
  '''
  Base class for segments of a SegmentString.
  
  Responsibilities:
  - produce representation as sequence of points
  - know index in parent SegmentString
  - create ControlPoints and Relations between them (on instantiation)
  - know relations between ControlPoints and order them
  - know endPoint and whether a ControlPoint is that endPoint
  - relay controlPointChanged
  
  !!! Points are FreehandPoints, in Scene CS
  '''
  
  def __init__(self, startPoint, endPoint):
    self.parentString = None
    self.indexOfSegmentInString = None
    # Every segment has FOUR ControlPoints.  These are empty ControlPoints until subclass fills them.
    self.controlPoints = [ControlPoint(self, 0), ControlPoint(self, 1), ControlPoint(self, 2), ControlPoint(self, 3)]
    
    # comparing floats, but no need for a near() comparison
    if startPoint == endPoint:
      raise FreehandNullSegmentError
    
    
  def __repr__(self):
    return ','.join([str(controlPoint.getCoordinate()) for controlPoint in self.controlPoints])


  def isNull(self):
    ''' 
    Is segment in fact a point, a segment of zero length? 
    Float equality a problem?
    '''
    result = self.controlPoints[0] == self.controlPoints[3]
    #print "isNull", result
    return result
  
  
  def asPointsScene(self):
    '''
    Representation as tuple of coordinates of self ControlPoints,
    which are in curveGenerator's frame, which is Scene CS.
    
    Tuple of points is compatible with Qt QPainterPath API.
    '''
    return [controlPoint.getCoordinate() for controlPoint in self.controlPoints]
  
  
  def setIndexInString(self, parentString, indexOfSegmentInString):
    self.parentString = parentString
    self.indexOfSegmentInString = indexOfSegmentInString
    
  def getIndexInString(self):
    return self.indexOfSegmentInString
  
  
  def createRelations(self, relations, previousEndAnchor=None):
    '''
    Set standard relations between control points of a Bezier curve.
    
    Depends on segmentRole (Start, Middle, End)
    '''
    # Left anchor OppositeTo right anchor.
    relations.relate(self.controlPoints[0], self.controlPoints[3], OPPOSITE_TO)
    # Left anchor ArmTo left direction, similarly for right.
    relations.relate(self.controlPoints[0], self.controlPoints[1], ARM_TO)
    relations.relate(self.controlPoints[2], self.controlPoints[3], ARM_TO)
    # Anchor of previous segment (if any) TiedTo to anchor of next segment.
    relations.relate(self.controlPoints[0], previousEndAnchor, TIED_TO)
    
    
  def getEndControlPoint(self):
    ''' End point is last ControlPoint. '''
    return self.controlPoints[-1]
  
  def isLastAnchor(self, controlPoint):
    return self.getEndControlPoint() is controlPoint
  
  
  def controlPointChanged(self, controlPointIndex):
    ''' 
    Event: a control point has changed. 
    Relay to segment, i.e. update draw.
    '''
    self.parentString.segmentChanged(segment=self, indexOfSegmentInString=self.indexOfSegmentInString)
    
  def controlPointIter(self):
    ''' Iterate control points in a canonical order: start,..., end '''
    for i in range(0,4):
      yield self.controlPoints[i]
  
  
class LineSegment(Segment):
  '''
  Line specialization of Segment.
  
  Additional responsibilities:
  - hide that we represent lines by curves, by fabricating direction control points
  (where none are mathematically needed to represent a straight line.)
  '''
  def __init__(self, startPoint, endPoint):
    super(LineSegment, self).__init__(startPoint, endPoint)
    
    # Set coordinates of anchor ControlPoints, at ends
    self.controlPoints[0].setCoordinate(startPoint)
    self.controlPoints[3].setCoordinate(endPoint)
    '''
    Compute and set coordinates of direction ControlPoints
    Interpolate.
    For now, use the midpoint for both direction ControlPoints.
    FUTURE divide in thirds.
    '''
    midpoint = startPoint.interval(endPoint, 1/2.0)
    self.controlPoints[1].setCoordinate(midpoint)
    self.controlPoints[2].setCoordinate(midpoint)

  """
  def interpolatePoints(self, startPoint, endPoint):
    # TODO: this should be in a vector library
    return startPoint + (endPoint - startPoint) / 2
  """



class CurveSegment(Segment):
  '''
  Curve specialization of Segment.
  
  All control points must be passed.
  '''
  def __init__(self, startPoint, controlPoint1, controlPoint2, endPoint):
    super(CurveSegment, self).__init__(startPoint, endPoint)
    
    # Anchor ControlPoints, at ends
    self.controlPoints[0].setCoordinate(startPoint)
    self.controlPoints[3].setCoordinate(endPoint)
    # Direction controlPoints, not necessarily colinear with Anchors.
    self.controlPoints[1].setCoordinate(controlPoint1)
    self.controlPoints[2].setCoordinate(controlPoint2)
    
