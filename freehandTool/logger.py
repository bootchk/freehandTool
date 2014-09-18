

'''
Whether we are debugging.

Should be False for a production (shipping) app.

This eliminates 'import logging'
The reason we do that is: the logging module is heavyweight, we don't want it on mobile platforms.

Formerly, many modules imported logging, and we disabled by:
logging.disable(logging.WARNING)
'''
DEBUG_FREEHAND = False

class NullLogger():
  '''
  Logger that mimics logging.logger but does nothing.
  Restrict to debug()
  '''
  def __init__(self):
    print("Freehand logging is off.")
    
  def debug(self, *args):
    return
  
  def critical(self, *args):
    return



  
if DEBUG_FREEHAND:
  import logging
  
  logger = logging.getLogger(__name__)  # "freehandTool")
  logger.setLevel(level=logging.DEBUG)
  
  # Better to do this than to assume logger of last resort?
  ch = logging.StreamHandler()
  ch.setLevel(logging.DEBUG)
  formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
  ch.setFormatter(formatter)
  logger.addHandler(ch)
  
  #print("Debug logging is on.")
  assert logger.hasHandlers()
else:
  logger = NullLogger()
  
