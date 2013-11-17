'''
'''

class History():
  '''
  Sequence of past states.
  
  Here, only two past states.
  
  States can be any class, but must implement equality operator.
  
  Callers typically either call:
  - roll(); update(new)
  - collapse(new)
  - update()  (when caller only uses one past state.)
  These do not result in the same history.
  
  roll() should NOT be called without subsequently calling update()
  '''
  
  def __init__(self, initialState):
    self.collapse(initialState)
    
    
  def updateEnd(self, newState):
    '''
    Set end of history to newState.
    '''
    self.end = newState
    
    
  def roll(self):
    '''
    Forget ancient history: both start and end the same historical end state.
    '''
    self.start = self.end
  
  
  def collapse(self, newState):
    '''
    Both start and end the same new state.
    
    Same as:
      updateEnd(newState)
      roll()
    '''
    self.start = self.end = newState
    
    
  def isCollapsed(self):
    '''
    Was most recent call a collapse()?
    '''
    return self.start == self.end
    