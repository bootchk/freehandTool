'''
Copyright 2012 Lloyd Konneker

This is free software, covered by the GNU General Public License.
'''
import logging

from PyQt5.QtCore import QTime

from history import History

logger = logging.getLogger(__name__)  # module level logger
logger.setLevel(level=logging.WARNING)


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
    
    try:
      while True:
        newPosition = (yield) # 2nd entry point of this coroutine
        positionElapsedTime = positionClock.restart()
        turn = self.detectTurn(history.end, newPosition)
        if turn is not None:
          self.lineGenerator.send((turn, positionElapsedTime))
          history.collapse(newPosition)
        else: # path is still on an axis with history.end: wait
          history.updateEnd(newPosition)
    # Not catching general exceptions, have not found a need for it.
    except GeneratorExit:
      self.flushTurnGenerator(history)
      
      

  
  def detectTurn(self, position1, position2):
    ''' 
    Return position2 if it turns, i.e. if not on horiz or vert axis with position1, else return None. 
    
    !!! A diagonal pointer track that reverses (returns from whence it came) generates turns.
    That is, turns are not just left or right, but also reversal.
    
    !!! A horizontal or vertical track that reverses does not generate a turn.
    '''
    if        position1.x() != position2.x() \
          and position1.y() != position2.y()   :
      logger.debug("Turn %s", str(position2))
      return position2
    else:
      logger.debug("Not turn %s", str(position2))
      return None
    
    
  def flushTurnGenerator(self, history):
    logger.debug("Flush")  
    if not history.isCollapsed():
      ''' Have position not sent. Send a turn at last known position. '''
      self.lineGenerator.send((history.end, 0)) # force a Turn 

