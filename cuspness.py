
class Cuspness(object):
  '''
  A cache of cuspness.
  
  Cuspness is a property between two adjacent segments in a string.
  Cuspness is the opposite of colinear.
  Ends of a SegmentString are NOT cusps (although the GUI can make them behave the same as cusps.)
  
  NOT a property of a single segment.
  However, we store cuspness by the index of a segment in a SegmentString.
  The cuspness property is at the last Anchor ControlPoint of the segment.
  TODO first?
  
  Cuspness CAN be computed on the fly.
  This is a cache, storing cuspness when we know whether is exists at SegmentString creation time.
  FIXME: The cache should be updated when a user moves controlPoints, possibly changing cuspness.
  For now, if it is a cusp at creation time, it always behaves like a cusp,
  even if user moves a ControlPoint so cuspness is removed.
  
  Implementation:
  Every segment is NOT a cusp unless it is in the dictionary.
  '''
  def __init__(self):
    self.cuspness = {}
    
  def setCuspness(self, index):
    self.cuspness[index]=1
    
  def clearCuspness(self, index):
    del self.cuspness[index]
    
  def isCusp(self, index):
    return index in self.cuspness
  
  def computeCuspness(self, index):
    ''' Use geometry to calculate whether is cusp. '''
    # FIXME:
    return False
