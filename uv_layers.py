import bpy
from bpy.app.handlers import persistent
from bpy.props import StringProperty, IntProperty, BoolProperty, CollectionProperty
from bpy.types import PropertyGroup, UIList, Operator, Panel

#region UI

class IMAGE_UL_UVKIT_UVLayerList(UIList):
    """UVKIT Map List"""
    bl_idname = "IMAGE_UL_UVKIT_UVLayerList"

    def draw_item(self, context, layout, data, item, icon, active_data,
                active_propname, index):

        row_main = layout.row()

        if self.layout_type == "COMPACT":
            row_main.prop(item, "name", text="", emboss=False)
            return

        split = row_main.split(factor=0.5, align=True)
        split.prop(item, "name", text="", emboss=False)
        
        row = split.row()
        if item.needs_sync:
            op = row.operator(UVLayerList_OT_NewMap.bl_idname, text='Sync')
            op.uv_layer_name = item.name
            op.mode = "Sync"            
        else:
            row.label(text="")

        row = split.row()
        op = row.operator(UVLayerList_OT_SelectObjectUsingUVmap.bl_idname, text=item.use_count)
        op.uv_layer_name = item.name


class IMAGE_PT_UVKIT_UVLayersPanel(Panel):
    """UVKIT UV Layerlist Panel"""

    bl_label = "UV kit Maps"
    bl_idname = "IMAGE_PT_UVKIT_UVLayersPanel"
    bl_space_type = 'IMAGE_EDITOR'   
    bl_region_type = 'UI'
    bl_category = "Tool"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        can_move_layers = True
        if scene.uvkit_uv_list_index >= 0 and scene.uvkit_uv_list:
            for item in scene.uvkit_uv_list:
                if item.order_mismatch or item.needs_sync:                    
                    can_move_layers = False
                    break
      
        if len(context.selected_objects) > 1 and not can_move_layers:
            row = layout.row()                      
            row.label(text="UV map order not synchronised!", icon="ERROR")
        
        if scene.uvkit_uv_list:
            row = layout.row()
            row.template_list(IMAGE_UL_UVKIT_UVLayerList.bl_idname, "The_List", scene,
                            "uvkit_uv_list", scene, "uvkit_uv_list_index")
        else:
            box = layout.box()	
            if len(context.selected_objects) == 0:
                box.label()
            else:
                box.label(text="Selected objects don't have any uv maps!", icon="ERROR" )
                op = box.operator(UVLayerList_OT_NewMap.bl_idname, text='Create UV map')
                op.uv_layer_name = 'UVMap'
                op.mode = "Sync"

            box.label()
                    
        row = layout.row()
        row.operator(UVLayerList_OT_ListUp.bl_idname, text='Up', icon='TRIA_UP')    
        row.operator(UVLayerList_OT_ListDown.bl_idname, text='Down', icon='TRIA_DOWN')
        row.enabled = can_move_layers

        row = layout.row()
        op = row.operator(UVLayerList_OT_NewMap.bl_idname, text='Copy', icon='EDITMODE_HLT')
        op.uv_layer_name = item.name
        op.mode = "Duplicate"

        op = row.operator(UVLayerList_OT_DeleteMap.bl_idname, text='Delete', icon='TRASH')
        op.uv_layer_name = item.name

        row = layout.row() 
        row.operator(UVLayerList_OT_ListSort_A_to_Z.bl_idname, text='Sort A-Z', icon='SORTALPHA')

        op = row.operator(UVLayerList_OT_SetMapRenderActive.bl_idname, text='Set Render Active', icon='RESTRICT_RENDER_OFF')
        op.uv_layer_name = item.name

class IMAGE_MT_UVKIT_UVLayersMenu(bpy.types.Menu):
  
    bl_idname = "IMAGE_MT_UVKIT_UVLayersMenu"
    bl_label = "UV kit Maps"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'

    def draw(self, context):
        layout = self.layout
    
        layout.separator()
        row = layout.row()
        row.label(text='UV kit Maps:')

        for index, uv in enumerate(context.scene.uvkit_uv_list):
            row = layout.row()
            if index == context.scene.uvkit_uv_list_index:
                text = f"→ {uv.name}"
            else:
                text = f"    {uv.name}"

            op = row.operator(UVLayerList_OT_SwitchMap.bl_idname, text=text)
            op.index = index    


