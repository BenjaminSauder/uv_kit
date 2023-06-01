import typing
from typing import List, Set

import bpy
from bpy.props import FloatProperty, BoolProperty, IntProperty
import bmesh
from bpy.types import Context, Event

from .uv import *
from .bbox import BBoxUV

expand_modes = (
    ("CONTINUOS", "Continous", ""),
    ("EXPAND", "Expand", "Expand by one edge"),
    ("SHRINK", "Shrink", "Shrink by one edge"),
)

align_directions = (
    ("X", "X", "Align in X direction"),
    ("Y", "Y", "Align in Y direction"),
    ("AUTO", "Auto", "Calculate align direction based on bounds"),
)

align_modes = (
    ("AVERAGE", "Average", ""),
    ("MIN", "Minimun", ""),
    ("MAX", "Maximum", ""),
)

straighten_modes = (
    ("GEOMETRY", "Geometry", ""),
    ("EVEN", "Even", ""),
    ("PROJECT", "Project", ""),
)

unwrap_modes = (
    ("ANGLE_BASED", "Angle based", ""),
    ("CONFORMAL", "Conformal", ""),
)


def is_uv_edit_mode():
    if not bpy.context.active_object:
        return False
    if bpy.context.active_object.type != 'MESH':
        return False
    if bpy.context.active_object.mode != 'EDIT':
        return False
    if bpy.context.scene.tool_settings.use_uv_select_sync:
        return False
    return True


class UV_OT_uvkit_select_uv_edgeloop(bpy.types.Operator):
    bl_idname = "view2d.uvkit_select_uv_edgeloop"
    bl_label = "uvkit select uv edge loop"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Select uv edgeloop"

    mode: bpy.props.EnumProperty(name="Mode", items=expand_modes)

    @classmethod
    def poll(cls, context):
        return is_uv_edit_mode()

    def execute(self, context):
        # print("#" * 66)
        for obj in context.selected_objects:
            if obj.mode == "EDIT" and obj.type == "MESH":
                bm = bmesh.from_edit_mesh(obj.data)
                uv_layer = bm.loops.layers.uv.verify()

                selected_uv_loops = get_selected_uv_edge_loops(bm, uv_layer)
                
                if self.mode == "CONTINUOS":
                    edge_loops = find_uv_edgeloops(selected_uv_loops, uv_layer)
                    # print(f"number of edgeloops: {len(edge_loops)}")

                    for edgeloop in edge_loops:
                        select_uv_edgeloop(edgeloop, uv_layer)

                elif self.mode == 'EXPAND':
                    edge_loops = find_uv_edgeloops(
                        selected_uv_loops, uv_layer, constrain_by_selected=True
                    )
                    # print(f"number of edgeloops: {len(edge_loops)}")

                    for edgeloop in edge_loops:
                        expand_uv_edgeloop(edgeloop, uv_layer)

                    for edgeloop in edge_loops:
                        select_uv_edgeloop(edgeloop, uv_layer)
                
                elif self.mode == 'SHRINK':
                    edge_loops = find_uv_edgeloops(
                        selected_uv_loops, uv_layer, constrain_by_selected=True
                    )
                    # print(f"number of edgeloops: {len(edge_loops)}")

                    for edgeloop in edge_loops:
                        shrink_uv_edgeloop(edgeloop, uv_layer)

                bmesh.update_edit_mesh(obj.data)

        return {"FINISHED"}

    def invoke(self, context, event):
        self.execute(context)
        return {"FINISHED"}


