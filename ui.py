import bpy
from bpy.types import Panel

from . import utils
from .utils import fetch_user_preferences, return_false_when

import itertools
from rna_keymap_ui import _indented_layout


def draw_bool_prop_icon(layout, data, property_name, icon_true, icon_false, emboss=False):
    icon = icon_true if getattr(data, property_name) else icon_false
    layout.prop(data, property_name, icon_only=True, icon=icon, emboss=emboss)


def draw_data_block(layout, data_block):
    icon_dict = {
        "OBJECT": "OBJECT_DATA",
        "COLLECTION": "OUTLINER_COLLECTION",
        "MATERIAL": "MATERIAL_DATA",
        "IMAGE": "IMAGE_DATA",
        "TEXTURE": "TEXTURE_DATA",
    }

    icon = icon_dict[data_block.id_type]
    layout.label(text=f"{data_block.name}", icon=icon)


def collapsible_row(layout, data, property_name, text, icon="NONE"):
    row = layout.row(align=True)
    toggle_state = getattr(data, property_name)

    if toggle_state:
        row.prop(data, property_name, icon_only=True, icon="DOWNARROW_HLT", emboss=False)
    else:
        row.prop(data, property_name, icon_only=True, icon="RIGHTARROW", emboss=False)

    row.label(text=text, icon=icon)
    return toggle_state


class NODE_PT_personal_settings(Panel):
    bl_label = "Personal Settings"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "HEADER"
    bl_ui_units_x = 7

    def draw(self, context):
        layout = self.layout
        layout.label(text="Personal Settings")

        prefs = context.preferences

        node_editor_prefs = prefs.themes["Default"].node_editor

        col = layout.column()
        col.use_property_decorate = True
        col.prop(node_editor_prefs, "noodle_curving")
        col.prop(prefs.inputs, "use_mouse_emulate_3_button")
        col.prop(prefs.view, "show_developer_ui")


class NODE_PT_nodegroup_names_and_descriptions(Panel):
    bl_label = "Group Descriptions"
    bl_category = "Node"
    bl_region_type = "UI"
    bl_space_type = "NODE_EDITOR"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    @return_false_when(AttributeError)
    def poll(cls, context):
        return context.active_node.select and context.active_node.node_tree is not None

    def draw(self, context):
        layout = self.layout
        layout.column(align=True)
        active_node = context.active_node
        tree = active_node.node_tree

        sort_function = lambda i: i.in_out if hasattr(i, "in_out") else i.item_type
        items_tree = sorted(tree.interface.items_tree, key=sort_function)

        for k, v in itertools.groupby(items_tree, key=sort_function):
            row = layout.row()
            split = row.split(factor=0.3)
            col1 = split.column()
            col2 = split.column()

            col1.label(text=f"{k.title()}:")
            col2.label(text="Description:")

            if k == "PANEL":
                for item in v:
                    col1.prop(item, "name", icon_only=True)
                    col2.prop(item, "description", icon_only=True)
            else:
                i = 0
                for sub_k, sub_v in itertools.groupby(v, key=lambda i: i.parent):
                    # Check if base panel, which has no parents
                    if sub_k.parent is not None:
                        col1.separator(factor=0.5)
                        col2.separator(factor=0.5)

                    for item in sub_v:
                        row = col1.row()
                        if k == "INPUT":
                            corresponding_socket = active_node.inputs[i]
                        else:
                            corresponding_socket = active_node.outputs[i]

                        row.template_node_socket(color=corresponding_socket.draw_color_simple())
                        row.prop(item, "name", icon_only=True)
                        col2.prop(item, "description", icon_only=True)

                        i += 1


class NODE_PT_menu_switch_all_descriptions(Panel):
    bl_label = "Menu Switch Descriptions"
    bl_region_type = "UI"
    bl_space_type = "NODE_EDITOR"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    @return_false_when(AttributeError)
    def poll(cls, context):
        return context.active_node.bl_idname == "GeometryNodeMenuSwitch" and context.active_node.select

    def draw(self, context):
        layout = self.layout
        layout.column(align=True)
        row = layout.row()
        split = row.split(factor=0.3)
        col1 = split.column()
        col1.alignment = "RIGHT"
        col2 = split.column()

        for item in context.active_node.enum_definition.enum_items:
            col1.prop(item, "name", icon_only=True)
            col2.prop(item, "description", icon_only=True)


class NODE_PT_group_utils(Panel):
    bl_label = "Group Utils"
    bl_category = "Group"
    bl_region_type = "UI"
    bl_space_type = "NODE_EDITOR"

    def draw(self, context):
        layout = self.layout
        prefs = fetch_user_preferences()

        layout.prop(prefs, "unhide_virtual_sockets")
        layout.operator("node.hide_unused_sockets")
        layout.operator("node.pin_editor")


