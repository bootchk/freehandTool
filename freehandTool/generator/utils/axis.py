'''
Copyright 2013 Lloyd Konneker

This is free software, covered by the GNU General Public License.
'''
from copy import copy

from .orthogonal import areOrthogonal, areVerticallyAligned, areHorizontallyAligned
from ...logger import logger


class Axis():
  '''
  States:
  - only self.startPosition known, self.orientation is not known (only one point received)
  - self.orientation is known (at least two points received.)
  
  Responsibilities:
  - know startPosition
  - determine and know three valued orientation: horizontal ('H'), vertical('V'), or None (unknown)
  - determine whether position is diagonal to self (off-axis)
  - determine position's value along axis (project)
  '''
  
  def __init__(self):
    self.orientation = None
    self.startPosition = None
    
    
  def reset(self, startPosition):
    ''' Position determines startPosition, but not orientation. '''
    self.orientation = None
    # !!! Copy to prevent aliasing bugs
    self.startPosition = copy(startPosition)
  
  
  def resetStartPosition(self, newStartPosition):
    ''' Reset startPosition but keep orientation '''
    assert self.isOnKnownAxis(newStartPosition)
    self.startPosition = newStartPosition
    
  
  '''
  Determine and know orientation
  '''
  def isOrientationKnown(self):
    return self.orientation is not None
    
  
  def tryDetermineOrientation(self, position):
    ''' Attempt to determine orientation from an aligned position (even startPosition.) '''
    if position == self.startPosition:
      return
    else:
      self.determineOrientation(position)
      
  def determineOrientation(self, position):
    ''' Definitely determine orientation from a position that is not the same as startPosition and is not diagonal to startPosition. '''
    assert not self.isOrientationKnown(), 'Should only be determined once'
    assert self.startPosition is not None
    assert self.startPosition != position, 'Cannot determine axis.orientation from same as start.'
    if areHorizontallyAligned(self.startPosition, position):
      self.orientation = 'H'
    elif areVerticallyAligned(self.startPosition, position):
      self.orientation = 'V'
    else:
      raise RuntimeError('Cannot determine axis.orientation from diagonal points.')
    logger.debug('determine returns %s', str(self.orientation))
    assert self.isOrientationKnown()
    
    
  def isHorizontal(self):
    return self.orientation == 'H'
  
  def isVertical(self):
    return self.orientation == 'V'
  
  

  def onAxisValue(self, position):
    ''' 
    Position's value on axis.
    assert position is on axis (not diagonal to self.startPosition)
    '''
    assert self.isOrientationKnown()
    if self.isHorizontal():
      result = position.x()
      assert position.y() == self.startPosition.y(), str(position.y()) + ':' + str(self.startPosition.y())
    else:
      assert self.isVertical()
      result = position.y()
      assert position.x() == self.startPosition.x(), str(position.x()) + ':' + str(self.startPosition.x())
    return result
  
  
  '''
  Determine whether position is diagonal to self (off-axis)
  '''
  
  def isPositionDiagonal(self, position):
    ''' 
    Is position diagonal to self in extended sense:
    not on known axis
    OR when axis.orientation is not known, diagonal to startPosition.
    
    When orientation is not known, a position orthogonal to startPosition is not diagonal.
    '''
    assert self.startPosition is not None
    if self.isOrientationKnown():
      result = not self.isOnKnownAxis(position)
    else:
      result = self.isDiagonalToStart(position)
    logger.debug("isPositionDiagonal %s returns %s", str(position), str(result))
    return result

  def isDiagonalToStart(self, position):
    return not areOrthogonal(self.startPosition, position)
  
  def isOnKnownAxis(self, position):
    assert self.isOrientationKnown()
    if self.isHorizontal():
      result = areHorizontallyAligned(self.startPosition, position)
    else:
      result = areVerticallyAligned(self.startPosition, position)
    return result
  
  """
  Not used.
  
  def isOrthogonalToStart(self, position):
    ''' 
    Is position on any same axis (both on horizontal or both on vertical) as self.startPosition.
    Orientation need not be known.
    '''
    return areOrthogonal(self.startPosition, position)
  """
  
  
  

    