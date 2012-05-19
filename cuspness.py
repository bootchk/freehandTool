'''
Copyright 2012 Lloyd Konneker

This is free software, covered by the GNU General Public License.
'''


class Cuspness(object):
  '''
  A cache of cuspness.
  
  Cuspness is a property between two adjacent segments in a string.
  Cuspness is the opposite of colinear.
  A synonym is "smoothness", with opposite values, but still meaning the same property.
  
  SegmentStrings know cuspness.  Cuspness just caches it.
  
  Start and End of a SegmentString are NOT cusps (although the GUI can make them behave the same as cusps.)
  
  NOT a property of a single segment.
  However, cuspness is accessed by the index of a segment in a SegmentString.
  The cuspness property is at the last Anchor ControlPoint of the segment.
  
  An index need NOT be an ordinal.
  cuspness[0] is False.
  cuspness[1] is the cuspness of first segment.
  Typically cuspness[4] is the cuspness of second segment.
  
  Cuspness CAN be computed on the fly.
  This is a cache, storing cuspness when we know whether is exists at SegmentString creation time.
  FIXME: The cache should be updated when a user moves controlPoints, possibly changing cuspness.
  For now, if it is a cusp at creation time, it always behaves like a cusp,
  even if user moves a ControlPoint so cuspness is removed.
  
  Implementation:
  Every segment is NOT a cusp unless it is in the dictionary.
  
  Responsibility:
  -set, clear, get cuspness for a segment index
  -compute cuspness from geometry of the direction points at the end of a segment.
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
    # FIXME: or is this a SegmentString responsibility?
    return False