class UV_OT_uvkit_select_uv_edgering(bpy.types.Operator):
    bl_idname = "view2d.uvkit_select_uv_edgering"
    bl_label = "uvkit select uv edge ring"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Select UV edgering"

    mode: bpy.props.EnumProperty(name="Mode", items=expand_modes)
    
    @classmethod
    def poll(cls, context):
        return is_uv_edit_mode()

    def execute(self, context):
        # print("#" * 66)
        for obj in context.selected_objects:
            if obj.mode == "EDIT" and obj.type == "MESH":
                bm = bmesh.from_edit_mesh(obj.data)
                uv_layer = bm.loops.layers.uv.verify()

                selected_uv_loops = get_selected_uv_edge_loops(bm, uv_layer)

                if self.mode == "CONTINUOS":
                    edge_rings = find_uv_edgerings(
                        selected_uv_loops, uv_layer, constrain_by_selected=False
                    )

                    for edge_ring in edge_rings:
                        select_uv_edgering(edge_ring, uv_layer)

                elif self.mode == "EXPAND":
                    edge_rings = find_uv_edgerings(
                        selected_uv_loops, uv_layer, constrain_by_selected=True
                    )

                    for edge_ring in edge_rings:
                        expand_uv_edgering(edge_ring, uv_layer)

                    for edge_ring in edge_rings:
                        select_uv_edgering(edge_ring, uv_layer)

                elif self.mode == "SHRINK":
                    edge_rings = find_uv_edgerings(
                        selected_uv_loops, uv_layer, constrain_by_selected=True
                    )

                    for edgering in edge_rings:
                        shrink_uv_edgering(edgering, uv_layer)

                bmesh.update_edit_mesh(obj.data)

        return {"FINISHED"}

    def invoke(self, context, event):
        self.execute(context)
        return {"FINISHED"}


class UV_OT_uvkit_align_uv_edgeloops(bpy.types.Operator):
    bl_idname = "view2d.uvkit_align_uv_edgeloops"
    bl_label = "uvkit align edge loops"
    bl_options = {"REGISTER", "UNDO"}

    bl_description = """Aligns uv edgeloops
    
SHIFT - align to max value.
CTRL - align to min value.
ALT - use global values"""

    apply_per_edgeloop: bpy.props.BoolProperty(name="Apply per loop", default=True)
    direction: bpy.props.EnumProperty(name="Direction", items=align_directions)
    mode: bpy.props.EnumProperty(name="Mode", items=align_modes)

    @classmethod
    def poll(cls, context):
        return is_uv_edit_mode()

    def execute(self, context):
        # print( "#" * 66)
        class Part:
            def __init__(self):
                self.mesh = None
                self.bm = None
                self.uv_layer = None
                self.edge_loops = []
                self.bounding_boxes = []
                self.directions = []

        parts = []

        for obj in context.selected_objects:
            if obj.mode != "EDIT" or obj.type != "MESH":
                continue

            bm = bmesh.from_edit_mesh(obj.data)
            uv_layer = bm.loops.layers.uv.verify()

            selected_uv_loops = get_selected_uv_edge_loops(bm, uv_layer)
            edge_loops = find_uv_edgeloops(
                selected_uv_loops, uv_layer, constrain_by_selected=True
            )

            # add "other" vert from end
            for edge_loop in edge_loops:
                edge_loop.append(edge_loop[-1].link_loop_next)

            part = Part()
            parts.append(part)
            part.mesh = obj.data
            part.bm = bm
            part.uv_layer = uv_layer
            part.edge_loops = edge_loops

            for edge_loop in edge_loops:
                bbox = BBoxUV(edge_loop, uv_layer)
                direction = self.direction
                # AUTO direction - need find out alignment
                if self.direction == "AUTO":                   
                    direction = "X"
                    if bbox.diagonal.y < bbox.diagonal.x:
                        direction = "Y"

                part.bounding_boxes.append(bbox)
                part.directions.append(direction)

        global_bbox = BBoxUV()
        if not self.apply_per_edgeloop:
            for part in parts:
                for bbox in part.bounding_boxes:
                    global_bbox.merge(bbox)
   
        for part in parts:
            bm = part.bm
            uv_layer = part.uv_layer

            for i, edge_loop in enumerate(part.edge_loops):
                connected_uv_verts = []
                for loop in edge_loop:
                    for connected in loop.vert.link_loops:
                        if not connected.face.select:
                            continue

                        a = loop[uv_layer].uv
                        b = connected[uv_layer].uv
                        if is_same_uv_location(a, b):
                            connected_uv_verts.append(connected)

                if self.apply_per_edgeloop:
                    current_bbox = part.bounding_boxes[i]
                else:
                    current_bbox = global_bbox

                for loop in connected_uv_verts:
                    if part.directions[i] == "X":
                        if self.mode == "AVERAGE":
                            loop[uv_layer].uv.x = current_bbox.average.x
                        elif self.mode == "MAX":
                            loop[uv_layer].uv.x = current_bbox.max.x
                        elif self.mode == "MIN":
                            loop[uv_layer].uv.x = current_bbox.min.x

                    elif part.directions[i] == "Y":
                        if self.mode == "AVERAGE":
                            loop[uv_layer].uv.y = current_bbox.average.y
                        elif self.mode == "MAX":
                            loop[uv_layer].uv.y = current_bbox.max.y
                        elif self.mode == "MIN":
                            loop[uv_layer].uv.y = current_bbox.min.y

            bmesh.update_edit_mesh(part.mesh)

        return {"FINISHED"}

    def invoke(self, context, event):
        self.mode = align_modes[0][0]

        if event.shift:
            self.mode = align_modes[2][0]
        elif event.ctrl:
            self.mode = align_modes[1][0]

        if event.alt:
            self.apply_per_edgeloop = False
        else:
            self.apply_per_edgeloop = True

        self.execute(context)
        return {"FINISHED"}


