'''
Copyright 2012 Lloyd Konneker

This is free software, covered by the GNU General Public License.
'''
import traceback
from PySide.QtCore import QLineF, QPointF
from segment import LineSegment, CurveSegment



class CurveGeneratorMixin(object):
  
  '''
  Parameter: degree of smoothing for curve fitting
  <0 : no smoothing, all straight lines
  >4/3 : no cusps, all splines
  potrace defaults to 1, which seems suitable for bitmap images.
  For freehand drawing, defaults to 1.2
  '''
  ALPHAMAX = 1.2
  

  def CurveGenerator(self, startLine):
    ''' 
    Takes lines, generates tuples of segments (lines or splines).
    Returns spline or cusp (two straight lines) defined between midpoints of previous two lines.
    On startup, previous PathLine is nullLine (!!! not None), but this still works.
    
    More generally known as "curve fitting."
    '''
    previousLine = startLine  # null PathLine
    
    try:
      while True:
        line, isLineForced = (yield)
        assert isinstance(line, QLineF), "input is a PathLine"
        if isLineForced:
          ''' User's pointer speed indicates wants a cusp-like fit, regardless of angle between lines.'''
          segments, pathEndPoint, cuspness = self.segmentsFromLineMidToEnd(previousLine, line)
          previousLine = self.nullPathLine(pathEndPoint) # !!! next element from midpoint of nullLine
          self.path.appendSegments(segments, segmentCuspness=cuspness)
        else:
          ''' Fit to path, possibly a cusp. '''
          segments, pathEndPoint, cuspness = self.segmentsFromLineMidToMid(previousLine, line)  
          # segments = nullcurveFromLines(previousLine, line) # TEST
          previousLine = line  # Roll forward
          # don't roll up the following and the one above, we want distinct traceback on errors
          self.path.appendSegments(segments, segmentCuspness=cuspness)
          
        self.pathHeadGhost.updateStart(pathEndPoint)
       
    except Exception:
      # !!! GeneratorExit is a BaseException, not an Exception
      # Unexpected programming errors, which are obscured unless caught
      print "Exception in CurveGenerator"
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
      print "closed curve generator"


  def nullPathLine(self, point):
    ''' 
    Zero length PathLine at a point.
    Initial send to CurveGenerator.
    '''
    return QLineF(point, point)

    

  def segmentsFromLineMidToMid(self, line1, line2):
    '''
    Return a sequence of segments that fit midpoints of two lines. Also return new path end point.
    Two cases, depend on angle between lines:
    - acute angle: cusp: returns two LineSegments.
    - obtuse angle: not cusp: return one CurveSegment that smoothly fits bend.
    '''
    
    # aliases for three points defined by two abutting PathLines
    point1 = line1.p1()
    point2 = line1.p2()
    point3 = line2.p2()
    
    # midpoints of PathLines
    midpoint1 = self.interval(1/2.0, point2, point1)  # needed if creating QGraphicPathItem directly
    midpoint2 = self.interval(1/2.0, point3, point2)
    
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
      #print "mid to mid curve"
      return ([CurveSegment(startPoint=midpoint1,
                            controlPoint1=self.interval(0.5+0.5*alpha, point1, point2), 
                            controlPoint2=self.interval(0.5+0.5*alpha, point3, point2), 
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
    finalEndPoint = line2.p2()
    print "Mid to end"
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
    print "cusp <<<"
    return [LineSegment(self.path.getEndPointVCS(), cuspPoint), 
            LineSegment(cuspPoint, endPoint)], endPoint, [True, False]  # First segment is cusp
  
  

  
  def interval(self, fraction, point1, point2):
    ''' 
    Return point fractionally along line from point1 to point2 
    I.E. fractional sect (eg bisect) between vectors.
    '''
    return QPointF( point1.x() + fraction * (point2.x() - point1.x()),
                    point1.y() + fraction * (point2.y() - point1.y())  )
  
  
  '''
  ddenom/areaOfParallelogram have property that the square of radius 1 centered
  at p1 intersects line p0p2 iff |areaOfParallelogram(p0,p1,p2)| <= ddenom(p0,p2)
  '''
      
  def ddenom(self, p0, p1):
    ''' ??? '''
    r = self.cardinalDirectionLeft90(p0, p1)
    return r.y()*(p1.x()-p0.x()) - r.x()*(p1.y()-p0.y());
    
    
  def areaOfParallelogram(self, p0, p1, p2):
    '''
    Vector cross product of vector point1 - point0 and point2 - point0
    I.E. area of the parallelogram defined by these three points.
    Scalar.
    '''
    return (p1.x()-p0.x()) * (p2.y()-p0.y()) - (p2.x()-p0.x()) * (p1.y()-p0.y())
  
  def cardinalDirectionLeft90(self, p0, p1):
    '''
    Return unit (length doesn't matter?) vector 90 degrees counterclockwise from p1-p0,
    but clamped to one of eight cardinal direction (n, nw, w, etc) 
    '''
    return QPointF(-self.sign(p1.y()-p0.y()), self.sign(p1.x()-p0.x()))
    
  
  def clampAlpha(self, alpha):
    if alpha < 0.55:  return 0.55
    elif alpha > 1:   return 1
    else:             return alpha
    
    
  def sign(self, x):
    ''' Known wart of standard Python: no sign(). '''
    if x > 0:
      return 1
    elif x < 0:
      return -1
    else:
      return 0