class NODE_PT_node_info(Panel):
    bl_label = "Node Info"
    bl_category = "Node"
    bl_region_type = "UI"
    bl_space_type = "NODE_EDITOR"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    @return_false_when(AttributeError)
    def poll(cls, context):
        return context.active_node is not None

    def draw(self, context):
        layout = self.layout
        layout = layout.row()
        layout.alignment = "CENTER"

        props = (
            "bl_idname",
            "bl_label",
            "type",
            "bl_rna",
        )

        col1 = layout.column()
        col2 = layout.column()
        col3 = layout.column()
        col1.alignment = "RIGHT"
        col2.alignment = "LEFT"
        col1.ui_units_x = 10

        active_node = context.active_node
        try:
            location = f"({active_node.location.x:.2f}, {active_node.location.y:.2f})"
            size = f"({active_node.width:.2f}, {utils.get_height(active_node):.2f})"
            dimensions = f"({active_node.dimensions.x:.2f}, {active_node.dimensions.y:.2f})"
        except (ZeroDivisionError, ValueError):
            size = "None"
            dimensions = "None"

        prop_info = list((prop_name, str(getattr(active_node, prop_name))) for prop_name in props)
        prop_info.extend([("size", size), ("dimensions", dimensions), ("location", location)])

        for prop, prop_value in prop_info:
            col1.label(text=prop)
            col2.label(text=prop_value)
            col3.operator("node.copy_to_clipboard", text="", icon="COPYDOWN").attribute = prop_value


class NODE_PT_node_coordinates(Panel):
    bl_label = "Node Coordinates"
    bl_category = "Node"
    bl_region_type = "UI"
    bl_space_type = "NODE_EDITOR"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        return context.active_node is not None

    def draw(self, context):
        layout = self.layout

        split = layout.split(factor=0.3)
        col1 = split.column()
        col1.alignment = "RIGHT"
        col2 = split.column()
        col2.alignment = "LEFT"

        active_node = context.active_node
        left, right, bottom, top = utils.get_bounds((active_node,))

        col1.label(text="node:")
        col2.label(text=str(active_node))

        col1.label(text="left")
        col1.label(text="center")
        col1.label(text="right")
        col1.label(text="bottom")
        col1.label(text="middle")
        col1.label(text="top")

        col2.label(text=str(left))
        col2.label(text=str(utils.get_center(active_node)))
        col2.label(text=str(right))
        col2.label(text=str(bottom))
        col2.label(text=str(utils.get_middle(active_node)))
        col2.label(text=str(top))

        layout.operator("node.troubleshoot_corners")


class NODE_PT_asset_operators(Panel):
    bl_label = "Asset Operations"
    bl_category = "Assets"
    bl_region_type = "UI"
    bl_space_type = "NODE_EDITOR"

    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)
        row.operator("node.multiple_asset_mark")
        row.operator("node.multiple_asset_clear")

        row = layout.row(align=True)
        row.operator("node.multiple_fake_user_set")
        row.operator("node.multiple_fake_user_clear")

        row = layout.row(align=True)
        row.operator("node.multiple_make_local")
        row = layout.row(align=True)
        row.operator("node.multiple_make_local_all")


def draw_personal_settings(self, context):
    self.layout.popover(panel="NODE_PT_personal_settings", text="", icon="PREFERENCES")


class NODE_PT_object_data_selector(Panel):
    bl_label = "Data Selector"
    bl_category = "Group"
    bl_region_type = "UI"
    bl_space_type = "NODE_EDITOR"

    @classmethod
    def poll(cls, context):
        tree = context.space_data.edit_tree
        has_tree = context.space_data.edit_tree is not None
        has_group = hasattr(context.active_node, "node_tree")

        return all((has_tree, has_group))

    def draw(self, context):
        layout = self.layout
        node_tree = context.active_node.node_tree

        # layout.prop(node_tree, "test_object_prop", text='', icon='LIGHT')
        # layout.prop(node_tree, "test_object_prop", text='')
        layout.prop_search(node_tree, "test_object_prop", context.scene, "objects", text="")


def data_selector_callback(self, context):
    if self.name.startswith("Object Info"):
        object_name = self.test_object_prop

        self.name = f"Object Info - ({object_name})"

        nodes = self.nodes
        nodes["location"].attribute_name = f'objects["{object_name}"].location'


class NODE_PT_reroutes_to_switch(Panel):
    bl_label = "Reroutes to Switch"
    bl_category = "Reroutes"
    bl_region_type = "UI"
    bl_space_type = "NODE_EDITOR"

    @classmethod
    def poll(cls, context):
        return context.space_data.edit_tree

    def draw(self, context):
        layout = self.layout
        prefs = utils.fetch_user_preferences()

        prefs.draw_enum_property(layout, "switch_type")
        prefs.draw_enum_property(layout, "reroute_merge_type")
        layout.prop(prefs, "switch_count")

        layout.operator("node.merge_reroutes_to_switch")
        layout.operator("node.convert_switch_type")
        layout.operator("node.menu_switch_to_enum")


