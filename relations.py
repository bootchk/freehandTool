'''
Copyright 2012 Lloyd Konneker

This is free software, covered by the GNU General Public License.
'''


class Relations(object):
  '''
  Binary, symmetric relations of objects to other objects.
  
  Binary: relation between two objects (not three objects) 
  Symmetric: relation is commutative, A related to B implies B related to A
  
  Implemented as dictionary of dictionary.
  Stores many relationTypes in same data structure.
  
  Responsibility:
  - accept relation element (relate instance to instance)
  - get related element (instance related to given instance)
  - return whether related (is instance related)
  - clear all relations
  
  '''
  def __init__(self):
    self.relations = {}
    
    
  def relate(self, instance1, instance2, relationType):
    '''
    Store relation between two instances.
    '''
    if instance1 is None or instance2 is None:
      return
    # Forward relation
    if not instance1 in self.relations:
      self.relations[instance1] = {}
    self.relations[instance1][relationType] = instance2
    # Backward relation
    if not instance2 in self.relations:
      self.relations[instance2] = {}
    self.relations[instance2][relationType] = instance1
    
    
  def getRelatedInstance(self, instance, relationType ):
    ''' Get instance related to given instance by relationType or None. '''
    try:
      return self.relations[instance][relationType]
    except KeyError:
      return None
  
  
  def isRelated(self, instance, relationType):
    return relationType in self.relations[instance]
  
  def isSolelyRelated(self, instance, relationType):
    return relationType in self.relations[instance] \
      and len(self.relations[instance]) == 1
    
  def clear(self):
    del self.relations
    self.relations = {}
  