def uvcontext_menu_draw_func(self, context):
    layout = self.layout
    
    if len(context.scene.uvkit_uv_list) < 8:
        layout.menu_contents(IMAGE_MT_UVKIT_UVLayersMenu.bl_idname)
    else:
        layout.menu(IMAGE_MT_UVKIT_UVLayersMenu.bl_idname)

#endregion UI    
#region OPERATORS

class UVLayerList_OT_Update(Operator):
    """ This recreates the data for the uv map list from scratch """

    bl_idname = "uvkit.uv_list_update"
    bl_label = "update the uv map list"

    def execute(self, context):
        global UVLayerProperties_isUpdating
        UVLayerProperties_isUpdating = True

        #print("update uvkit layerlist")
               
        uv_layer_names = []
        unique_uv_layer_names = []
        name_counts = []
        mesh_count = 0
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue
            mesh_count += 1

            uv_layer_names_for_obj = []
            mesh = obj.data
            for uv_map in mesh.uv_layers:
                uv_layer_names_for_obj.append(uv_map.name)

                if uv_map.name in unique_uv_layer_names:
                    index = unique_uv_layer_names.index(uv_map.name)
                    value = name_counts[index]
                    name_counts[index] = value + 1
                else:
                    unique_uv_layer_names.append(uv_map.name)
                    name_counts.append(1)

            uv_layer_names.append(uv_layer_names_for_obj)
            
        # check if the order of the names is always the same
        order_mismatch = False
        if mesh_count > 1:
            for i in range(1, len(uv_layer_names)):                
                if uv_layer_names[0] != uv_layer_names[i]:
                    order_mismatch = True
                    break
            
        context.scene.uvkit_uv_list.clear()
        for index, name in enumerate(unique_uv_layer_names):         
            item = context.scene.uvkit_uv_list.add()
            item.name = name
            item.intial_name = item.name 
            item.use_count = f"{name_counts[index]}/{mesh_count}"
            item.needs_sync = name_counts[index] != mesh_count
            item.order_mismatch = order_mismatch
   
        # lets take the active uv layer from the active_object as a guide to 
        # decide what to select in the uv layer list
        if (context.active_object and
            context.active_object.type == "MESH" and 
            context.active_object in context.selected_objects and 
            context.active_object.data.uv_layers):

            for index, item in enumerate(context.scene.uvkit_uv_list):                
                if item.name == context.active_object.data.uv_layers.active.name:
                    context.scene.uvkit_uv_list_index = index                    
                    break
        else:
            context.scene.uvkit_uv_list_index = 0

        UVLayerProperties_isUpdating = False
        return{'FINISHED'}
    

class UVLayerList_OT_SwitchMap(Operator):
    '''Make uv map active'''
    
    bl_idname = "uvkit_uv_list.switch_map"
    bl_label = "switch the active uv map"
    
    index: IntProperty(name="index", description="", default=0)

    def execute(self, context):
        if self.index != context.scene.uvkit_uv_list_index:
            context.scene.uvkit_uv_list_index = self.index
        return{'FINISHED'}
    
class UVLayerList_OT_SelectObjectUsingUVmap(Operator):
    '''Select objects which are using this uvmap'''

    bl_idname = "uvkit_uv_list.select_objects_using_uvmap"
    bl_label = "Selection objects using this uvmap"
    
    uv_layer_name: StringProperty(name="UVMap", description="", default="UVMap")

    def execute(self, context):
      
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue            
            mesh = obj.data
            uvs = mesh.uv_layers       

            uv_map = uvs.get(self.uv_layer_name)
        
            obj.select_set(uv_map != None)

            if uv_map:
                uv_map.active = True

        if len(context.selected_objects) > 0:
            bpy.context.view_layer.objects.active = context.selected_objects[0]

        return{'FINISHED'}


