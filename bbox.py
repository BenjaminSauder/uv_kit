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
    def topleft(self) -> mathutils.Vector:
        return  mathutils.Vector((self.min.x, self.max.y))
    
    @property
    def topright(self) -> mathutils.Vector:
        return  mathutils.Vector((self.max.x, self.max.y))

    @property
    def bottomleft(self) -> mathutils.Vector:
        return mathutils.Vector((self.min.x, self.min.y))
    
    @property
    def bottomright(self) -> mathutils.Vector:
        return  mathutils.Vector((self.max.x, self.min.y))

    @property
    def left(self) -> mathutils.Vector:
        return  mathutils.Vector((self.min.x, (self.max.y + self.min.y) * 0.5))
    
    @property
    def right(self) -> mathutils.Vector:
        return  mathutils.Vector((self.max.x, (self.max.y + self.min.y) * 0.5))
    
    @property
    def top(self) -> mathutils.Vector:
        return  mathutils.Vector(((self.max.x + self.min.x) * 0.5, self.max.y))
    
    @property
    def bottom(self) -> mathutils.Vector:
        return  mathutils.Vector(((self.max.x + self.min.x) * 0.5, self.min.y))

    @property
    def diagonal(self) -> mathutils.Vector:
        return self.max - self.min
    
    @property
    def average(self) -> mathutils.Vector:
        return (self.min + self.max) * 0.5
    
    @property
    def center(self) -> mathutils.Vector:
        return self.average
    
    def get_location(self, direction):
        if direction == 'left':
            return self.left
        elif direction == 'topleft':
            return self.topleft  
        elif direction == 'top':
            return self.top
        elif direction == 'topright':
            return self.topright
        elif direction == 'right':
            return self.right
        elif direction == 'bottomright':
            return self.bottomright
        elif direction == 'bottom':
            return self.bottom
        elif direction == 'bottomleft':
            return self.bottomleft
        elif direction == 'center':
            return self.center
        elif direction == 'horizontal':
            return self.center
        elif direction == 'vertical':
            return self.center

    def set_to_unit_square(self):
        self.min = mathutils.Vector((0, 0))
        self.max = mathutils.Vector((1, 1))

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