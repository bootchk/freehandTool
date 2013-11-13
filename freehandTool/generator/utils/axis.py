'''
Copyright 2013 Lloyd Konneker

This is free software, covered by the GNU General Public License.
'''
import logging
from copy import copy

logger = logging.getLogger(__name__)  # module level logger
logger.setLevel(level=logging.DEBUG)


class Axis():
  '''
  States:
  - only axisStart known, axis is not known (only one point received)
  - axis is known (at least two points received.)
  
  Maintains three valued axis direction: horizontal (True), vertical(False), or None (unknown)
  '''
  def __init__(self):
    self.axis = None
    self.axisStart = None
    
    
  def reset(self, startPosition):
    ''' One position determines the start, but not the axis direction. '''
    self.axis = None
    # !!! Make copy to prevent aliasing bugs
    self.axisStart = copy(startPosition)
  
  
  def isKnown(self):
    return self.axis is not None
    
  
  def determine(self, position):
    ''' Determine my axis from a position that is not the same as axisStart. '''
    assert not self.isKnown(), 'Should only be determined once'
    assert self.axisStart is not None
    assert self.axisStart != position, 'Cannot determine axis from same as start.'
    if self.isSameHorizontalAxis(self.axisStart, position):
      self.axis = True
    elif self.isSameVerticalAxis(self.axisStart, position):
      self.axis = False
    else:
      raise RuntimeError('Cannot determine axis from diagonal points.')
    logger.debug('determine returns %s', str(self.axis))
    assert self.isKnown()
    
    
  def isHorizontal(self):
    return self.axis == True
  
  def isVertical(self):
    return self.axis == False
  
  
  def onAxisValue(self, position):
    ''' 
    Position's value on axis.
    assert position is on axis (not diagonal to self.axisStart)
    '''
    assert self.isKnown()
    if self.isHorizontal():
      result = position.x()
      assert position.y() == self.axisStart.y(), str(position.y()) + ':' + str(self.axisStart.y())
    else:
      assert self.isVertical()
      result = position.y()
      assert position.x() == self.axisStart.x(), str(position.x()) + ':' + str(self.axisStart.x())
    return result
  
  """
  def detectOffAxis(self, position1, position2):
    '''
    Return position2 if: not on horiz or vert axis with position1, else return None. 
    !!! A diagonal pointer track that reverses (returns from whence it came) is off-axis.
    !!! A horizontal or vertical track that reverses is NOT off-axis.
    '''
    if  not self.isSameAxis(position1, position2):
      logger.debug("Off-axis %s", str(position2))
      return position2
    else:
      logger.debug("Not Off-axis %s", str(position2))
      return None
  """
  def isDiagonalToStart(self, position):
    ''' 
    Is diagonal in extended sense:
     not on known axis
     OR when axis is not known, diagonal to start. 
     '''
    assert self.axisStart is not None
    if self.isKnown():
      result = self.isOnKnownAxis(position)
    else:
      result = self.isAnySameAxis(self.axisStart, position)
    return result
  
  def isSameHorizontalAxis(self, position1, position2):
    ''' same horizontal axis implies y()'s are same. '''
    return position1.y() == position2.y()
  
  def isSameVerticalAxis(self, position1, position2):
    return position1.x() == position2.x()

  def isAnySameAxis(self, position1, position2):
    ''' Are both positions on any same axis (both on horizontal or both on vertical) '''
    return self.isSameHorizontalAxis(position1, position2) or self.isSameVerticalAxis(position1, position2)

  def isOnKnownAxis(self, position):
    assert self.isKnown()
    if self.isHorizontal(position):
      result = self.isSameHorizontalAxis(self.axisStart, position)
    else:
      result = self.isSameVerticalAxis(self.axistStart, position)
    return result
  
  """              
  def isOnAxis(self, position):
    ''' Is position on any same axis (both on horizontal or both on vertical) as self.startPosition. '''
    return self.isAnySameAxis(self.axisStart, position)
  """
    
# singleton
axis = Axis()