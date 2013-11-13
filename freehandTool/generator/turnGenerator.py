'''
Copyright 2012 Lloyd Konneker

This is free software, covered by the GNU General Public License.
'''
import logging

from PyQt5.QtCore import QTime

from .utils.history import History
from .utils.reversalDetector import ReversalDetector

logger = logging.getLogger(__name__)  # module level logger
logger.setLevel(level=logging.DEBUG)


class TurnGeneratorMixin(object):
  '''
  Method name is capitalized because method *appears* to be a class.
  '''
  
  def TurnGenerator(self, initialPosition):
    '''
    Freehand send()'s PointerPosition when user moves graphics pointer.
    A Turn is a position between lines that lie on a axis (vertical or horizontal).
   
    This is agnostic of int versus real, with no loss of precision.
    Typically, in int.
    
    Qt doesn't have event.time . Fabricate it here.  X11 has event.time.
    
    close() may come before the first send() e.g if user just clicks pointer without moving it.
    '''
    history = History(initialPosition)
    
    positionClock = QTime.currentTime()  # note restart returns elapsed
    positionClock.restart()
    # I also tried countPositionsSinceTurn to solve lag for cusp-like
    
    self.reversalDetector = ReversalDetector(initialPosition)
    
    try:
      while True:
        newPosition = (yield) # 2nd entry point of this coroutine
        positionElapsedTime = positionClock.restart()
        ##turn = self.detectTurn(history.end, newPosition)
        # !!! not assert newPosition is different from any prior position, including initialPosition
        turn = self.detectTurn(newPosition)
        if turn is not None:
          self.lineGenerator.send((turn, positionElapsedTime))
          history.collapse(newPosition)
        else: # path is still on an axis with history.end: wait
          history.updateEnd(newPosition)
    # Not catching general exceptions, have not found a need for it.
    except GeneratorExit:
      self.flushTurnGenerator(history)
      
      
  def detectTurn(self, position):
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
    
  
    
  def flushTurnGenerator(self, history):
    logger.debug("Flush")  
    if not history.isCollapsed():
      ''' Have position not sent. Send a turn at last known position. '''
      self.lineGenerator.send((history.end, 0)) # force a Turn 

