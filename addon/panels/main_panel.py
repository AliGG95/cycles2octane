import bpy

from ..utility.material_functions import get_materials_selected


class COC_PT_ObjPanel(bpy.types.Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Octane Tools'
    bl_context = ''

    @classmethod
    def poll(cls, context):
        if bpy.data.scenes["Scene"].render.engine != 'octane':
            return False
        return not (False)


class COC_PT_MainPanel(COC_PT_ObjPanel):
    bl_label = "Cycles2Octane"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        pass


class COC_PT_NodeConverter(COC_PT_ObjPanel):
    """Convert Materials"""

    bl_label = "Material Converter"
    bl_parent_id = "COC_PT_MainPanel"

    def draw(self, context):
        layout = self.layout
        props = context.scene.cycles2octane

        # Create box for selection method
        box = layout.box()
        col = box.column(align=False)
        col.separator(factor=1)
        col.prop(props, "select_method")
        col.separator(factor=1)
        
        # Create box for selected materials info and convert button
        box = layout.box()
        col = box.column(align=False)
        col.separator(factor=1)
        
        selected_materials = len(get_materials_selected())
        col.label(text=str(selected_materials) +
                  (" Material Selected" if selected_materials == 1 else " Materials Selected"))
        
        row = col.row(align=True)
        row.scale_y = 1.3
        row.operator("coc.convert_nodes", text=" Convert to Octane", icon="NODETREE")
        col.separator(factor=1)