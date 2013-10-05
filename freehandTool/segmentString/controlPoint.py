
'''
Copyright 2012 Lloyd Konneker

This is free software, covered by the GNU General Public License.
'''



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
  
  A ControlPoint does NOT know its type.  (See SegmentString)
  The types are:
  - Anchor (ends of cubic curves)
  - Direction (ends of control arms)
  - Center (arcs)
  - End (ends of lines)
  '''
  
  def __init__(self, parentSegment, indexInParent):
    self.coordinate = None
    self.isTraversed = False
    self.parentSegment = parentSegment
    self.indexInParent = indexInParent
  
  
  def __eq__(self, other):
    return self.coordinate == other.coordinate
  
  
  def __hash__(self):
    ''' 
    Python3: if eq is defined, hash must be defined so object usable as key in hashable collection.
    
    indexInParent defines type? so include it in hashing.
    Otherwise two controlpoints with same coordinate hash identically.
    '''
    return hash((self.coordinate.x(), self.coordinate.y(), self.indexInParent ))
  
  
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
    
    
  def getTraversed(self):
    return self.isTraversed
  
  def setTraversed(self, value):
    self.isTraversed = value
  
  

