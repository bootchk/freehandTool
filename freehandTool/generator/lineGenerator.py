'''
Copyright 2012 Lloyd Konneker

This is free software, covered by the GNU General Public License.
'''
import traceback
import logging

from ..type.pathLine import PathLine
from .utils.constraints import Constraints
from .utils.history import History

logger = logging.getLogger(__name__)  # module level logger
logger.setLevel(level=logging.DEBUG)


class LineGeneratorMixin(object):
  
  def LineGenerator(self, initialPosition):
    '''
    Generate PathLine sequence from Turn sequence.
    Takes pointer Turn on explicit call to send().
    Consumes Turns until pixels of PointerPath cannot be approximated by (impinged upon by) one vector.
    Generates PathLines (vectors on integer plane (grid)), not necessarily axial, roughly speaking: diagonals.
    
    Note structure of this filter differs from others:
    - uses three turns (input objects): start, previous, and current.
    - on startup, previousTurn and startTurn are same
    - rolls forward previousTurn every iter, instead of on send().
    '''
    turnHistory = History(initialPosition)
    self.constraints = Constraints()
  
    # directions = Directions()
    #turnClock = QTime.currentTime()  # note restart returns elapsed
    #turnClock.restart()
    try:
      while True:
        newTurn, isForced = (yield)  # 2nd entry point of this coroutine
        #turnElapsedTime = turnClock.restart()
        #logger.debug("Turn elapsed %d", turnElapsedTime)
        #line = self.smallestLineFromPath(previousTurn, turn) # TEST 
        
        ##if positionElapsedTime > LineGeneratorMixin.MAX_POINTER_ELAPSED_FOR_SMOOTH:
        if isForced:
          self._sendForcedLine(newTurn, turnHistory)
          # assert turnHistory was updated by _sendForcedLine()
        else:
          line = self._lineFromPath(turnHistory.start, turnHistory.end, newTurn, self.constraints) # ,directions)
          if line is not None:  # if newTurn not satisfied by vector
            self.curveGenerator.send((line, False))
            # self.labelLine(str(positionElapsedTime), newTurn)
            turnHistory.roll()
        
          # else current path (all turns) still satisfied by a PathLine: wait
          turnHistory.updateEnd(newTurn)
          
          '''
          If sent a pathLine to oldHistory.end, new turnHistory is (oldHistory.end, newTurn)
          Else new turnHistory is (oldHistory.start, newTurn) i.e. discarded intermediate Turns.
          '''
          assert not turnHistory.isCollapsed()
        
    except Exception:
      # !!! GeneratorExit is a BaseException, not an Exception
      logger.critical( "Unexpected exception")  # Program error
      traceback.print_exc()
      raise
    except GeneratorExit:
      self.flushLineGenerator(turnHistory)  # self is FreehandTool having three generators with distinctly named flush methods
      
      
  def _sendForcedLine(self, newTurn, turnHistory):

    # User paused, send a forced PathLine which subsequently makes cusp-like graphic
    # Effectively, eliminate generation lag by generating a LinePathElement.
    forcedLine = self._forceLineFromPath(turnHistory.start, turnHistory.end, newTurn, self.constraints)
    self.curveGenerator.send((forcedLine, True))
    ##print("Forced line")
    ## For debug: self.labelLine("F" + str(positionElapsedTime), newTurn)
    turnHistory.roll()
    
  
  def flushLineGenerator(self, turnHistory):
    ''' 
    The only case where turnHistory isCollapsed()==True is the case where we never generated any PathLines. 
    IOW, the 'if branch' below is taken for all but that rare case.
    '''
    logger.debug("flush")
    if not turnHistory.isCollapsed():
      ''' Have turn not sent. Fabricate a PathLine and send() it now. '''
      self.curveGenerator.send((PathLine(turnHistory.start, turnHistory.end), False))
      
    ''' Cause CurveGenerator to generate a segmment to turnHistory.end Turn, which is the end of the PointerTrack.'''
    self.curveGenerator.send((PathLine.nullPathLine(turnHistory.end), False))
      
    
  
  
  def _smallestLineFromPath(self, turn1, turn2):
    ''' For TESTING: just emit a vector regardless of fit. '''
    return PathLine(turn1, turn2)
  
  
  def _lineFromPath(self, startTurn, previousTurn, currentTurn, constraints, directions=None):
    '''
    Fit a vector to an integer path.
    If no one vector fits path (a pivot): return vector and start new vector.
    Otherwise return None.
    
    Generally speaking, this is a "line simplification" algorithm (e.g. Lang or Douglas-Puecker).
    Given an input path (a sequence of small lines between pointer turns.)
    Output a longer line that approximates path.
    More generally, input line sequence are vectors on a real plane, here they are vectors on a integer plane.
    More generally, there is an epsilon parameter that defines goodness of fit.
    Here, epsilon is half width of a pixel (one half.)
    
    A vector approximates a path (sequence of small lines between pointer turns) until either:
    - path has four directions
    - OR constraints are violated.
    
    Any turn can violate constraints, but more precisely,
    constraint is violated between turns.
    A series of turns need not violate a constraint.
    Only check constraints at each turn,
    then when constraints ARE violated by a turn,
    calculate exactly which PointerPosition (between turns) violated constraints.
    '''
    '''
    I found that for PointerTracks, this happens so rarely it is useless.
    Only useful for traced bitmap images?
    
    directions.update(previousTurn, currentTurn)
    if len(directions) > 3:
      # a path with four directions can't be approximated with one vector
      # end point is starting pixel of segment ???
      #logger.debug("Four directions")
      self.resetLineFittingFilter()
      # Note end is previousTurn, not current Turn
      return PathLine(startTurn, previousTurn)
    else:
    '''
    # Vector from startTurn, via many turns, to currentTurn
    vectorViaAllTurns = currentTurn - startTurn
      
    if constraints.isViolatedBy(vector=vectorViaAllTurns):
      logger.debug("Line for constraint violation") # , constraints, "vector", vectorViaAllTurns
      result = self._interpolateConstraintViolating(startTurn=startTurn,
         lastSatisfyingTurn=previousTurn,
         firstNonsatisfingTurn=currentTurn)
      # reset
      constraints.__init__()
      # directions.reset()
    else:
      constraints.update(vectorViaAllTurns)
      result = None # Defer, until subsequent corner
    return result
    
    
  def _forceLineFromPath(self, startTurn, previousTurn, currentTurn, constraints, directions=None):
    ''' 
    Force a PathLine to currentTurn, regardless of constraints. 
    Note this is a PathLine, not a LinePathElement.
    '''
    constraints.__init__()
    
    if startTurn == currentTurn:
      ''' A reversal. A line from start to current would be Null. '''
      logger.debug("Reversal")
      assert previousTurn != startTurn
      result = PathLine(startTurn, previousTurn)
    else:
      result = PathLine(startTurn, currentTurn)
    logger.debug( "Force PathLine %s %s", str(startTurn), str(currentTurn))
    return result
    
    
  def _interpolateConstraintViolating(self, startTurn, lastSatisfyingTurn, firstNonsatisfingTurn):
    '''
    Interpolate precise violating pixel position
    Return a PathLine.
    
    This version simply returns PathLine to lastSatisfyingTurn (a null interpolation.)
    potrace does more, a non-null interpolation.
    '''
    return PathLine(startTurn, lastSatisfyingTurn)
  
  