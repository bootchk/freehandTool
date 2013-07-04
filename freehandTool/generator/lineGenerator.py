'''
Copyright 2012 Lloyd Konneker

This is free software, covered by the GNU General Public License.
'''
import traceback
from ..type.pathLine import PathLine
from constraints import Constraints


class LineGeneratorMixin(object):
  
  # If elapsed time in milliseconds between pointer moves is greater, generate cusp-like instead of smooth.  
  MAX_POINTER_ELAPSED_FOR_SMOOTH = 100
  
  def LineGenerator(self, startPosition):
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
    startTurn = startPosition
    previousTurn = startPosition
    constraints = Constraints()
    didLastEmitCusp = False # state
    # directions = Directions()
    #turnClock = QTime.currentTime()  # note restart returns elapsed
    #turnClock.restart()
    try:
      while True:
        turn, positionElapsedTime = (yield)
        #turnElapsedTime = turnClock.restart()
        # print "Turn elapsed", turnElapsedTime
        #line = self.smallestLineFromPath(previousTurn, turn) # TEST 
        line = self._lineFromPath(startTurn, previousTurn, turn, constraints) # ,directions)
        if line is not None:  # if turn not satisfied by vector
          self.curveGenerator.send((line, False))
          # self.labelLine(str(positionElapsedTime), turn)
          startTurn = previousTurn  # !!! current turn is part of next line
          didLastEmitCusp = False
        elif positionElapsedTime > LineGeneratorMixin.MAX_POINTER_ELAPSED_FOR_SMOOTH:
          # User turned slowly, send a forced PathLine which subsequently makes cusp-like graphic
          # Effectively, eliminate generation lag by generating a LinePathElement.
          if not didLastEmitCusp:
            forcedLine = self._forceLineFromPath(startTurn, previousTurn, turn, constraints)
            self.curveGenerator.send((forcedLine, True))
            ## For debug: self.labelLine("F" + str(positionElapsedTime), turn)
            startTurn = previousTurn  # !!! current turn is part of next PathLine
            didLastEmitCusp = True
          else:
            print "Skipping consecutive cusps"
        # else current path (all turns) still satisfied by a PathLine: wait
          
        previousTurn = turn  # Roll forward  !!! Every turn, not just on send()
    except Exception:
      # !!! GeneratorExit is a BaseException, not an Exception
      # Unexpected programming errors, which are obscured unless caught
      print "Exception in LineGenerator"
      traceback.print_exc()
      raise
    except GeneratorExit:
      print "closing line generator"
      if previousTurn != startTurn:
        print "closing line generator"
        #print "startTurn, previousTurn", startTurn, previousTurn
        ''' Have turn not sent. Fabricate a PathLine and send() it now. '''
        self.curveGenerator.send((PathLine(startTurn, previousTurn), False))
      print "closed line generator"
  
  
  
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
      print "Four directions"
      self.resetLineFittingFilter()
      # Note end is previousTurn, not current Turn
      return PathLine(startTurn, previousTurn)
    else:
    '''
    # Vector from startTurn, via many turns, to currentTurn
    vectorViaAllTurns = currentTurn - startTurn
      
    if constraints.isViolatedBy(vector=vectorViaAllTurns):
      # print "Constraint violation", constraints, "vector", vectorViaAllTurns
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
      print "Reversal"
      assert previousTurn != startTurn
      return PathLine(startTurn, previousTurn)
    else:
      ## print "Force PathLine", startTurn, currentTurn
      return PathLine(startTurn, currentTurn)
    
    
  def _interpolateConstraintViolating(self, startTurn, lastSatisfyingTurn, firstNonsatisfingTurn):
    '''
    Interpolate precise violating pixel position
    Return a PathLine.
    
    This version simply returns PathLine to lastSatisfyingTurn (a null interpolation.)
    potrace does more, a non-null interpolation.
    '''
    return PathLine(startTurn, lastSatisfyingTurn)
  
  