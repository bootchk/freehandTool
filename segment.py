'''
FreehandTool understands straight segments and curved segments,
but PolySegment represents both by the mathematical abstraction *curve*
(although curves for straight lines are created straight.)
User can subsequently manipulate segments the same way,
regardless of their curvature (straight or curved.)
This is a UI design decision.
'''



from controlPoint import ControlPoint
## from relation import import relations

class Segment(object):
  '''
  Base class for segments of a PolySegment.
  
  Responsibilities:
  - produce representation as sequence of points
  - know index in parent
  - create ControlPoints and Relations between them
  - know relations between ControlPoints
  - know endPoint
  '''
  
  def __init__(self):
    self.indexInParent = None
    # Every segment has FOUR ControlPoints
    self.controlPoints = [ControlPoint(), ControlPoint(), ControlPoint(), ControlPoint()]
    
    
  def __repr__(self):
    return ','.join([str(controlPoint.getCoordinate()) for controlPoint in self.controlPoints])


  def asPoints(self):
    '''
    Representation as tuple of coordinates of self ControlPoints.
    
    Tuple of points is compatible with Qt QPainterPath API.
    '''
    return [controlPoint.getCoordinate() for controlPoint in self.controlPoints]
  
  
  def setIndex(self, indexInParent):
    self.indexInParent = indexInParent
    
  def getIndex(self):
    return self.indexInParent
  
  
  def createRelations(self):
    '''
    Set relations.
    Standard relations between control points of a Bezier curve.
    Anchor of one segment TieTo to anchor of next segment.
    Left anchor ArmTo left direction, similarly for right.
    Left anchor OppositeTo right anchor.
    '''
    #relations.relate(self.controlPoints[0], self.controlPoints[1], "TieTo")
    # WORK IN PROGRESS
    pass
    
  def getEndPoint(self):
    ''' Self end point is self last ControlPoint. '''
    return self.controlPoints[3].getCoordinate()
  
    
class LineSegment(Segment):
  '''
  Line specialization of Segment.
  
  Additional responsibilities:
  - hide that we represent lines by curves, by fabricating direction control points
  (where none are mathematically needed to represent a straight line.)
  '''
  def __init__(self, startPoint, endPoint):
    super(LineSegment, self).__init__()
    # Set coordinates of anchor ControlPoints, at ends
    self.controlPoints[0].setCoordinate(startPoint)
    self.controlPoints[3].setCoordinate(endPoint)
    '''
    Compute and set coordinates of direction ControlPoints
    Interpolate.
    For now, use the midpoint for both direction ControlPoints.
    FUTURE divide in thirds.
    '''
    midpoint = (endPoint - startPoint) / 2
    self.controlPoints[1].setCoordinate(midpoint)
    self.controlPoints[2].setCoordinate(midpoint)


class CurveSegment(Segment):
  '''
  Curve specialization of Segment.
  
  All control points must be passed.
  '''
  def __init__(self, startPoint, controlPoint1, controlPoint2, endPoint):
    super(CurveSegment, self).__init__()
    # Set coordinates of anchor ControlPoints, at ends
    self.controlPoints[0].setCoordinate(startPoint)
    self.controlPoints[1].setCoordinate(controlPoint1)
    self.controlPoints[2].setCoordinate(controlPoint2)
    self.controlPoints[3].setCoordinate(endPoint)