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
    - uses three turns (input objects): history.start, history.end, and current.
    - on startup, history.isCollapsed()
    - updates history.end every iter, instead of on send().
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
        #line = self.smallestLineFromPath(turnHistory.end, newTurn) # TEST 
        
        ##if positionElapsedTime > LineGeneratorMixin.MAX_POINTER_ELAPSED_FOR_SMOOTH:
        if isForced:
          self._flushUpToNewTurn(newTurn, turnHistory)
          # assert turnHistory was updated by _flushUpToNewTurn()
        else:
          line = self._lineFromPath(turnHistory, newTurn, self.constraints) # ,directions)
          if line is not None:  # if newTurn not satisfied by vector
            self.curveGenerator.send((line, False))
            # self.labelLine(str(positionElapsedTime), newTurn)
            turnHistory.roll()
            turnHistory.updateEnd(newTurn)
            # sent a pathLine to oldHistory.end, new turnHistory is (oldHistory.end, newTurn)
          else: # current path (all turns) still satisfied by a PathLine.
            # Don't send any lines, but discard intermediate turns
            turnHistory.updateEnd(newTurn)
            # new turnHistory is (oldHistory.start, newTurn)
          
          '''
          Cannot assert not turnHistory.isCollapsed():
          Diagonal jitter may send consecutive turns ending where we started (without violating constraints.)
          '''
        
    except Exception:
      # !!! GeneratorExit is a BaseException, not an Exception
      logger.critical( "Unexpected exception")  # Program error
      traceback.print_exc()
      raise
    except GeneratorExit:
      self.flushLineGenerator(turnHistory)  # self is FreehandTool having three generators with distinctly named flush methods
      
      
  def _flushUpToNewTurn(self, newTurn, turnHistory):
    '''
    Flush self from history up to newTurn.
    
    User paused, send a forced PathLine which subsequently makes cusp-like graphic
    Effectively, eliminate pipeline lag by generating a LinePathElement.
    '''
    forcedLine = self._forcedLineFromPath(turnHistory, newTurn, self.constraints)
    # _forcedLineFromPath revised turnHistory
    self._sendForcedLine(forcedLine)
    ##print("Forced line")
    ## For debug: self.labelLine("F" + str(positionElapsedTime), newTurn)
    
  
  def flushLineGenerator(self, turnHistory):
    ''' 
    The only case where turnHistory isCollapsed()==True is the case where we never generated any PathLines. 
    IOW, the 'if branch' below is taken for all but that rare case.
    '''
    logger.debug("flush")
    if not turnHistory.isCollapsed():
      ''' Have turn not sent. Fabricate a PathLine and send() it now. '''
      self._sendForcedLine(PathLine(turnHistory.start, turnHistory.end))
    else:
      ''' Cause CurveGenerator to generate a segmment to turnHistory.end Turn, which is the end of the PointerTrack.'''
      self._sendForcedLine(PathLine.nullPathLine(turnHistory.end))
    # Assert sent exactly one forcing line.
      
      
  def _sendForcedLine(self, line):
    '''
    Encapsulates how to send a forced line:
    - send a tuple where 2nd element is True.
    '''
    logger.debug("sendForcedLine")
    self.curveGenerator.send((line, True))
    
  
  def _smallestLineFromPath(self, turn1, turn2):
    ''' For TESTING: just emit a vector regardless of fit. '''
    return PathLine(turn1, turn2)
  
  
  def _lineFromPath(self, history, currentTurn, constraints, directions=None):
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
    vectorViaAllTurns = currentTurn - history.start
      
    if constraints.isViolatedBy(vector=vectorViaAllTurns):
      logger.debug("Line for constraint violation") # , constraints, "vector", vectorViaAllTurns
      result = self._interpolateConstraintViolating(history, firstNonsatisfingTurn=currentTurn)
      # reset
      constraints.__init__()
      # directions.reset()
    else:
      constraints.update(vectorViaAllTurns)
      result = None # Defer, until subsequent corner
    return result
    
    
  def _forcedLineFromPath(self, history, currentTurn, constraints, directions=None):
    ''' 
    PathLine that forces to currentTurn, regardless of constraints. 
    Note returns a PathLine, not a LinePathElement.
    '''
    constraints.__init__()
    
    if history.start == currentTurn:
      '''
      A reversal in the turns.
      A line from start to current isNull.
      We must send some line (to flush/force CurveGenerator).
      One alternative is to send a NullPathLine (but that loses the move to history.end, which hopefully is just jitter.)
      Another alternative  is to send two lines (with the second being forcing.)
      Note that this does not catch all reversals in turns: history.end might not be the extreme turn.
      '''
      logger.debug("Reversal in turns")
      """
      assert not history.isCollapsed(), 'No consecutive forces'
      result = PathLine(history.start, history.end)
      logger.debug( "Force PathLine %s %s", str(history.start), str(history.end))
      history.roll()
      """
      result = PathLine.nullPathLine(currentTurn)
      history.collapse(currentTurn)
    else: # Current turn is different from history.start
      # Better to send two lines??
      result = PathLine(history.start, currentTurn)
      logger.debug( "Force PathLine %s %s", str(history.start), str(currentTurn))
      history.collapse(currentTurn)
    # Forcing makes history collapsed on the currentTurn.
    assert history.isCollapsed()
    assert history.end == currentTurn
    return result
    
    
  def _interpolateConstraintViolating(self, history, firstNonsatisfingTurn):
    '''
    Interpolate precise violating pixel position
    Return a PathLine.
    
    This version simply returns PathLine to lastSatisfyingTurn (a null interpolation.)
    potrace does more, a non-null interpolation.
    '''
    # history.end is the last satisfying turn
    return PathLine(history.start, history.end)
  
  