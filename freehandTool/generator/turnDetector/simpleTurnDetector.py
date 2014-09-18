'''
Copyright 2013 Lloyd Konneker

This is free software, covered by the GNU General Public License.
'''


from turnDetector import TurnDetector
from ..utils.axis import Axis
from ..utils.orthogonal import areOrthogonal
from ...logger import logger



class SimpleTurnDetector(TurnDetector):
  '''
  This subclass doesn't attempt to detect reversals as turns: compare with ReversalTurnDetector.
  
  This subclass doesn't keep its own history: the caller does, and passes a non-None referencePosition.
  
  This is the simplest subclass, most like what Potrace does.
  
  Spikes
  ------
  !!! A horizontal or vertical track that reverses (a spike) does not generate a turn (is filtered out.)
  e.g. (0,0), (1,0), (2,0), ...(5,0), (4,0)  does not generate a turn, where (0,0) is the referencePosition.
  If that pointer track continues ...(3,0), (3,1) then a turn would be generated at (3,1).
  
  For batch line tracing, it is OK if spikes are filtered out (they are 'hairs' on 'blocks' of pixels.)
  For incremental line tracing from a user's pointer track, it could be a problem,
  since a user might very carefully draw a spike (that stays one on pixel row) but it would be filtered out.
  
  Whether filtering out spikes is a problem might depend on the resolution of the pointer device,
  and its resolution relative to the resolution of the screen,
  and the resolution at which a user's hand can draw a straight line.
  Here we assume that the resolutions are the same
  (that even if the pointer device is high resolution, it's driver reduces to screen resolution.)
  
  Note the related problem of filtering out spikes at the line level, from reversing turns along a diagonal pointer track.
  '''
  
  def __init__(self, initialPosition):
    self.axis = Axis()
    
    
  def detect(self, newPosition, referencePosition=None):
    '''
    Return newPosition if not on horiz or vert axis with referencePosition, else return None. 
    '''
    if not areOrthogonal(newPosition, referencePosition):
      logger.debug("Turn %s", str(newPosition))
      return newPosition
    else:
      logger.debug("Not turn %s", str(newPosition))
      return None

