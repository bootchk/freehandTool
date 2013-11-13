'''
Copyright 2013 Lloyd Konneker

This is free software, covered by the GNU General Public License.
'''
import logging

from .axis import axis

logger = logging.getLogger(__name__)  # module level logger
logger.setLevel(level=logging.DEBUG)

class ReversalDetector():
  '''
  Takes stream of positions(coordinates) on one of the two axises (horizontal or vertical.)
  Maintain a growing, linear limit pair.
  As long as each new position is near one of the limits, returns None.
  When a new position is a reversal (a certain distance inside the limits), returns limit that was reversed from.
  Ignores jitter (reversals less than the certain distance.)
  '''
  
  def __init__(self, initialPosition):
    self.reset(initialPosition)
    
    
  def _resetGrowthParameters(self):
    ''' None means undetermined. '''
    self.lowerLimit = None
    self.upperLimit = None
    self.isGrowingLower = None
  
  
  def reset(self, newStartPosition):
    logger.debug("reset %s", str(newStartPosition))
    self._resetGrowthParameters()
    axis.reset(newStartPosition)
    self.extremePosition = newStartPosition
    # assert self.size() == 1
  
  
  def _resetAfterReversal(self, newPosition):
    '''
    A reversal has been detected.
    Assert self.extremePosition != newPosition.
    Reset self so that initialPosition is the old extremePosition
    and newPosition is the first move away from extremePosition.
    '''
    self.reset(newStartPosition = self.extremePosition)
    self.detect(newPosition=newPosition)
    # TODO, a reversal means that extremePosition and newPosition are not the same point, thus assert
    # assert size > 1
    
  def _size(self):
    return self.upperLimit - self.lowerLimit + 1
  
  
  def isDiagonal(self, newPosition):
    ''' Delegate to axis. '''
    result = axis.isDiagonalToStart(newPosition)
    logger.debug("isDiagonal %s returns %s", str(newPosition), str(result))
    return result
  
  
  def detect(self, newPosition):
    '''
    detect a reversal
    
    Extreme historical position on same axis as startPosition if newPosition is more than FOO pixels away from limits.
    
    If reversal: limit that was reversed from, and reset
    Else: none, and grow.
    '''
    logger.debug("detect %s", str(newPosition))
    assert axis.isAnySameAxis(newPosition)
    # Position could be equal to axis.startPosition
    
    if not axis.isKnown():
      axis.determine(newPosition)
      # If startPosition == newPosition, still not axis.isKnown()
      if axis.isKnown():
        # We just determined axis, also determine limits
        self._setInitialLimits(newPosition)
      
    if not axis.isKnown():
      result = None
    else:
      # axis is known and limits are known
      ## onAxisValue = self._tryOnAxisValue(newPosition)
      onAxisValue = axis.onAxisValue(newPosition)
      if self._adjustLimitsOrReverse(value = onAxisValue, newPosition=newPosition):
        result = self.extremePosition
        self._resetAfterReversal(newPosition=newPosition)
      else:
        result = None
    return result
  
  """
  # TODO assert axis.isKnown()
  def _tryOnAxisValue(self, position):
    ''' position's value on self's axis, or None. '''
    if not axis.isKnown():
      if self.startPosition == position:
        # No axis determinable yet
        result = None
      else:
        axis.determine(position)
        assert axis.isKnown()
        self._setInitialLimits(position)
        result = axis.onAxisValue(position)
    else:
      result = axis.onAxisValue(position)
    return result
  """
    
    
  def _setInitialLimits(self, position):
    '''
    Two separate positions (axis.axisStart and position) are just now known.
    Establish limits from them, on the axis they share.
    '''
    assert axis.isKnown()
    assert axis.isAnySameAxis(position)
    if axis.isVertical():
      # x's are same, limits are y
      if axis.axisStart.y() < position.y():
        self.lowerLimit = axis.axisStart.y()
        self.upperLimit = position.y()
      else:
        self.lowerLimit = position.y()
        self.upperLimit = axis.axisStart.y()
    else:
      # y's are same, limits are x
      if axis.axisStart.x() < position.x():
        self.lowerLimit = axis.axisStart.x()
        self.upperLimit = position.x()
      else:
        self.lowerLimit = position.x()
        self.upperLimit = axis.axisStart.x()
    assert self.lowerLimit is not None and self.upperLimit is not None and self.lowerLimit != self.upperLimit
    
      
  def _adjustLimitsOrReverse(self, value, newPosition):
    # axis and limits are known
    assert self._size() > 1
    if self._size() == 2:
      # not enough size to detect reversals
      result = False
    else:
      # size > 2, enough to detect reversals
      result = self._isReversal(value)
    self._expandLimits(value, newPosition=newPosition)
    return result
  
  
  def _expandLimits(self, value, newPosition):
    ''' 
    Expand limits if newPosition exceeds limits.
    This is agnostic of reversals, but the newPosition was already tested for reversal.
    assert size() > 1
    '''
    if value < self.lowerLimit:
      self.lowerLimit = value
      self.isGrowingLower = True
      self.extremePosition = newPosition
    elif value > self.upperLimit:
      self.upperLimit = value
      self.isGrowingLower = False
      self.extremePosition = newPosition
      # assert size >= 3, self.extremePosition is not None, self.isGrowingLower is not None
    else:
      # newPosition is contained in limits
      pass
  
  
  def _isReversal(self, value):
    result = False
    if self.isGrowingLower:
      if value > self.lowerLimit + 1:
        result = True
    else:
      if value < self.upperLimit - 1:
        result = True
    return result
      
      
  
    
    
    