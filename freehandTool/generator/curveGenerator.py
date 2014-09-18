'''
Copyright 2012 Lloyd Konneker

This is free software, covered by the GNU General Public License.
'''
##For debugging
##import traceback

from ..segmentString.segment import LineSegment, CurveSegment
from ..type.pathLine import PathLine
from ..type.freehandPoint import FreehandPoint
from ..type.pointerPoint import PointerPoint
from ..exception import FreehandNullSegmentError

from .utils.history import History



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
    Takes PathLines, generates tuples of segments (lines or splines).
    Returns spline or cusp (two straight lines) defined between midpoints of previous two PathLines.
    On startup, previous PathLine is nullLine (!!! not None), but this still works.
    
    More generally known as "curve fitting."
    
    !!! InitialLine is NullPathLine and might receive a NullPathLine as part of flushing.
    Don't assume any yielded line is not null, i.e. a very short line, from a point to the same point.
    '''
    assert initialLine.isNullPathLine()
    history = History(initialLine)
    
    try:
      while True:
        newPathLine, isLineForced = (yield)
        assert isinstance(newPathLine, PathLine), "input is a PathLine"
        if isLineForced:
          ''' 
          Forced line from: 1) User pointer pause or 2) closing generators. 
          Make cusp-like fit, regardless of angle between PathLines.
          newPathLine is not necessarily NullPathLine.
          '''
          if history.end.isNullPathLine():
            '''
            Either never generated any segments, or already flushed by a prior user pointer pause.
            '''
            if newPathLine.isNullPathLine():
              self.logger.debug("Already flushed, or empty")
              ''' !!! This is not a return which is StopIteration: it might be a pause, followed by close. '''
              pass
            else:
              segments, pathEndPoint, cuspness = self.segmentsFromLineEndToEnd(history.end, newPathLine)
              history.updateEnd(PathLine.nullPathLine(PointerPoint(newPathLine.p2())))
              self._putSegments(segments, pathEndPoint, cuspness)
          else:
            segments, pathEndPoint, cuspness = self.segmentsFromLineMidToEnd(history.end, newPathLine)
            '''
            !!! next element from midpoint of nullLine
            at end point of path, but as a PointerPoint
            not as pathEndPoint, which is a FreehandPoint
            '''
            # Make history show null pathLine created here, not yielded
            history.updateEnd(PathLine.nullPathLine(PointerPoint(newPathLine.p2()))) # pathEndPoint) 
            
            self._putSegments(segments, pathEndPoint, cuspness)
        else:
          ''' Fit to path, possibly a cusp. '''
          segments, pathEndPoint, cuspness = self.segmentsFromLineMidToMid(history.end, newPathLine)  
          # segments = nullcurveFromLines(history.end, newPathLine) # TEST
          history.updateEnd(newPathLine)
          # don't roll up the following stmt and stmt above, we want distinct traceback on errors
          self._putSegments(segments, pathEndPoint, cuspness)
       
    except Exception:
      # !!! GeneratorExit is a BaseException, not an Exception
      self.logger.critical("Unexpected exception in CurveGenerator")  # program error
      ##traceback.print_exc()
      raise
    except GeneratorExit:
      self.flushCurveGenerator(history)


  def flushCurveGenerator(self, history):
    '''
    Assert my feeding generators have been flushed.
    '''
    '''
    OLD DESIGN
    
      Last drawn element stopped at midpoint of PathLine.
      Caller must draw one last element from there to current PointerPosition.
      Here we don't know PointerPosition, and caller doesn't *know* PathLine midpoint,
      but path stops at last PathLine midpoint.  IOW  midpoint is *known* by caller as end of PointerTrack.
      
      GeneratorExit exception is still in effect after finally, but caller does not see it,
      and Python does NOT allow it to return a value.
    '''
    self.logger.debug("flush")
    '''
    Assert LineGenerator sent a NullPathLine that caused self to generate a segment to it's midpoint.
    So already generated segments accurately reach end of the PointerTrack.
    '''
    assert history.end.isNullPathLine()
    pass


  def _putSegments(self, segments, pathEndPoint, cuspness):
    '''
    Append segments and other updating.
    This is equivalent to 'send' of other generators.
    '''
    self.path.appendSegments(segments, segmentCuspness=cuspness)
    self.lastEndPointGenerated = pathEndPoint # !!! global cache
    self.pathHeadGhost.updateStart(pathEndPoint)
    
  
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
      self.logger.debug("mid to mid curve")
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
    self.logger.debug("Mid to end")
    midToEnd = LineSegment(endOfMidToMid, finalEndPoint)
    return midToMidsegments + [midToEnd], finalEndPoint, cuspness + [True]


  def segmentsFromLineEndToEnd(self, line1, line2):
    ''' 
    Single segment from end of line1 to end of line2 
    
    This is called for example:
    - when the previous line ended in a cusp,
    i.e. we already generated segments to the end of previous line.
    - when only line is generated (pointerdown, move straight, pointer up)
    when line1 is the initial line (a null line.)
    
    '''
    startPoint = FreehandPoint(self.mapFromDeviceToScene(line1.p2()))
    endPoint = FreehandPoint(self.mapFromDeviceToScene(line2.p2()))
    segment = LineSegment(startPoint, endPoint)
    # end of line2 is a cusp
    result = [segment, ], endPoint, [True, ]
    return result

  '''
  Auxiliary functions for segmentsFromLineMidToMid() etc
  '''

  def segmentsForCusp(self, cuspPoint, endPoint):
    '''
    Return list of segments for sharp cusp. Return two straight LinePathElements and endPoint.
    from midpoints of two generating PathLines (not passed end of path, and endPoint) 
    to point where generating PathLines meet (cuspPoint).
    Note we already generated segment to first midpoint,
    and will subsequently generate segment from second midpoint.
    '''
    self.logger.debug("cusp")
    try:
      # !!! Here is where we use cache
      firstSegment = LineSegment(self.lastEndPointGenerated, cuspPoint)
    except FreehandNullSegmentError:
      self.logger.debug("??? First segment null in segmentsForCusp")
      try:
        secondSegment = LineSegment(cuspPoint, endPoint)
      except FreehandNullSegmentError:
        self.logger.debug("??? Both segments null in segmentsForCusp")
        result = [], endPoint, []
      else:
        # Only secondSegment is not null
        result = [secondSegment,], endPoint, [False,]
    else:
      try:
        secondSegment = LineSegment(cuspPoint, endPoint)
      except FreehandNullSegmentError:
        self.logger.debug("??? Second segment null in segmentsForCusp")
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
    