class UV_OT_uvkit_spread_loop(bpy.types.Operator):
    bl_idname = "view2d.uvkit_spread_loop"
    bl_label = "uvkit spread loop"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Straightens uv edgeloops"

    mode: bpy.props.EnumProperty(name="Mode", items=straighten_modes)

    @classmethod
    def poll(cls, context):
        return is_uv_edit_mode()

    def execute(self, context):
        # print("#"*66)
        for obj in context.selected_objects:
            if obj.mode == "EDIT" and obj.type == "MESH":
                bm = bmesh.from_edit_mesh(obj.data)
                uv_layer = bm.loops.layers.uv.verify()

                selected_uv_loops = get_selected_uv_edge_loops(bm, uv_layer)

                edge_loops = find_uv_edgeloops(
                    selected_uv_loops, uv_layer, constrain_by_selected=True
                )
                # add "other" vert from end
                for edge_loop in edge_loops:
                    edge_loop.append(edge_loop[-1].link_loop_next)

                for edge_loop in edge_loops:
                    bbox = BBoxUV(edge_loop, uv_layer)
                    uv_distance = bbox.diagonal.length

                    distances = []
                    for i in range(1, len(edge_loop)):
                        a = edge_loop[i - 1]
                        b = edge_loop[i]
                        c = b.vert.co - a.vert.co
                        distances.append(c.length)
                    total_distance = sum(distances)

                    first_loop_uv = edge_loop[0][uv_layer].uv
                    last_loop_uv = edge_loop[-1][uv_layer].uv
                    direction = (last_loop_uv - first_loop_uv).normalized()

                    uv_vectors = []
                    for loop in edge_loop:
                        uv_vectors.append(loop[uv_layer].uv - first_loop_uv)

                    for i in range(1, len(edge_loop) - 1):
                        a = edge_loop[i - 1]
                        b = edge_loop[i]

                        a_uv = a[uv_layer]
                        b_uv = b[uv_layer]

                        target_pos = b_uv.uv.to_2d()

                        if self.mode == "GEOMETRY":
                            distance = (distances[i - 1] * uv_distance) / total_distance
                            target_pos = a_uv.uv + direction * distance

                        elif self.mode == "EVEN":
                            distance = uv_distance / (len(edge_loop) - 1)
                            target_pos = a_uv.uv + direction * distance

                        elif self.mode == "PROJECT":
                            vector = uv_vectors[i]
                            projection = vector.dot(direction)
                            target_pos = (
                                edge_loop[0][uv_layer].uv + direction * projection
                            )

                        # need to store the pos, as b_uv could be moved around in following code
                        b_pos = b_uv.uv.to_2d()

                        for connected in b.vert.link_loops:
                            if not connected.face.select:
                                continue

                            c_uv = connected[uv_layer]
                            if is_same_uv_location(c_uv.uv, b_pos):
                                c_uv.uv = target_pos

                bmesh.update_edit_mesh(obj.data)
        return {"FINISHED"}

    def invoke(self, context, event):
        self.execute(context)
        return {"FINISHED"}


