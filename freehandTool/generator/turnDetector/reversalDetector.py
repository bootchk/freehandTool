'''
Copyright 2013 Lloyd Konneker

This is free software, covered by the GNU General Public License.
'''
import logging

from ..utils.axis import Axis

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
    self.axis = Axis()
    
    
  def _resetGrowthParameters(self):
    ''' None means undetermined. '''
    self.lowerLimit = None
    self.upperLimit = None
    self.isGrowingLower = None
  
  
  def reset(self, newStartPosition):
    logger.debug("reset %s", str(newStartPosition))
    self._resetGrowthParameters()
    self.axis.reset(newStartPosition)
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
    result = self.axis.isPositionDiagonal(newPosition)
    logger.debug("isDiagonal %s returns %s", str(newPosition), str(result))
    return result
  
  
  def detectTurn(self, position, referencePosition=None):
    ''' 
    Return position2 if it is diagonal to reversalDetector's start
    OR if it is a reversal from 
    
    '''
    """
    offAxisPosition = axisDeterminer.detectOffAxis(position1, position2)
    if offAxisPosition is not None:
      result = offAxisPosition
      self.reversalDetector.reset(position2)
    else:
      result = self.reversalDetector.detect(position2)
    assert result is None or result is not None
    return result
    """
    if self.reversalDetector.isDiagonal(position):
      result = position
      self.reversalDetector.reset(position)
    else:
      result = self.reversalDetector.detect(position)
      # if result is not None, reversalDetector was reset to an extreme position
    assert result is None or result is not None
    return result
  
  
  def detect(self, newPosition):
    '''
    detect a reversal
    
    Extreme historical position on same axis as startPosition if newPosition is more than FOO pixels away from limits.
    
    If reversal: limit that was reversed from, and reset
    Else: none, and grow.
    '''
    logger.debug("detect %s", str(newPosition))
    assert not self.axis.isPositionDiagonal(newPosition)
    # Cannot assert self.axis.isOnKnownAxis(): newPosition could be equal to self.axis.startPosition
    
    if not self.axis.isKnown():
      self.axis.determine(newPosition)
      # If startPosition == newPosition, still not self.axis.isKnown()
      if self.axis.isKnown():
        # We just determined axis, also determine limits
        self._setInitialLimits(newPosition)
      
    if not self.axis.isKnown():
      result = None
    else:
      # axis is known and limits are known
      ## onAxisValue = self._tryOnAxisValue(newPosition)
      onAxisValue = self.axis.onAxisValue(newPosition)
      if self._adjustLimitsOrReverse(value = onAxisValue, newPosition=newPosition):
        result = self.extremePosition
        self._resetAfterReversal(newPosition=newPosition)
      else:
        result = None
    return result
  
  """
  # TODO assert self.axis.isKnown()
  def _tryOnAxisValue(self, position):
    ''' position's value on self's axis, or None. '''
    if not self.axis.isKnown():
      if self.startPosition == position:
        # No axis determinable yet
        result = None
      else:
        self.axis.determine(position)
        assert self.axis.isKnown()
        self._setInitialLimits(position)
        result = self.axis.onAxisValue(position)
    else:
      result = self.axis.onAxisValue(position)
    return result
  """
    
    
  def _setInitialLimits(self, position):
    '''
    Two separate positions (self.axis.axisStart and position) are just now known.
    Establish limits from them, on the axis they share.
    '''
    assert self.axis.isKnown()
    assert self.axis.isOnKnownAxis(position)
    if self.axis.isVertical():
      # x's are same, limits are y
      if self.axis.axisStart.y() < position.y():
        self.lowerLimit = self.axis.axisStart.y()
        self.upperLimit = position.y()
      else:
        self.lowerLimit = position.y()
        self.upperLimit = self.axis.axisStart.y()
    else:
      # y's are same, limits are x
      if self.axis.axisStart.x() < position.x():
        self.lowerLimit = self.axis.axisStart.x()
        self.upperLimit = position.x()
      else:
        self.lowerLimit = position.x()
        self.upperLimit = self.axis.axisStart.x()
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
      
      
  
    
    
    