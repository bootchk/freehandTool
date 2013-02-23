'''
Copyright 2012 Lloyd Konneker

This is free software, covered by the GNU General Public License.
'''

# NOT USED by freehand.py but  traces remain in freehand.py.  Potrace uses it.


class Directions(object):
  '''
  Dictionary of cardinal directions (N, S, E, W) taken by a path.
  Understands how to compute a direction between two turns.
  '''
  def __init__(self):
    self.dict = {}
  
  def __len__(self):
    return len(self.dict)
    
  def update(self, turn1, turn2):
    vectorBetweenTurns = turn2 - turn1
    direction = (3 + 3*sign(vectorBetweenTurns.x()) + sign(vectorBetweenTurns.y()))/2
    self.dict[direction] = 1
    
  def reset(self):
    self.__init__()
    # super(Directions, self).__init__()
    