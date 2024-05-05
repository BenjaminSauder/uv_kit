import math
import bpy
import bmesh


from bpy.props import (IntProperty,
                       BoolProperty,
                       StringProperty,
                       CollectionProperty,
                       PointerProperty)

from bpy.types import (Operator,
                       Panel,
                       PropertyGroup,
                       UIList)



class IMAGE_MT_uvkit_imageList(bpy.types.Menu):
    # heavily copied from Reinier Goijvaerts
    bl_idname = "IMAGE_MT_uvkit_imageList"
    bl_label = "Textures from material"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'

    def draw(self, context):
        layout = self.layout              
        
        obj = bpy.context.active_object
        
        materials = []
        if obj.type == 'MESH' and obj.mode == 'EDIT':
            mesh = bmesh.from_edit_mesh(obj.data)
            material_indices = [face.material_index for face in mesh.faces if face.select]
            for index in material_indices:
                mat = obj.material_slots[index].material
                if mat.use_nodes and mat not in materials:
                    materials.append(mat)
        else:
            active_mat = bpy.context.active_object.active_material
            if active_mat.use_nodes:
                materials.append(active_mat)

        for mat in materials:   
            if not mat:
                continue

            for node in mat.node_tree.nodes:
                if node.type != 'TEX_IMAGE':
                    continue

                if not node.image:
                    continue
              
                button = layout.operator("view2d.uvkit_show_image", text=node.image.name, icon_value=layout.icon(node.image))
                button.image_name = node.image.name


class IMAGE_PT_uvkit_main(Panel):
    bl_idname = "IMAGE_PT_uvkit_main"
    bl_label = "UV kit"
    bl_space_type = 'IMAGE_EDITOR'   
    bl_region_type = 'UI'
    bl_category = "Tool"
    
    def draw(self, context):       
        layout = self.layout
        sima = context.space_data
        show_uvedit = sima.show_uvedit

        if context.preferences.view.show_developer_ui:
            col = layout.column()
            col.separator()
            col.operator("script.reload", text="Reload  Scripts", icon="NONE")

        layout.menu(IMAGE_MT_uvkit_imageList.bl_idname)
        
        if not show_uvedit:
            return  

        box = layout.box()	
        box.label(text="UV and Cursor align")
        row = box.column(align=True).row(align=True)
        col = row.column(align=True)

        col = row.column(align=True)
        col.operator("view2d.uvkit_align", text="↖").direction = "topleft"
        col.operator("view2d.uvkit_align", text="← ").direction = "left"
        col.operator("view2d.uvkit_align", text="↙").direction = "bottomleft"
              
        col = row.column(align=True)
        col.operator("view2d.uvkit_align", text="↑").direction = "top"
        col.operator("view2d.uvkit_align", text="+").direction = "center"
        col.operator("view2d.uvkit_align", text="↓").direction = "bottom"

        col = row.column(align=True)
        col.operator("view2d.uvkit_align", text="↗").direction = "topright"
        col.operator("view2d.uvkit_align", text=" →").direction = "right"
        col.operator("view2d.uvkit_align", text="↘").direction = "bottomright"

        row = box.row(align=True)
        row.operator("view2d.uvkit_align", text="—").direction = "horizontal"
        row.operator("view2d.uvkit_align", text="|").direction = "vertical"

        row = box.row(align=True)
        row.operator("view2d.uvkit_rotate_shell", text="Turn Left").angle = -math.pi / 2
        row.operator("view2d.uvkit_rotate_shell", text="Turn Right").angle = -math.pi / 2

        box = layout.box()
        box.label(text="UV edgeloop tools")

        col = box.column()        

        split = col.split(factor=0.2, align=True)
        split.operator("view2d.uvkit_select_uv_edgering", text="-").mode = "SHRINK"        
        row = split.split(factor=0.8, align=True)
        row.operator("view2d.uvkit_select_uv_edgering", text="Select Ring").mode = "CONTINUOS"
        row.operator("view2d.uvkit_select_uv_edgering", text="+").mode = "EXPAND"  

        split = col.split(factor=0.2, align=True)
        split.operator("view2d.uvkit_select_uv_edgeloop", text="-").mode = "SHRINK"
        row = split.split(factor=0.8, align=True)
        row.operator("view2d.uvkit_select_uv_edgeloop", text="Select Loop").mode = "CONTINUOS"
        row.operator("view2d.uvkit_select_uv_edgeloop", text="+").mode = "EXPAND"

        split = col.split(factor=0.33, align=True)
        split.label(text="Align:")
        split.operator("view2d.uvkit_align_uv_edgeloops", text="X").direction = "X"
        # row = split.split(factor=0.66, align=True)
        split.operator("view2d.uvkit_align_uv_edgeloops", text="Y").direction = "Y"
        split.operator("view2d.uvkit_align_uv_edgeloops", text="Auto").direction = "AUTO"

        
        split = col.split(factor=0.33, align=True)
        split.label(text="Straighten:")
        split.operator("view2d.uvkit_spread_loop", text="Even").mode = "EVEN"
        #row = split.split(factor=0.66, align=True)
        split.operator("view2d.uvkit_spread_loop", text="Geo").mode = "GEOMETRY"
        split.operator("view2d.uvkit_spread_loop", text="Project").mode = "PROJECT"

        col = layout.column()
        
        col.operator("view2d.uvkit_constrained_unwrap", text="Constrained Unwrap")

class IMAGE_MT_uvkit_align_PIE(bpy.types.Menu):
    bl_label = 'UV kit Align'
    bl_idname = 'IMAGE_MT_uvkit_align_pie' 
    
    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()   
    
        # left
        pie.operator("view2d.uvkit_align", text="Left").direction = "left"
        pie.operator("view2d.uvkit_align", text="Right").direction = "right"
        pie.operator("view2d.uvkit_align", text="Bottom").direction = "bottom"
        pie.operator("view2d.uvkit_align", text="Top").direction = "top"
        pie.operator("view2d.uvkit_align", text="Top Left").direction = "topleft"
        pie.operator("view2d.uvkit_align", text="Top Right").direction = "topright"
        pie.operator("view2d.uvkit_align", text="Bottom Left").direction = "bottomleft"
        pie.operator("view2d.uvkit_align", text="Bottom Right").direction = "bottomright"
       

# -------------------------------------------------------------------
#   Register & Unregister
# -------------------------------------------------------------------

classes = [
    #ui panels
    IMAGE_PT_uvkit_main,
    IMAGE_PT_uvkit_imageList,
    IMAGE_MT_uvkit_align_PIE,
]

addon_keymaps = []

def register():    
    for c in classes:
        bpy.utils.register_class(c)

    wm = bpy.context.window_manager     
    if  wm.keyconfigs.addon:
        keymap = wm.keyconfigs.addon.keymaps.new(name='UV Editor', space_type='EMPTY', region_type="WINDOW")

        keymap_item = keymap.keymap_items.new("wm.call_menu_pie", type="NONE", value='PRESS', ctrl=False)
        keymap_item.properties.name = "IMAGE_MT_uvkit_align_pie"         
        addon_keymaps.append((keymap, keymap_item))


def unregister():
    for keymap, keymap_item in addon_keymaps:
        keymap.keymap_items.remove(keymap_item)
    addon_keymaps.clear()   

    for c in reversed(classes):
        bpy.utils.unregister_class(c)

    