class UVLayerList_OT_NewMap(Operator):
    """Copy or Sync a uv map"""

    bl_idname = "uvkit.uv_list_new_map"
    bl_label = "Copies or ensures a uv map exists"

    uv_layer_name: StringProperty(name="UVMap", description="", default="UVMap")
    mode: StringProperty(name="Mode", description="", default="Duplicate")
   
    def execute(self, context):
        active_obj = bpy.context.view_layer.objects.active

        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue            
            mesh = obj.data
            uvs = mesh.uv_layers       

            # TODO this might be obsolete already, can add more than 8 uv layers via attributes...
            if len(uvs) == 8:
                self.report({'WARNING'}, f'{obj.name}: UV map limit reached, cannot have more than 8 UV maps.')
                continue    

            if self.mode == "Duplicate":
                copy_active_index = False
            else:
                copy_active_index = True
                if len(uvs) > 0:
                    uvs[0].active = True

            uv_layer = uvs.get(self.uv_layer_name)
            if uv_layer:
                if self.mode == "Duplicate":
                    uv_layer.active = True
                    copy_active_index = True
                else:
                    copy_active_index = False
            
            if not copy_active_index:
                continue

            index = uvs.active_index                
            bpy.context.view_layer.objects.active = obj
            bpy.ops.mesh.uv_texture_add()
            uvs.active.name = self.uv_layer_name
            final_name = uvs.active.name 

            if self.mode == "Duplicate":
                for i in range(index, len(uvs) - 2):                
                    move_to_bottom(obj, index+1)

            uvs[final_name].active = True

        bpy.context.view_layer.objects.active = active_obj
        bpy.ops.uvkit.uv_list_update()
        return{'FINISHED'}


class UVLayerList_OT_DeleteMap(Operator):
    """Deletes uv map"""

    bl_idname = "uvkit.uv_list_delete_map"
    bl_label = "Deletes an uv map"

    uv_layer_name: StringProperty(name="UVMap", description="", default="UVMap")

    @classmethod
    def poll(cls, context):
        return context.scene.uvkit_uv_list

    def execute(self, context):
        active_obj = bpy.context.view_layer.objects.active

        item = context.scene.uvkit_uv_list[context.scene.uvkit_uv_list_index]
       
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue            
            mesh = obj.data
            uvs = mesh.uv_layers           

            uv_layer = uvs.get(self.uv_layer_name)

            if uv_layer:
                uv_layer.active = True
                bpy.context.view_layer.objects.active = obj
                bpy.ops.mesh.uv_texture_remove()         

                original = uvs.get(item.name)  
                if original:
                    original.active = True
            else:
                continue

        bpy.context.view_layer.objects.active = active_obj
        bpy.ops.uvkit.uv_list_update()
        return{'FINISHED'}


class UVLayerList_OT_SetMapRenderActive(Operator):
    """Set uv map active for render"""

    bl_idname = "uvkit.uv_list_set_map_render_active"
    bl_label = "Active render"

    uv_layer_name: StringProperty(name="UVMap", description="", default="UVMap")

    @classmethod
    def poll(cls, context):
        return context.scene.uvkit_uv_list

    def execute(self, context):      
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue            
            mesh = obj.data
            uvs = mesh.uv_layers          

            uv_layer = uvs.get(self.uv_layer_name)
            if uv_layer:
               uv_layer.active_render = True

        return{'FINISHED'}



# see: https://blender.stackexchange.com/questions/67266/changing-order-of-uv-maps
# adapted the code a bit

def set_active_uv_layer(obj, uv_layer_name):
    uvs = obj.data.uv_layers
    uv = uvs.get(uv_layer_name)
    if uv:
        uv.active = True
        return
    
    raise Exception("UVMap not found!")


def move_to_bottom(obj, index):
    """Make sure active object is set correctly before calling this"""

    # uvs = obj.data.uv_layers
    uvs = obj.data.uv_layers
    uvs.active_index = index
    new_name = uvs.active.name

    bpy.ops.mesh.uv_texture_add()

    # delete the "old" one
    set_active_uv_layer(obj, new_name)
    bpy.ops.mesh.uv_texture_remove()

    # set the name of the last one
    uvs.active_index = len(uvs) - 1
    uvs.active.name = new_name


def move_one_down(obj, uvs):    
    # get the selected UV map
    original_index = uvs.active_index
    original_name = uvs.active.name

    if original_index == len(uvs) - 1:
        return

    # use "trick" on the one after it
    move_to_bottom(obj, original_index + 1)

    # use the "trick" on the UV map
    move_to_bottom(obj, original_index)

    # use the "trick" on the rest that are after where it was
    for i in range(original_index, len(uvs) - 2):
        move_to_bottom(obj, original_index)
    
    set_active_uv_layer(obj, original_name)


