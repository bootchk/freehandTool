'''
Copyright 2013 Lloyd Konneker

This is free software, covered by the GNU General Public License.
'''

from copy import copy

from .turnDetector import TurnDetector
from ..utils.axis import Axis
from ...logger import logger



class ReverseDetector(TurnDetector):
  '''
  See super.
  
  This subclass, like sibling SimpleTurnDetector, detects a turn when a position is off horizontal or vertical axis.
  But it also detects a turn when a stream of positions stays on an axis but reverses.
  
  Unlike sibling SimpleTurnDetector, this subclass maintains its own knowledge of history (knows an axis.)
  (Thus it ignores the referencePosition parameter.)
  It resets itself when a turn is detected.
  
    Maintain a growing, linear limit pair along the axis.
  As long as each new position is near one of the limits, returns None.
  When a new position is a reversal (a certain distance inside the limits), returns limit that was reversed from.
  Ignores jitter (reversals less than the certain distance.)
  
  Unlike sibling SimpleTurnDetector, if a position is is detected as a reversal turn,
  the position returned is not the input newPosition, but the limit that was reversed from.
  '''
  
  def __init__(self, initialPosition):
    self.axis = Axis()
    self._resetToAxisUnknown(initialPosition)
    
  def dumpState(self):
    print("lower " + str(self.lowerLimit) + " upper " + str(self.upperLimit) )
    print("extreme " + str(self.extremePosition) + " isGrowingLower", str(self.isGrowingLower))
    
  def _resetToAxisUnknown(self, newStartPosition):
    logger.debug("_resetToAxisUnknown %s", str(newStartPosition))
    self._resetGrowthParameters()
    self.axis.reset(newStartPosition)
    # Can't 'assert self._size() == 1' because limits are None
  
  
  def _resetAfterReversal(self, newPosition):
    '''
    A reversal has been detected.
    
    Reset self so that initialPosition is the old extremePosition
    and newPosition is the first move away from extremePosition.
    
    self.axis keeps orientation but self.axis.startDirection is reset
    growth direction flips.
    '''
    assert self.extremePosition != newPosition
    oldExtremePosition = copy(self.extremePosition)
    self.axis.resetStartPosition(newStartPosition = self.extremePosition)
    self._flipGrowth()
    self._setInitialLimits(newPosition) # sets new self.extremePosition
    assert oldExtremePosition != self.extremePosition
    # Can't call 'self.detect(newPosition=newPosition)' because its an infinite loop
    # assert size > 1
    
  '''
  Growth along axis.
  '''
  def _resetGrowthParameters(self):
    ''' None means undetermined. '''
    self.lowerLimit = None
    self.upperLimit = None
    self.isGrowingLower = None
    self.extremePosition = None


  def _flipGrowth(self):
    ''' A reversal has been detected: now growing in opposite direction along the axis. '''
    assert self.isGrowingLower is not None
    self.isGrowingLower = not self.isGrowingLower
    
    
  def _size(self):
    return self.upperLimit - self.lowerLimit + 1
  
  def isDirectionKnown(self):
    return self.isGrowingLower is not None

  def detect(self, newPosition, referencePosition=None):
    ''' 
    newPosition if it is diagonal to axis
    OR a limit position if newPosition reverses along axis
    OR None
    '''
    if self.axis.isPositionDiagonal(newPosition):
      result = newPosition
      self._resetToAxisUnknown(newPosition)
    else:
      result = self.detectReversal(newPosition)
      if result is not None: 
        assert result == self.extremePosition
        self._resetAfterReversal(newPosition=newPosition)
    # WRONG assert result is None or result==newPosition or result==self.oldupperLimit or result==self.lowerLimit
    return result
  
  
  def detectReversal(self, newPosition):
    '''
    Extreme historical position on axis if newPosition is more than 2 pixels away from limits.
    
    If reversal: limit that was reversed from, and reset
    Else: none, and grow.
    '''
    assert not self.axis.isPositionDiagonal(newPosition)
    # Cannot assert self.axis.isOnKnownAxis(): newPosition could be equal to self.axis.startPosition
    
    if not self.axis.isOrientationKnown():
      self.axis.tryDetermineOrientation(newPosition)
      # If startPosition == newPosition, still not self.axis.isOrientationKnown()
      if self.axis.isOrientationKnown():
        # We just determined orientation, also determine limits
        self._setInitialLimits(newPosition)
      
    if not self.axis.isOrientationKnown():
      result = None
    else:
      # axis orientation is known and limits are known but direction may not be known
      onAxisValue = self.axis.onAxisValue(newPosition)
      self._expandLimits(onAxisValue, newPosition)
      if self.isDirectionKnown():
        ## onAxisValue = self._tryOnAxisValue(newPosition)
        if self._isReverse(onAxisValue, newPosition=newPosition):
          result = self.extremePosition
        else:
          result = None
      else:
        result = None
    logger.debug("detectReversal %s returns %s", str(newPosition), str(result))
    return result
  
  """
  # TODO assert self.axis.isOrientationKnown()
  def _tryOnAxisValue(self, position):
    ''' position's value on self's axis, or None. '''
    if not self.axis.isOrientationKnown():
      if self.startPosition == position:
        # No axis determinable yet
        result = None
      else:
        self.axis.determineOrientation(position)
        assert self.axis.isOrientationKnown()
        self._setInitialLimits(position)
        result = self.axis.onAxisValue(position)
    else:
      result = self.axis.onAxisValue(position)
    return result
  """
    
    
  def _setInitialLimits(self, position):
    '''
    Two separate positions (self.axis.startPosition and position) are just now known.
    Establish limits from them, on the axis they share.
    The distance between the points is >=2.
    '''
    assert self.axis.isOrientationKnown()
    assert self.axis.isOnKnownAxis(position)
    if self.axis.isVertical():
      # x's are same, limits are y
      if self.axis.startPosition.y() < position.y():
        self.lowerLimit = self.axis.startPosition.y()
        self.upperLimit = position.y()
      else:
        self.lowerLimit = position.y()
        self.upperLimit = self.axis.startPosition.y()
    else:
      # y's are same, limits are x
      if self.axis.startPosition.x() < position.x():
        self.lowerLimit = self.axis.startPosition.x()
        self.upperLimit = position.x()
      else:
        self.lowerLimit = position.x()
        self.upperLimit = self.axis.startPosition.x()
    self.extremePosition = position # TODO do we also know direction?
    assert self.lowerLimit is not None and self.upperLimit is not None and self.lowerLimit != self.upperLimit
    
    
  def _isReverse(self, onAxisValue, newPosition):
    # axis and limits are known
    assert self._size() > 1
    if self._size() == 2:
      # not enough size to detect reversals
      result = False
    else:
      # size > 2, enough to detect reversals
      result = self._isReversal(onAxisValue)
    return result
  
  """
  def _adjustLimitsOrReverse(self, newPosition):
    # axis and limits are known
    assert self._size() > 1
    onAxisValue = self.axis.onAxisValue(newPosition)
    if self._size() == 2:
      # not enough size to detect reversals
      result = False
    else:
      # size > 2, enough to detect reversals
      result = self._isReversal(onAxisValue)
    self._expandLimits(onAxisValue, newPosition=newPosition)
    return result
  """
  
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
      # assert size >= 3, self.isGrowingLower is not None
      # assert if newPosition set a new limit, self.extremePosition = newPosition
    else:
      # newPosition is contained in limits
      pass
    # self.isGrowingLower may still be None
    
  
  def _isReversal(self, value):
    assert self.isGrowingLower is not None, 'Cannot check for reversal if direction not known'
    result = False
    if self.isGrowingLower:
      if value > self.lowerLimit + 1:
        result = True
    else: # self.isGrowingLower == False
      if value < self.upperLimit - 1:
        result = True
    
    ##if result == True:
    ##  self.dumpState()
    logger.debug("_isReversal %s returns %s", str(value), str(result))
    return result
      
      
  
    
    
    