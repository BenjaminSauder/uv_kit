import math

import mathutils
import bmesh

from typing import List

class BBoxUV():
    '''Store bounds of uv loops'''
    
    def __init__(self, loops:List[bmesh.types.BMLoop]=None, uv_layer:bmesh.types.BMLayerItem=None) -> None:
        self.min = mathutils.Vector((math.inf, math.inf))
        self.max = mathutils.Vector((-math.inf, -math.inf))

        if loops != None and uv_layer != None:
            self.update(loops, uv_layer)

    @property
    def diagonal(self) -> mathutils.Vector:
        return self.max - self.min
    
    @property
    def average(self) -> mathutils.Vector:
        return (self.min + self.max) * 0.5

    def update(self, loops:List[bmesh.types.BMLoop], uv_layer:bmesh.types.BMLayerItem) -> None:
        self.min = mathutils.Vector((math.inf, math.inf))
        self.max = mathutils.Vector((-math.inf, -math.inf))
        for loop in loops:
            uv = loop[uv_layer].uv

            if uv.x > self.max.x:
                self.max.x = uv.x
            if uv.y > self.max.y:
                self.max.y = uv.y

            if uv.y < self.min.y:
                self.min.y = uv.y
            if uv.x < self.min.x:
                self.min.x = uv.x
    
    def merge(self, other_bbox:"BBoxUV") -> None:
        self.min.x = min(self.min.x, other_bbox.min.x)
        self.min.y = min(self.min.y, other_bbox.min.y)
        self.max.x = max(self.max.x, other_bbox.max.x)
        self.max.y = max(self.max.y, other_bbox.max.y)