class UVLayerList_OT_ListDown(bpy.types.Operator):
    bl_idname = "uvkit.uv_list_move_slot_down"
    bl_label = "Move Down"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Move uv map down in the list slots"

    def execute(self, context):               
        active_obj = bpy.context.view_layer.objects.active
        for obj in bpy.context.selected_objects:
            if obj.type != 'MESH':
                continue

            bpy.context.view_layer.objects.active = obj
            uvs = obj.data.uv_layers
            move_one_down(obj, uvs)            

        bpy.context.view_layer.objects.active = active_obj

        bpy.ops.uvkit.uv_list_update()

        index = bpy.context.scene.uvkit_uv_list_index
        list_length = len(bpy.context.scene.uvkit_uv_list) - 1
        new_index = index + 1
        bpy.context.scene.uvkit_uv_list_index = max(0, min(new_index, list_length))

        return {'FINISHED'}


class UVLayerList_OT_ListUp(bpy.types.Operator):
    bl_idname = "uvkit.uv_list_move_slot_up"
    bl_label = "Move Up"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Move uv map up in the list slots"

    def execute(self, context):
        active_obj = context.view_layer.objects.active

        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue

            uvs = obj.data.uv_layers

            if uvs.active_index == 0:
                continue
            
            uvs.active_index -= 1
            context.view_layer.objects.active = obj
            move_one_down(obj, uvs)
           
        context.view_layer.objects.active = active_obj

        bpy.ops.uvkit.uv_list_update()

        index = bpy.context.scene.uvkit_uv_list_index
        list_length = len(bpy.context.scene.uvkit_uv_list) - 1
        new_index = index - 1
        bpy.context.scene.uvkit_uv_list_index = max(0, min(new_index, list_length))
        
        return {'FINISHED'}


class UVLayerList_OT_ListSort_A_to_Z (bpy.types.Operator):
    bl_idname = 'uvkit.uv_list_sort_maps_a_to_z'
    bl_label = 'Sort UV map slots A to Z'
    bl_description = "Sorting UV map slots by name (A to Z)"
    bl_options = {"REGISTER", "UNDO"}
  
    def execute(self, context):   
        active_obj = context.view_layer.objects.active

        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue
            
            context.view_layer.objects.active = obj

            uvs = obj.data.uv_layers
            original_name = uvs.active.name
            
            for j in range (len(uvs)):
                for i in range (len(uvs)-1):
                    uvs.active_index = i
                    temp_name = uvs.active.name
                    uvs.active_index = i+1
                    if uvs.active.name < temp_name:                   
                        uvs.active_index -= 1
                        context.view_layer.objects.active = obj
                        move_one_down(obj, uvs)
                                                           
                        
            set_active_uv_layer(obj, original_name)

        context.view_layer.objects.active = active_obj   
        bpy.ops.uvkit.uv_list_update()  
        return {"FINISHED"}
    
#endregion OPERATORS
#region CALLBACKS

@persistent
def load_handler(dummy):
    subscribe_msgbus(subscription_owner)

prev_operator = None
prev_selected_objects = set()

@persistent
def depsgraph_update_handler(scene):
    if  UVLayerProperties_isUpdating:
        return
    
    global prev_operator  
    if (bpy.context.active_operator and 
        prev_operator != bpy.context.active_operator and 
        (
        bpy.context.active_operator.name == 'Add UV Map' or
        bpy.context.active_operator.name == 'Remove UV Map' 
        )):
        
        prev_operator = bpy.context.active_operator       
        bpy.ops.uvkit.uv_list_update()
        return

    global prev_selected_objects  
    current_selected_objects = set(bpy.context.selected_objects)
    if current_selected_objects != prev_selected_objects:
        prev_selected_objects = current_selected_objects
        bpy.ops.uvkit.uv_list_update()
        return


def msgbus_notification_handler(*args):
    if  UVLayerProperties_isUpdating:
        return
     
    bpy.ops.uvkit.uv_list_update()  

