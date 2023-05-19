import bpy

from bpy.props import (IntProperty,
                       BoolProperty,
                       StringProperty,
                       CollectionProperty,
                       PointerProperty)

from bpy.types import (Operator,
                       Panel,
                       PropertyGroup,
                       UIList)


class IMAGE_PT_uvkit_imageList(bpy.types.Menu):
    # heavily copied from Reinier Goijvaerts
    bl_idname = "uvkit_imageList"
    bl_label = "Images from material"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'

    def draw(self, context):
        layout = self.layout        
        
        active_mat = bpy.context.active_object.active_material        
        if active_mat.use_nodes:
            for node in active_mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE':
                    image = node.image

                    if image is not None:
                        button = layout.operator("view2d.uvkit_show_image", text=image.name, icon_value=layout.icon(image))
                        button.image_name = image.name


class IMAGE_PT_uvkit_main(Panel):
    bl_idname = "UVKIT_PT_main"
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

        layout.menu("uvkit_imageList")
        
        if not show_uvedit:
            return

        mesh = context.edit_object.data

        box = layout.box()
        row = box.row()
        col = row.column()

        row.prop_search(mesh.uv_layers, "active", mesh, "uv_layers", text="")
       
        row.operator("mesh.uv_texture_add", icon='ADD', text="")
        row.operator("mesh.uv_texture_remove", icon='REMOVE', text="")


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

        

# -------------------------------------------------------------------
#   Register & Unregister
# -------------------------------------------------------------------

classes = [
    #ui panels
    IMAGE_PT_uvkit_main,
    IMAGE_PT_uvkit_imageList,
]


def register():    
    for c in classes:
        bpy.utils.register_class(c)

def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)

    