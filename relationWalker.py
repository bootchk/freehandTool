


class RelationWalker(object):
  '''
  An algorithm for walking objects in a tree of relations, applying a visit function.
  
  Responsibility:
  - walk
  '''
  def walk(self, root, relations, relationsToFollow, visitor, maxDepth):
    ''' 
    Walk network of relations:
    - starting at root
    - only following relations (types) in relationsToFollow
    - to maxDepth
    '''
    print "Visit", root
    visitor(root)
    root.setTraversed()
  
    for relation in relationsToFollow:
      try:
        relatedInstance = relations.getRelatedInstance(root, relation)
        if not relatedInstance.getTraversed():
          if maxDepth > 0:
            # Recursion
            print "Related by", relation
            self.walk(relatedInstance, relations, relationsToFollow, visitor, maxDepth = maxDepth - 1)
      except KeyError:
        pass  # no related instance

# singleton
relationWalker = RelationWalker()