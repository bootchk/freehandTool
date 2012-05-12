class ControlPoint(object):
  '''
  Base class for a Model of a point of a segment that determines the segment's shape.
  CP's are not necessarily ON a segment.
  
  A user can manipulate a drawn ControlPoint to control, ie shape a segment,
  although ControlPoints are not drawables.
  A user manipulates a CP via a Viewer/Control, e.g. a ControlPointMorph or ControlArmMorph
  
  Responsibility:
  - know coordinate
  - know whether it has been traversed
  - know its parent Segment and index in same
  
  A ControlPoint does NOT know its type.
  The types are:
  - Anchor (ends)
  - Direction (ends of control arms)
  
  FIXME most of what follows is not implemented yet.
  
  The type is a role, defined by relations among ControlPoints.
  The role of a ControlPoint is not explicitly modeled, only modeled by relations between ControlPoints.
  
  A ControlPoint plays the Anchor role if:
  - it is ArmTo related (paired with a Direction CP)
  - AND it is OppositeTo related (paired with an opposite Anchor CP)
  A ControlPoint playing the Anchor role MAY be TiedTo related (to an Anchor of an adjoining segment)
  unless it is the starting or ending Anchor of a PolySegment.
  
  A ControlPoint plays the Direction role if:
  - it is ArmTo related 
  - AND has no other relations
  
  We do it this way for flexibility of design:
  the relations form a network or graph that helps define the behavior when user drags ControlPoints.
  A drag behavior is defined by a traversal method of the relations network.
  '''
  
  def __init__(self, parentSegment, indexInParent):
    self.coordinate = None
    self.isTraversed = False
    self.parentSegment = parentSegment
    self.indexInParent = indexInParent
  
  
  def getCoordinate(self):
    return self.coordinate
  
  def setCoordinate(self, coordinate):
    ''' 
    Set initial, undrawn coordinate.
    This does NOT update the drawing: see updateCoordinate()
    '''
    self.coordinate = coordinate
                            
  def updateCoordinate(self, deltaCoordinate):
    ''' Set coordinate and update '''
    self.setCoordinate(self.getCoordinate() + deltaCoordinate)
    self.parentSegment.controlPointChanged(self.indexInParent)
    
    
  def isTraversed(self):
    return self.isTraversed
  

