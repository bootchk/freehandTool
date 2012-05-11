class ControlPoint(object):
  '''
  Base class for a Model of a point of a segment that controls the segment.
  CP's are not necessarily ON a segment.
  A user controls a CP via a Viewer/Control, e.g. a ControlPointMorph and a ControlArmMorph
  
  Responsibility:
  - know coordinate
  - know whether it has been traversed
  - know its index in parent Segment
  
  A ControlPoint does NOT know its type.
  The types are:
  - Anchor (ends)
  - Direction (ends of control arms)
  
  The type is a role, defined by relations among ControlPoints.
  The role of a ControlPoint is not explicitly modeled, only modeled by relations between ControlPoints.
  
  A ControlPoint plays the Anchor role if:
  - it is ArmTo related 
  - AND it is OppositeTo related
  A ControlPoint playing the Anchor role MAY be TiedTo related,
  unless it is the starting or ending Anchor of a PolySegment.
  
  A ControlPoint plays the Direction role if:
  - it is ArmTo related 
  - AND has no other relations
  
  We do it this way for flexibility of design:
  the relations form a network or graph that helps define the behavior when user drags ControlPoints.
  A drag behavior is defined by a traversal method of the relations network.
  '''
  
  def __init__(self):
    self.coordinate = None
    self.isTraversed = False
  
  
  def getCoordinate(self):
    return self.coordinate
  
  def setCoordinate(self, coordinate):
    self.coordinate = coordinate
                            
  def isTraversed(self):
    return self.isTraversed
  

