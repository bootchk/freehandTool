'''
Copyright 2012 Lloyd Konneker

This is free software, covered by the GNU General Public License.
'''

from PySide.QtCore import QTime



class TurnGeneratorMixin(object):
  '''
  Method name is capitalized because method *appears* to be a class.
  '''
  
  def TurnGenerator(self, startPosition):
    '''
    Freehand send()'s PointerPosition when user moves graphics pointer.
    Generates Turns.
    A Turn is a position between lines that lie on a axis (vertical or horizontal).
   
    Qt doesn't have event.time . Fabricate it here.  X11 has event.time.
    '''
    position = None   # if events are: send(None), close(), need this defined
    previousPosition = startPosition
    positionClock = QTime.currentTime()  # note restart returns elapsed
    positionClock.restart()
    # I also tried countPositionsSinceTurn to solve lag for cusp-like
    # print "init turn"
    
    try:
      while True:
        position = (yield)
        positionElapsedTime = positionClock.restart()
        turn = self.detectTurn(previousPosition, position)
        if turn is not None:
          self.lineGenerator.send((turn, positionElapsedTime))
          previousPosition = position  # Roll forward
        else: # path is still on an axis: wait
          pass
    # Not catching general exceptions, have not found a need for it.
    except GeneratorExit:
      print "Closing turn generator"
      # assert position is defined
      if previousPosition != position:
        ''' Have position not sent. Fabricate a turn (equal to position) and send() '''
        self.lineGenerator.send((position, 0))
      print "Closed turn generator"
      

  
  def detectTurn(self, position1, position2):
    ''' 
    Return position2 if it turns, i.e. if not on horiz or vert axis with position1, else return None. 
    
    !!! A diagonal pointer track that reverses (returns from whence it came) generates turns.
    That is, turns are not just left or right, but also reversal.
    
    !!! A horizontal or vertical track that reverses does not generate a turn.
    '''
    if        position1.x() != position2.x() \
          and position1.y() != position2.y()   :
      #print "Turn", position2
      return position2
    else:
      #print "Not turn", position2
      return None
    
    
    