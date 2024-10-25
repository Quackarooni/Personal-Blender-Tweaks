import bpy
from bpy.types import Panel

from . import utils
from .utils import fetch_user_preferences

import itertools
from rna_keymap_ui import _indented_layout


def draw_bool_prop_icon(
    layout, data, property_name, icon_true, icon_false, emboss=False
):
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
        row.prop(
            data, property_name, icon_only=True, icon="DOWNARROW_HLT", emboss=False
        )
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
    def poll(cls, context):
        try:
            return (
                context.active_node.select and context.active_node.node_tree is not None
            )
        except AttributeError:
            return False

    def draw(self, context):
        layout = self.layout
        layout.column(align=True)
        active_node = context.active_node

        try:
            tree = active_node.node_tree
        except AttributeError:
            return

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

                        row.template_node_socket(
                            color=corresponding_socket.draw_color_simple()
                        )
                        row.prop(item, "name", icon_only=True)
                        col2.prop(item, "description", icon_only=True)

                        i += 1


class NODE_PT_menu_switch_all_descriptions(Panel):
    bl_label = "Menu Switch Descriptions"
    bl_region_type = "UI"
    bl_space_type = "NODE_EDITOR"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        try:
            return (
                context.active_node.bl_idname == "GeometryNodeMenuSwitch"
                and context.active_node.select
            )
        except AttributeError:
            return False

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
    def poll(cls, context):
        try:
            return context.active_node is not None
        except AttributeError:
            return False

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
            size = str(tuple(active_node.dimensions))
            dimensions = str((active_node.width, utils.get_height(active_node)))
        except ZeroDivisionError:
            size = "None"
            dimensions = "None"

        prop_info = list(
            (prop_name, str(getattr(active_node, prop_name))) for prop_name in props
        )
        prop_info.extend(
            [
                ("size", size),
                ("dimensions", dimensions),
            ]
        )

        for prop, prop_value in prop_info:
            col1.label(text=prop)
            col2.label(text=prop_value)
            col3.operator(
                "node.copy_to_clipboard", text="", icon="COPYDOWN"
            ).attribute = prop_value


class NODE_PT_node_coordinates(Panel):
    bl_label = "Node Coordinates"
    bl_category = "Node"
    bl_region_type = "UI"
    bl_space_type = "NODE_EDITOR"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        try:
            return context.active_node is not None
        except AttributeError:
            return False

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


