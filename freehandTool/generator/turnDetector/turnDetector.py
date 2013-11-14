'''
Copyright 2013 Lloyd Konneker

This is free software, covered by the GNU General Public License.
'''


class TurnDetector():
  '''
  Abstract Base Class: defines API
  
  Several TurnDetector subclasses are implemented.
  It is not clear which is best.
  
  A TurnDetector detects turns in a stream of PointerTrack positions.
  '''
  def __init__(self, initialPosition):
    raise NotImplementedError
  
  def detect(self, newPosition, referencePosition=None):
    ''' 
    Receive newPosition from a stream.
    Return a position (not necessarily newPosition) if it constitutes a turn, else None.
    Not all TurnDetectors pass a referencePosition
    '''
    raise NotImplementedError
