'''
Copyright 2012 Lloyd Konneker

This is free software, covered by the GNU General Public License.
'''


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
    #print "Visit", root
    visitor(root)
    root.setTraversed(True)
  
    for relation in relationsToFollow:
      relatedInstance = relations.getRelatedInstance(root, relation)
      if relatedInstance is not None and not relatedInstance.getTraversed() and maxDepth > 0:
        # Recursion
        #print "Related by", relation
        self.walk(relatedInstance, relations, relationsToFollow, visitor, maxDepth = maxDepth - 1)

# singleton
relationWalker = RelationWalker()