class UV_OT_uvkit_constrained_unwrap(bpy.types.Operator):
    bl_idname = "view2d.uvkit_constrained_unwrap"
    bl_label = "uvkit constrained unwrap"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = """Keeps the selected uv's in place/pinned and unwraps the unselected rest of the uv island.

SHIFT - ignore seams.
CTRL - ignore pins.
ALT - ignore seams and pins"""

    mode: bpy.props.EnumProperty(name="Mode", items=unwrap_modes)
    ignore_seams: bpy.props.BoolProperty(name="Ignore edge seams", default=False)
    ignore_pins: bpy.props.BoolProperty(name="Ignore pinned uv", default=False)

    @classmethod
    def poll(cls, context):
        return is_uv_edit_mode()

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.mode == "EDIT" and obj.type == "MESH":
                bm = bmesh.from_edit_mesh(obj.data)
                uv_layer = bm.loops.layers.uv.verify()
                
                selected_uv_loops = get_selected_uv_vert_loops(bm, uv_layer)
                uv_islands = find_uv_islands_for_selected_uv_loops(bm, uv_layer)

                pinned_uvs = set()
                seam_edges = set()

                for island in uv_islands:
                    for loop in island:
                        for connected in loop.face.loops:
                            if not connected.face.select:
                                continue

                            connected[uv_layer].select = True
                            connected[uv_layer].select_edge = False

                            if self.ignore_pins:
                                if connected[uv_layer].pin_uv:
                                    pinned_uvs.add(connected)
                                connected[uv_layer].pin_uv = False

                            if self.ignore_seams:
                                if connected.edge.seam:
                                    seam_edges.add(connected.edge)
                                connected.edge.seam = False

                for selected_uv_loop in selected_uv_loops:
                    selected_uv_loop[uv_layer].select = False

                    if selected_uv_loop[uv_layer].pin_uv:
                        pinned_uvs.add(selected_uv_loop)
                    selected_uv_loop[uv_layer].pin_uv = True
                    
                    for connected in selected_uv_loop.vert.link_loops:
                        if connected.face.select:
                            connected[uv_layer].select = False

                            if connected[uv_layer].pin_uv:
                                pinned_uvs.add(connected)
                            connected[uv_layer].pin_uv = True

                if self.mode == "ANGLE_BASED":
                    bpy.ops.uv.unwrap(method="ANGLE_BASED")
                elif self.mode == "CONFORMAL":
                    bpy.ops.uv.unwrap(method="CONFORMAL")

                for island in uv_islands:
                    for loop in island:
                        for connected in loop.face.loops:
                            connected[uv_layer].select = False
                            connected[uv_layer].select_edge = False

                for edge in seam_edges:
                    edge.seam = True

                for selected_uv_loop in selected_uv_loops:
                    selected_uv_loop[uv_layer].select = True
                    selected_uv_loop[uv_layer].pin_uv = False
                
                for pinned_uv in pinned_uvs:
                    pinned_uv[uv_layer].pin_uv = False

                for selected_uv_loop in selected_uv_loops:
                    selected_uv_loop[uv_layer].select_edge = selected_uv_loop.link_loop_next[uv_layer].select

                bmesh.update_edit_mesh(obj.data)

        return {"FINISHED"}

    def invoke(self, context, event):
        if event.shift:
            self.ignore_seams = True
        elif event.ctrl:
            self.ignore_pins = True
        elif event.alt:
            self.ignore_seams = True
            self.ignore_pins = True
        else:
            self.ignore_seams = False
            self.ignore_pins = False

        self.execute(context)
        return {"FINISHED"}
    