class NODE_PT_node_cleanup(Panel):
    bl_label = "Node Cleanup"
    bl_category = "Options"
    bl_region_type = "UI"
    bl_space_type = "NODE_EDITOR"

    @classmethod
    def poll(cls, context):
        return context.space_data.edit_tree is not None

    @staticmethod
    def draw_invisible_links(layout, context):
        links = context.space_data.edit_tree.links
        invisible_links = utils.filter_hidden_links(links, as_tuple=True)

        row = layout.row(align=True)
        row.alignment = "CENTER"

        if len(invisible_links) <= 0:
            row.label(text="No invisible links found.")

        else:
            col1 = row.column()
            col2 = row.column()
            for link in invisible_links:
                row = col1.row(align=True)
                row.alignment = "LEFT"
                row.template_node_socket(color=link.from_socket.draw_color_simple())
                row.label(text=f"{link.from_node.bl_label} ({link.from_socket.name})")

                row = col2.row(align=True)
                row.alignment = "LEFT"
                draw_bool_prop_icon(
                    row, link, "is_muted", icon_true="PANEL_CLOSE", icon_false="FORWARD"
                )

                row.template_node_socket(color=link.to_socket.draw_color_simple())
                row.label(text=f"{link.to_node.bl_label} ({link.to_socket.name})")

    @staticmethod
    def draw_uncleared_data_blocks(layout, context):
        row = layout.row(align=True)
        row.alignment = "CENTER"

        icon_dict = {
            "OBJECT": "OBJECT_DATA",
            "COLLECTION": "OUTLINER_COLLECTION",
            "MATERIAL": "MATERIAL_DATA",
            "IMAGE": "IMAGE_DATA",
            "TEXTURE": "TEXTURE_DATA",
        }
        collection_icon_dict = {
            "NONE": "OUTLINER_COLLECTION",
            "COLOR_01": "COLLECTION_COLOR_01",
            "COLOR_02": "COLLECTION_COLOR_02",
            "COLOR_03": "COLLECTION_COLOR_03",
            "COLOR_04": "COLLECTION_COLOR_04",
            "COLOR_05": "COLLECTION_COLOR_05",
            "COLOR_06": "COLLECTION_COLOR_06",
            "COLOR_07": "COLLECTION_COLOR_07",
            "COLOR_08": "COLLECTION_COLOR_08",
        }

        links = context.space_data.edit_tree.links
        data_block_info = utils.filter_hidden_data_blocks(links, as_tuple=True)

        if len(data_block_info) <= 0:
            row.label(text="No hidden data-blocks found.")

        else:
            col1 = row.column()
            col2 = row.column()

            for link, socket, data_block in data_block_info:
                socket = link.to_socket

                row = col1.row(align=True)
                row.alignment = "LEFT"

                row.template_node_socket(color=socket.draw_color_simple())
                row.label(text=f"{link.to_node.bl_label} ({socket.name})")

                row = col2.row(align=True)
                row.alignment = "LEFT"
                draw_bool_prop_icon(
                    row, link, "is_muted", icon_true="PANEL_CLOSE", icon_false="FORWARD"
                )
                draw_data_block(row, data_block)

    @staticmethod
    def draw_group_data_blocks(layout, context, in_out):
        tree = context.space_data.edit_tree
        sockets = utils.get_data_block_defaults(tree, in_out=in_out, as_tuple=True)

        indent = _indented_layout(layout, level=1)
        indent.label(text="Inputs:" if in_out == "INPUT" else "Outputs:")
        row = layout.row(align=True)
        row.alignment = "CENTER"

        color_dict = {
            "NodeSocketObject": (
                0.9300000071525574,
                0.6200000047683716,
                0.36000001430511475,
                1.0,
            ),
            "NodeSocketCollection": (
                0.9599999785423279,
                0.9599999785423279,
                0.9599999785423279,
                1.0,
            ),
            "NodeSocketMaterial": (
                0.9200000166893005,
                0.46000000834465027,
                0.5099999904632568,
                1.0,
            ),
            "NodeSocketImage": (
                0.38999998569488525,
                0.2199999988079071,
                0.38999998569488525,
                1.0,
            ),
            "NodeSocketTexture": (
                0.6200000047683716,
                0.3100000023841858,
                0.6399999856948853,
                1.0,
            ),
        }

        if len(sockets) <= 0:
            row.label(text="No data-block defaults found.")

        else:
            col1 = row.column()
            col2 = row.column()

            for socket, data_block in sockets:
                row = col1.row(align=True)
                row.alignment = "LEFT"
                row.template_node_socket(color=color_dict[socket.socket_type])
                row.label(text=f"{socket.name}")

                row = col2.row()
                row.alignment = "LEFT"

                row.label(text="", icon="REMOVE")
                draw_data_block(row, data_block)

    def draw(self, context):
        layout = self.layout
        prefs = fetch_user_preferences()
        tree = context.space_data.edit_tree

        if collapsible_row(
            layout, prefs, "show_invisible_links", text="Invisible Links"
        ):
            self.draw_invisible_links(layout, context)
        layout.operator("node.clean_invisible_links")

        # Only GeometryNodeTrees support data-block sockets so skip for other node tree types
        if tree.bl_idname == "GeometryNodeTree":
            if collapsible_row(
                layout, prefs, "show_hidden_data_blocks", text="Hidden Data-Blocks"
            ):
                self.draw_uncleared_data_blocks(layout, context)
            layout.operator("node.clean_hidden_data_blocks")

            if collapsible_row(
                layout,
                prefs,
                "show_group_data_block_defaults",
                text="Group Data-Block Defaults",
            ):
                self.draw_group_data_blocks(layout, context, in_out="INPUT")
                self.draw_group_data_blocks(layout, context, in_out="OUTPUT")
            layout.operator("node.clean_data_block_defaults")


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
        layout.prop_search(
            node_tree, "test_object_prop", context.scene, "objects", text=""
        )


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
        row.operator(
            "node.split_group_input", text="Split by Sockets"
        ).split_by = "SOCKETS"
        row.operator("node.split_group_input", text="Split by Links").split_by = "LINKS"


if bpy.app.version >= (4, 3, 0):
    classes = (
        NODE_PT_personal_settings,
        NODE_PT_group_utils,
        NODE_PT_node_info,
        NODE_PT_asset_operators,
        # NODE_PT_node_coordinates,
        NODE_PT_nodegroup_names_and_descriptions,
        NODE_PT_node_cleanup,
        NODE_PT_object_data_selector,
        NODE_PT_reroutes_to_switch,
        NODE_PT_math_node_convert,
        NODE_PT_group_inputs,
    )
else:
    classes = (
        NODE_PT_personal_settings,
        NODE_PT_group_utils,
        NODE_PT_node_info,
        NODE_PT_asset_operators,
        # NODE_PT_node_coordinates,
        NODE_PT_nodegroup_names_and_descriptions,
        NODE_PT_node_cleanup,
        NODE_PT_object_data_selector,
        NODE_PT_reroutes_to_switch,
        NODE_PT_group_inputs,
    )


def register():
    if bpy.app.version >= (4, 2, 0):
        if hasattr(NODE_PT_menu_switch_all_descriptions, "bl_parent_id"):
            delattr(NODE_PT_menu_switch_all_descriptions, "bl_parent_id")
        NODE_PT_menu_switch_all_descriptions.bl_category = "Node"
    else:
        if hasattr(NODE_PT_menu_switch_all_descriptions, "bl_category"):
            delattr(NODE_PT_menu_switch_all_descriptions, "bl_category")
        NODE_PT_menu_switch_all_descriptions.bl_parent_id = (
            "NODE_PT_active_node_properties"
        )

    for cls in classes:
        bpy.utils.register_class(cls)

    if bpy.app.version >= (4, 1, 0):
        bpy.utils.register_class(NODE_PT_menu_switch_all_descriptions)

    bpy.types.NODE_HT_header.append(draw_personal_settings)

    bpy.types.NodeTree.test_object_prop = bpy.props.StringProperty(
        update=data_selector_callback
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


if __name__ == "__main__":
    register()