class NODE_PT_math_node_convert(Panel):
    bl_label = "Convert Math Nodes"
    bl_category = "Math Nodes"
    bl_region_type = "UI"
    bl_space_type = "NODE_EDITOR"

    @classmethod
    def poll(cls, context):
        return context.space_data.edit_tree

    def draw(self, context):
        layout = self.layout
        layout.operator("node.convert_math_node")


class NODE_PT_group_inputs(Panel):
    bl_label = "Group Inputs"
    bl_category = "Group"
    bl_region_type = "UI"
    bl_space_type = "NODE_EDITOR"

    @classmethod
    def poll(cls, context):
        return context.space_data.edit_tree

    def draw(self, context):
        layout = self.layout
        prefs = utils.fetch_user_preferences()

        layout.operator("node.merge_group_input")
        row = layout.row(align=True)
        row.operator("node.split_group_input", text="Split by Sockets").split_by = "SOCKETS"
        row.operator("node.split_group_input", text="Split by Links").split_by = "LINKS"


class NODE_PT_replace_group(Panel):
    bl_label = "Replace Group"
    bl_category = "Node"
    bl_region_type = "UI"
    bl_space_type = "NODE_EDITOR"

    @classmethod
    def poll(cls, context):
        active_node = context.active_node
        return hasattr(active_node, "node_tree") and active_node.select

    def draw(self, context):
        layout = self.layout
        prefs = utils.fetch_user_preferences()

        wm = context.window_manager
        layout.prop(wm, "nodegroup_to_replace", text="")
        layout.prop(prefs, "show_hidden_nodegroups")
        layout.operator("NODE_OT_batch_replace_group")


if bpy.app.version >= (4, 3, 0):
    classes = (
        NODE_PT_personal_settings,
        NODE_PT_group_utils,
        NODE_PT_node_info,
        NODE_PT_asset_operators,
        # NODE_PT_node_coordinates,
        # NODE_PT_nodegroup_names_and_descriptions,
        NODE_PT_object_data_selector,
        NODE_PT_reroutes_to_switch,
        NODE_PT_math_node_convert,
        NODE_PT_group_inputs,
        NODE_PT_replace_group,
    )
else:
    classes = (
        NODE_PT_personal_settings,
        NODE_PT_group_utils,
        NODE_PT_node_info,
        NODE_PT_asset_operators,
        # NODE_PT_node_coordinates,
        # NODE_PT_nodegroup_names_and_descriptions,
        NODE_PT_object_data_selector,
        NODE_PT_reroutes_to_switch,
        NODE_PT_group_inputs,
        NODE_PT_replace_group,
    )


def replace_nodegroup_poll(self, object):
    tree = bpy.context.space_data.edit_tree
    group = object

    return (
        group.bl_idname == tree.bl_idname
        and not group.contains_tree(tree)
        and (not group.name.startswith(".") or fetch_user_preferences("show_hidden_nodegroups"))
    )


def register():
    if bpy.app.version >= (4, 2, 0):
        if hasattr(NODE_PT_menu_switch_all_descriptions, "bl_parent_id"):
            delattr(NODE_PT_menu_switch_all_descriptions, "bl_parent_id")
        NODE_PT_menu_switch_all_descriptions.bl_category = "Node"
    else:
        if hasattr(NODE_PT_menu_switch_all_descriptions, "bl_category"):
            delattr(NODE_PT_menu_switch_all_descriptions, "bl_category")
        NODE_PT_menu_switch_all_descriptions.bl_parent_id = "NODE_PT_active_node_properties"

    for cls in classes:
        bpy.utils.register_class(cls)

    if bpy.app.version >= (4, 1, 0):
        bpy.utils.register_class(NODE_PT_menu_switch_all_descriptions)

    bpy.types.NODE_HT_header.append(draw_personal_settings)

    bpy.types.NodeTree.test_object_prop = bpy.props.StringProperty(update=data_selector_callback)

    bpy.types.WindowManager.nodegroup_to_replace = bpy.props.PointerProperty(
        name="Group to Replace",
        type=bpy.types.NodeTree,
        poll=replace_nodegroup_poll,
    )
    # bpy.types.NodeTree.test_object_prop = PointerProperty(type=bpy.types.Object, update=data_selector_callback)
    # bpy.types.NodeTree.test_object_prop = PointerProperty(type=bpy.types.Object, poll=lambda self, object: object.type == 'LIGHT')


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    if bpy.app.version >= (4, 1, 0):
        bpy.utils.unregister_class(NODE_PT_menu_switch_all_descriptions)

    bpy.types.NODE_HT_header.remove(draw_personal_settings)
    del bpy.types.NodeTree.test_object_prop
    del bpy.types.WindowManager.nodegroup_to_replace


if __name__ == "__main__":
    register()