subscription_owner = object()
def subscribe_msgbus(subscription_owner):    
    subscribe_to = bpy.types.MeshUVLoopLayer, "name"
    bpy.msgbus.subscribe_rna(
        key=subscribe_to,
        owner=subscription_owner,
        args=("name",),
        notify=msgbus_notification_handler,
        options={"PERSISTENT",}
    )

    subscribe_to = bpy.types.UVLoopLayers, "active_index"
    bpy.msgbus.subscribe_rna(
        key=subscribe_to,
        owner=subscription_owner,
        args=("active_index",),
        notify=msgbus_notification_handler,
        options={"PERSISTENT",}
    )   

def unsubscribe_msgbus(subscription_owner):
    if subscription_owner is not None:
        bpy.msgbus.clear_by_owner(subscription_owner)


def listIndex_update_handler(self, context):
    uv_properties = context.scene.uvkit_uv_list[context.scene.uvkit_uv_list_index]

    for obj in bpy.context.selected_objects:
        if obj.type != 'MESH':
            continue
        
        mesh = obj.data
        for uv_map in mesh.uv_layers:
            if uv_map.name == uv_properties.name:
                uv_map.active = True
                break


UVLayerProperties_isUpdating = False
def UVLayerProperties_Update(self, context):
    """This gets called when a rename in the custom uvlayer list happens."""
    if  UVLayerProperties_isUpdating:
        return

    print(f"update uv name: {self.intial_name} to {self.name}" )
    for obj in bpy.context.selected_objects:
        if obj.type != 'MESH':
            continue
        
        mesh = obj.data
        uvs = mesh.uv_layers

        uv_layer = uvs.get(self.intial_name)
        if uv_layer: uv_layer.name = self.name

    bpy.ops.uvkit.uv_list_update()

#endregion CALLBACKS
#region DATA

class UVLayerProperties(PropertyGroup):
    """Group of properties representing an item in the list."""

    name: StringProperty(
        name="Name",
        description="Name of this uv layer",    
        default="UVMap",
        update=UVLayerProperties_Update,
        )
    intial_name: StringProperty(
        name="Intial_Name",
        description="Name of this uv layer before changed",    
        default="UVMap"        
        )

    use_count: StringProperty(
        name="Use count",
        description="Amount of objects using this uv layer name",
        default="")
    
    needs_sync: BoolProperty(
        name="Needs Sync",
        description="UVlayer not present on all selected objects",
        default=False)
    
    order_mismatch: BoolProperty(
        name="Order mismatch",
        description="Order of uv layers is  different between objects",
        default=False)
    
#endregion DATA
#region REGISTER / UNREGISTER

classes = [
    UVLayerProperties,
    UVLayerList_OT_Update,
    UVLayerList_OT_SwitchMap,
    UVLayerList_OT_SelectObjectUsingUVmap,
    UVLayerList_OT_NewMap,
    UVLayerList_OT_DeleteMap,
    UVLayerList_OT_SetMapRenderActive,
    UVLayerList_OT_ListUp,
    UVLayerList_OT_ListDown,
    UVLayerList_OT_ListSort_A_to_Z,
    IMAGE_UL_UVKIT_UVLayerList,
    IMAGE_PT_UVKIT_UVLayersPanel,
    IMAGE_MT_UVKIT_UVLayersMenu,
]

def register():
    for c in classes:
        bpy.utils.register_class(c)
   
    bpy.types.Scene.uvkit_uv_list = CollectionProperty(type = UVLayerProperties)
    bpy.types.Scene.uvkit_uv_list_index = IntProperty(name = "Active UVMap index",
                                            default = 0,
                                            update=listIndex_update_handler)
    subscribe_msgbus(subscription_owner)
    
    if depsgraph_update_handler not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(depsgraph_update_handler)
    
    if load_handler not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(load_handler)

    bpy.types.IMAGE_MT_uvs_context_menu.append(uvcontext_menu_draw_func)


def unregister():
    bpy.types.IMAGE_MT_uvs_context_menu.remove(uvcontext_menu_draw_func)

    if depsgraph_update_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update_handler)

    if load_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_handler)

    unsubscribe_msgbus(subscription_owner)
    
    for c in reversed(classes):
        bpy.utils.unregister_class(c)

    del bpy.types.Scene.uvkit_uv_list
    del bpy.types.Scene.uvkit_uv_list_index

#endregion REGISTER / UNREGISTER