class UV_OT_uvkit_show_image(bpy.types.Operator):
    # heavily copied from Reinier Goijvaerts
    bl_idname = "view2d.uvkit_show_image"
    bl_label = "Show Image"
    bl_options = {"INTERNAL"}

    image_name: bpy.props.StringProperty(name='image_name', default='')
    
    def execute(self, context):        
        for area in bpy.context.screen.areas:
            if area.type == 'IMAGE_EDITOR':
                for image in bpy.data.images:
                    if image.name == self.image_name:
                        area.spaces.active.image = image
                
        return {'FINISHED'}
    
class UV_OT_uvkit_align(bpy.types.Operator):
    bl_idname = "view2d.uvkit_align"
    bl_label = "Align"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = """Aligns the selection or the Cursor.

CTRL - use 0-1 space as boundary.
ALT - set the Cursor"""

    align_selection: bpy.props.BoolProperty(name="Align selection", default=False)
    direction: bpy.props.StringProperty(name='Direction', default='center')
    use_unit_square: bpy.props.BoolProperty(name="Use 0-1 space", default=False)
    set_cursor: bpy.props.BoolProperty(name="Set Cursor", default=False)

    def execute(self, context: Context) -> Set[str]:
        class Part:
            def __init__(self):
                self.mesh = None
                self.bm = None
                self.uv_layer = None
                self.selected_uvs = []
                self.uv_islands = []
                self.uv_islands_bounds = []

        global_bbox = BBoxUV()
        parts = []
        has_uv_selection = False

        selection_mode = context.scene.tool_settings.uv_select_mode
        face_or_island_selection_mode = selection_mode == 'FACE' or selection_mode == 'ISLAND'

        for obj in context.selected_objects:
            if obj.mode != "EDIT" or obj.type != "MESH":
                continue

            bm = bmesh.from_edit_mesh(obj.data)
            uv_layer = bm.loops.layers.uv.verify()

            selected_uv_loops = get_selected_uv_vert_loops(bm, uv_layer)

            if not has_uv_selection and len(selected_uv_loops) > 0:
                has_uv_selection  = True

            uv_islands: List[bmesh.types.BMLoop] = []
            uv_islands_bounds: List[BBoxUV] = []
            if face_or_island_selection_mode:
                uv_islands = find_uv_islands_for_selected_uv_loops(bm, uv_layer)       
                print(f"islands: {len(uv_islands)}")
                for island in uv_islands:
                    uv_islands_bounds.append(BBoxUV(island, uv_layer))

            part = Part()
            part.mesh = obj.data
            part.bm = bm
            part.uv_layer = uv_layer
            part.selected_uvs = selected_uv_loops
            part.uv_islands = uv_islands
            part.uv_islands_bounds = uv_islands_bounds
            parts.append(part)

            if face_or_island_selection_mode:
                for bbox in part.uv_islands_bounds:
                    global_bbox.merge(bbox)
            else:
                global_bbox.merge(BBoxUV(selected_uv_loops, uv_layer))


        if not has_uv_selection or self.use_unit_square:
            global_bbox.set_to_unit_square()                    

        if self.set_cursor:
            space_data = context.space_data
            space_data.cursor_location = global_bbox.get_location(self.direction)
            return {"FINISHED"}
               
        if self.align_selection and has_uv_selection:
            for part in parts:
                bm = part.bm
                uv_layer = part.uv_layer
               
                if face_or_island_selection_mode:
                    for i, island in enumerate(part.uv_islands):
                        island_bbox: BBoxUV = part.uv_islands_bounds[i]
                    
                        if self.direction == 'left':
                            delta = global_bbox.left - island_bbox.left
                            delta.y = 0 
                        elif self.direction == 'topleft':
                            delta = global_bbox.topleft - island_bbox.topleft                           
                        elif self.direction == 'top':
                            delta = global_bbox.top - island_bbox.top
                            delta.x = 0 
                        elif self.direction == 'topright':
                            delta = global_bbox.topright - island_bbox.topright
                        elif self.direction == 'right':
                            delta = global_bbox.right - island_bbox.right
                            delta.y = 0 
                        elif self.direction == 'bottomright':
                            delta = global_bbox.bottomright - island_bbox.bottomright
                        elif self.direction == 'bottom':
                            delta = global_bbox.bottom - island_bbox.bottom
                            delta.x = 0 
                        elif self.direction == 'bottomleft':
                            delta = global_bbox.bottomleft - island_bbox.bottomleft
                        elif self.direction == 'center':
                            delta = global_bbox.center - island_bbox.center
                        elif self.direction == 'horizontal':
                            delta = global_bbox.center - island_bbox.center
                            delta.y = 0
                        elif self.direction == 'vertical':
                            delta = global_bbox.center - island_bbox.center
                            delta.x = 0

                        for loop in island:
                            loop[uv_layer].uv += delta

                else:
                    for loop in part.selected_uvs:
                        if self.direction == 'left':
                            loop[uv_layer].uv.x = global_bbox.get_location(self.direction).x
                        elif self.direction == 'topleft':
                            loop[uv_layer].uv = global_bbox.get_location(self.direction)
                        elif self.direction == 'top':
                            loop[uv_layer].uv.y = global_bbox.get_location(self.direction).y
                        elif self.direction == 'topright':
                            loop[uv_layer].uv = global_bbox.get_location(self.direction)
                        elif self.direction == 'right':
                            loop[uv_layer].uv.x = global_bbox.get_location(self.direction).x
                        elif self.direction == 'bottomright':
                            loop[uv_layer].uv = global_bbox.get_location(self.direction)
                        elif self.direction == 'bottom':
                            loop[uv_layer].uv.y = global_bbox.get_location(self.direction).y
                        elif self.direction == 'bottomleft':
                            loop[uv_layer].uv = global_bbox.get_location(self.direction)
                        elif self.direction == 'center':
                            loop[uv_layer].uv = global_bbox.get_location(self.direction)
                        elif self.direction == 'horizontal':
                            loop[uv_layer].uv.y = global_bbox.get_location(self.direction).y
                        elif self.direction == 'vertical':
                            loop[uv_layer].uv.x = global_bbox.get_location(self.direction).x

            bmesh.update_edit_mesh(part.mesh)
        return {"FINISHED"}


    

    def invoke(self, context: Context, event: Event) -> Set[str]:
        self.set_cursor = False
        self.align_selection = False
        self.use_unit_square = False

        if event.alt:
            self.set_cursor = True
        else:
            self.align_selection = True

        if event.ctrl:
            self.use_unit_square = True
        
        return self.execute(context)

# -------------------------------------------------------------------
#   Register & Unregister
# -------------------------------------------------------------------

classes = [
    UV_OT_uvkit_spread_loop,
    UV_OT_uvkit_select_uv_edgering,
    UV_OT_uvkit_select_uv_edgeloop,
    UV_OT_uvkit_align_uv_edgeloops,
    UV_OT_uvkit_constrained_unwrap,
    UV_OT_uvkit_show_image,
    UV_OT_uvkit_align,
]


def register():

    import importlib
    from . import bbox
    importlib.reload(bbox)
    from . import uv
    importlib.reload(uv)

    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
