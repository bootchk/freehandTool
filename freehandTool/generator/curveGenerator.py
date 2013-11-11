'''
Copyright 2012 Lloyd Konneker

This is free software, covered by the GNU General Public License.
'''
import traceback
import logging

from ..segmentString.segment import LineSegment, CurveSegment
from ..type.pathLine import PathLine
from ..type.freehandPoint import FreehandPoint
from ..type.pointerPoint import PointerPoint
from ..exception import FreehandNullSegmentError

logger = logging.getLogger(__name__)  # module level logger
logging.basicConfig(level=logging.DEBUG)


class CurveGeneratorMixin(object):
  
  '''
  Parameter: degree of smoothing for curve fitting
  <0 : no smoothing, all straight lines
  >4/3 : no cusps, all splines
  potrace defaults to 1, which seems suitable for bitmap images.
  For freehand drawing, defaults to 1.2
  '''
  ALPHAMAX = 1.2
  

  def CurveGenerator(self, initialLine):
    ''' 
    Takes lines, generates tuples of segments (lines or splines).
    Returns spline or cusp (two straight lines) defined between midpoints of previous two lines.
    On startup, previous PathLine is nullLine (!!! not None), but this still works.
    
    More generally known as "curve fitting."
    '''
    assert initialLine.isNullPathLine()
    previousLine = initialLine  # initial: assert is null PathLine
    
    try:
      while True:
        line, isLineForced = (yield)
        assert isinstance(line, PathLine), "input is a PathLine"
        if isLineForced:
          ''' User's pointer speed indicates wants a cusp-like fit, regardless of angle between lines.'''
          segments, pathEndPoint, cuspness = self.segmentsFromLineMidToEnd(previousLine, line)
          '''
          !!! next element from midpoint of nullLine
          at end point of path, but as a PointerPoint
          not as pathEndPoint, which is a FreehandPoint
          '''
          previousLine = PathLine.nullPathLine(PointerPoint(line.p2())) # pathEndPoint) 
          
          self.path.appendSegments(segments, segmentCuspness=cuspness)
        else:
          ''' Fit to path, possibly a cusp. '''
          segments, pathEndPoint, cuspness = self.segmentsFromLineMidToMid(previousLine, line)  
          # segments = nullcurveFromLines(previousLine, line) # TEST
          previousLine = line  # Roll forward
          # don't roll up the following and the one above, we want distinct traceback on errors
          self.path.appendSegments(segments, segmentCuspness=cuspness)
        
        self.lastEndPointGenerated = pathEndPoint # !!! global cache
        
        self.pathHeadGhost.updateStart(pathEndPoint)
       
    except Exception:
      # !!! GeneratorExit is a BaseException, not an Exception
      logger.critical("Unexpected exception in CurveGenerator")  # program error
      traceback.print_exc()
      raise
    except GeneratorExit:
      ''' 
      Last drawn element stopped at midpoint of PathLine.
      Caller must draw one last element from there to current PointerPosition.
      Here we don't know PointerPosition, and caller doesn't *know* PathLine midpoint,
      but path stops at last PathLine midpoint.  IOW  midpoint is *known* by caller as end of PointerTrack.
      
      GeneratorExit exception is still in effect after finally, but caller does not see it,
      and Python does NOT allow it to return a value.
      '''
      #logger.debug( "closed curve generator"
      pass



  def segmentsFromLineMidToMid(self, line1, line2):
    '''
    Return a sequence of segments that fit midpoints of two lines. Also return new path end point.
    Two cases, depend on angle between lines:
    - acute angle: cusp: returns two LineSegments.
    - obtuse angle: not cusp: return one CurveSegment that smoothly fits bend.
    '''
    
    # aliases for three points defined by two abutting PathLines
    # !!! Here we being real valued math, in a new CS (e.g. Scene)
    point1 = FreehandPoint(self.mapFromDeviceToScene(line1.p1()))
    point2 = FreehandPoint(self.mapFromDeviceToScene(line1.p2()))
    point3 = FreehandPoint(self.mapFromDeviceToScene(line2.p2()))
    
    # midpoints of PathLines
    midpoint1 = point2.interval(point1, 1/2.0)  # needed if creating QGraphicPathItem directly
    midpoint2 = point3.interval(point2, 1/2.0)
    
    denom = self.ddenom(point1, point3);
    if denom != 0.0:
      dd = abs(self.areaOfParallelogram(point1, point2, point3) / denom)
      if dd > 1:
        alpha = (1 - 1.0/dd)/0.75
      else : 
        alpha = 0
    else:
        alpha = 4/3.0

    if alpha > CurveGeneratorMixin.ALPHAMAX:
      return self.segmentsForCusp(cuspPoint=point2, endPoint=midpoint2)
    else:
      alpha = self.clampAlpha(alpha)
      '''
      Since first control point for this spline is on same PathLine
      as second control point for previous spline,
      said control points are colinear and joint between consecutive splines is smooth.
      '''
      logger.debug("mid to mid curve")
      return ([CurveSegment(startPoint=midpoint1,
                            controlPoint1=point1.interval(point2, 0.5+0.5*alpha), 
                            controlPoint2=point3.interval(point2, 0.5+0.5*alpha), 
                            endPoint=midpoint2)], 
              midpoint2,
              [False])  # Not a cusp
      

  def segmentsFromLineMidToEnd(self, line1, line2):
    '''
    Return sequence (two or three) of segments that fit midpoint of first PathLine to end of second PathLine.
    
    At least the last segment is a cusp.
    
    Cases for results:
    - [line, line, line], cuspness = [True, False, True]
    - [curve, line], cuspness = [False, True]
    '''
    midToMidsegments, endOfMidToMid, cuspness = self.segmentsFromLineMidToMid(line1, line2)
    finalEndPoint = FreehandPoint(self.mapFromDeviceToScene(line2.p2()))  # line2.p2()
    logger.debug("Mid to end")
    midToEnd = LineSegment(endOfMidToMid, finalEndPoint)
    return midToMidsegments + [midToEnd], finalEndPoint, cuspness + [True]



  '''
  Auxiliary functions for segmentsFromLineMidToMid() etc
  '''

  def segmentsForCusp(self, cuspPoint, endPoint):
    '''
    Return list of segments for sharp cusp. Return two straight LinePathElements and endPoint.
    from midpoints of two generating lines (not passed end of path, and endPoint) 
    to point where generating lines meet (cuspPoint).
    Note we already generated segment to first midpoint,
    and will subsequently generate segment from second midpoint.
    '''
    logger.debug("cusp <<<")
    try:
      # !!! Here is where we use cache
      firstSegment = LineSegment(self.lastEndPointGenerated, cuspPoint)
    except FreehandNullSegmentError:
      logger.debug("??? First segment null in segmentsForCusp")
      try:
        secondSegment = LineSegment(cuspPoint, endPoint)
      except FreehandNullSegmentError:
        logger.debug("??? Both segments null in segmentsForCusp")
        result = [], endPoint, []
      else:
        # Only secondSegment is not null
        result = [secondSegment,], endPoint, [False,]
    else:
      try:
        secondSegment = LineSegment(cuspPoint, endPoint)
      except FreehandNullSegmentError:
        logger.debug("??? Second segment null in segmentsForCusp")
        result = [firstSegment,], endPoint, [False,]
      else:
        # Normal case
        result = [firstSegment, secondSegment], endPoint, [True, False]  # First segment is cusp
    
    # !!! Not ensure that result is non-empty list
    # assert that any segments are not null, and len of segment list == len of cuspness list
    return result
  
  
  
  '''
  ddenom/areaOfParallelogram have property that the square of radius 1 centered
  at p1 intersects line p0p2 iff |areaOfParallelogram(p0,p1,p2)| <= ddenom(p0,p2)
  '''
      
  def ddenom(self, p0, p1):
    ''' ??? '''
    r = p0.cardinalDirectionLeft90(p1)
    return r.y()*(p1.x()-p0.x()) - r.x()*(p1.y()-p0.y());
    
    
  def areaOfParallelogram(self, p0, p1, p2):
    '''
    Vector cross product of vector point1 - point0 and point2 - point0
    I.E. area of the parallelogram defined by these three points.
    Scalar.
    '''
    return (p1.x()-p0.x()) * (p2.y()-p0.y()) - (p2.x()-p0.x()) * (p1.y()-p0.y())
    
  
  def clampAlpha(self, alpha):
    if alpha < 0.55:  return 0.55
    elif alpha > 1:   return 1
    else:             return alpha
    

