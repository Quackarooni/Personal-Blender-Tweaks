import bpy
import re

from bpy.types import NodeSocketVirtual, Operator
from bpy.props import BoolProperty, EnumProperty, StringProperty

from collections import Counter
from itertools import zip_longest
from math import ceil
from mathutils import Vector

from .utils import fetch_user_preferences, return_false_when
from . import utils


class NODE_OT_pin_node_editor(Operator):
    bl_idname = "node.pin_editor"
    bl_label = "Pin Node Editor"
    bl_options = {"REGISTER", "UNDO_GROUPED"}

    @classmethod
    def poll(cls, context):
        return context.space_data.node_tree is not None

    def execute(self, context):
        pin_status = not (context.space_data.pin)
        context.space_data.pin = pin_status

        if pin_status:
            self.report({"INFO"}, f"NODE EDITOR: Enabled pinning.")
        else:
            self.report({"INFO"}, f"NODE EDITOR: Disabled pinning.")

        return {"FINISHED"}


class NODE_OT_hide_unused_group_inputs(Operator):
    bl_idname = "node.hide_unused_sockets"
    bl_label = "Hide Unused Sockets"
    bl_options = {"REGISTER", "UNDO_GROUPED"}

    mode: EnumProperty(
        name="Display Mode",
        items=(
            ("SELECTED", "Selected", "Apply operator to selected nodes"),
            ("ALL", "All", "Apply operator to all nodes"),
        ),
        default="ALL",
        description="Specifies on which nodes this operator gets applied on",
    )

    @classmethod
    @return_false_when(AttributeError)
    def poll(cls, context):
        space = context.space_data

        is_existing = space.edit_tree is not None
        is_node_editor = space.type == "NODE_EDITOR"
        has_group_input = any((node.bl_idname == "NodeGroupInput") for node in space.edit_tree.nodes)

        return all((is_existing, is_node_editor, has_group_input))

    def execute(self, context):
        prefs = fetch_user_preferences()
        tree = context.space_data.edit_tree

        if self.mode == "SELECTED":
            nodes = context.selected_nodes
        else:
            nodes = tree.nodes

        for node in nodes:
            if node.bl_idname != "NodeGroupInput":
                continue

            for output in node.outputs:
                if not output.enabled:
                    continue

                if output.bl_idname != "NodeSocketVirtual":
                    output.hide = True
                else:
                    if prefs.unhide_virtual_sockets:
                        output.hide = False

        return {"FINISHED"}


class NODE_OT_troubleshoot_corners(Operator):
    bl_idname = "node.troubleshoot_corners"
    bl_label = "Troubleshoot Corners"
    bl_options = {"REGISTER", "UNDO_GROUPED"}

    @classmethod
    def poll(cls, context):
        return context.active_node

    def execute(self, context):
        prefs = fetch_user_preferences()
        tree = context.space_data.edit_tree
        active_node = context.active_node
        left, right, bottom, top = utils.get_bounds((active_node,))
        center, middle = utils.get_center(active_node), utils.get_middle(active_node)

        positions = [
            (left, top),
            (left, middle),
            (left, bottom),
            (center, top),
            (center, bottom),
            (right, top),
            (right, middle),
            (right, bottom),
        ]

        for position in positions:
            reroute = tree.nodes.new("NodeReroute")
            reroute.name = "TEST_REROUTE"
            reroute.location = position

        return {"FINISHED"}


class NODE_OT_copy_to_clipboard(Operator):
    bl_idname = "node.copy_to_clipboard"
    bl_label = "Copy Active Node Attribute"
    bl_options = {"REGISTER"}

    attribute: StringProperty(default="bl_idname")

    @classmethod
    def poll(cls, context):
        return context.active_node

    def execute(self, context):
        context.window_manager.clipboard = self.attribute

        self.report({"INFO"}, f"Copied to clipboard: '{self.attribute}'")
        return {"FINISHED"}


class NODE_OT_multiple_asset_mark(Operator):
    bl_idname = "node.multiple_asset_mark"
    bl_label = "Mark as Assets"
    bl_options = {"REGISTER", "UNDO_GROUPED"}

    @classmethod
    @return_false_when(AttributeError)
    def poll(cls, context):
        group_nodes = utils.filter_group_nodes(context.selected_nodes, as_tuple=True)
        return len(group_nodes) > 0

    def execute(self, context):
        group_nodes = utils.filter_group_nodes(context.selected_nodes, as_tuple=True)

        for node in group_nodes:
            node.node_tree.asset_mark()

        self.report({"INFO"}, f"Marked {len(group_nodes)} nodegroups as assets.")
        return {"FINISHED"}


class NODE_OT_multiple_asset_clear(Operator):
    bl_idname = "node.multiple_asset_clear"
    bl_label = "Clear Assets"
    bl_options = {"REGISTER", "UNDO_GROUPED"}

    @classmethod
    @return_false_when(AttributeError)
    def poll(cls, context):
        group_nodes = utils.filter_group_nodes(context.selected_nodes, as_tuple=True)
        return len(group_nodes) > 0

    def execute(self, context):
        group_nodes = utils.filter_group_nodes(context.selected_nodes, as_tuple=True)

        for node in group_nodes:
            node.node_tree.asset_clear()

        self.report({"INFO"}, f"Cleared {len(group_nodes)} nodegroups as assets.")
        return {"FINISHED"}


class NODE_OT_multiple_fake_user_set(Operator):
    bl_idname = "node.multiple_fake_user_set"
    bl_label = "Set Fake Users"
    bl_options = {"REGISTER", "UNDO_GROUPED"}

    @classmethod
    @return_false_when(AttributeError)
    def poll(cls, context):
        group_nodes = utils.filter_group_nodes(context.selected_nodes, as_tuple=True)
        return len(group_nodes) > 0

    def execute(self, context):
        group_nodes = utils.filter_group_nodes(context.selected_nodes, as_tuple=True)

        for node in group_nodes:
            node.node_tree.use_fake_user = True

        refresh_ui(context)

        self.report({"INFO"}, f"Set {len(group_nodes)} nodegroups as fake users.")
        return {"FINISHED"}


class NODE_OT_multiple_fake_user_clear(Operator):
    bl_idname = "node.multiple_fake_user_clear"
    bl_label = "Clear Fake Users"
    bl_options = {"REGISTER", "UNDO_GROUPED"}

    @classmethod
    @return_false_when(AttributeError)
    def poll(cls, context):
        group_nodes = utils.filter_group_nodes(context.selected_nodes, as_tuple=True)
        return len(group_nodes) > 0

    def execute(self, context):
        group_nodes = utils.filter_group_nodes(context.selected_nodes, as_tuple=True)

        for node in group_nodes:
            node.node_tree.use_fake_user = False

        refresh_ui(context)

        self.report({"INFO"}, f"Cleared {len(group_nodes)} nodegroups as fake users.")
        return {"FINISHED"}


class NODE_OT_multiple_make_local(Operator):
    bl_idname = "node.multiple_make_local"
    bl_label = "Make Local"
    bl_options = {"REGISTER", "UNDO_GROUPED"}

    @classmethod
    @return_false_when(AttributeError)
    def poll(cls, context):
        group_nodes = utils.filter_group_nodes(context.selected_nodes)
        asset_groups = tuple(n for n in group_nodes if not n.node_tree.is_editable)
        return len(asset_groups) > 0

    def execute(self, context):
        group_nodes = utils.filter_group_nodes(context.selected_nodes)
        asset_groups = tuple(n for n in group_nodes if not n.node_tree.is_editable)

        for node in asset_groups:
            node.node_tree.make_local()

        refresh_ui(context)

        self.report({"INFO"}, f"Created local copies of {len(asset_groups)} linked nodegroups.")
        return {"FINISHED"}


class NODE_OT_multiple_make_local_all(Operator):
    bl_idname = "node.multiple_make_local_all"
    bl_label = "Make Local (All)"
    bl_options = {"REGISTER", "UNDO_GROUPED"}

    @classmethod
    @return_false_when(AttributeError)
    def poll(cls, context):
        group_nodes = utils.filter_group_nodes(context.selected_nodes)
        asset_groups = tuple(n for n in group_nodes if not n.node_tree.is_editable)
        return len(asset_groups) > 0

    @staticmethod
    def remove_duplicate_groups():
        node_groups = bpy.data.node_groups

        for group in node_groups:
            unduped_name, *_ = re.split("\.\d+$", group.name)

            if unduped_name in node_groups:
                group.user_remap(node_groups[unduped_name])
            else:
                group.name = unduped_name

    def make_local(self, nodes):
        group_nodes = utils.filter_group_nodes(nodes)
        asset_groups = tuple(n for n in group_nodes if not n.node_tree.is_editable)

        for node in asset_groups:
            group = node.node_tree
            group.make_local()
            self.make_local(group.nodes)

    def execute(self, context):
        node_trees = tuple(tree for tree in context.blend_data.node_groups)

        self.make_local(context.space_data.edit_tree.nodes)
        self.remove_duplicate_groups()
        refresh_ui(context)

        self.report({"INFO"}, f"Created local copies of {len(node_trees)} linked nodegroups.")
        return {"FINISHED"}


class NODE_OT_merge_reroutes_to_switch(Operator):
    bl_idname = "node.merge_reroutes_to_switch"
    bl_label = "Reroutes to Switch"
    bl_options = {"REGISTER", "UNDO_GROUPED"}

    @classmethod
    def poll(cls, context):
        return all(n.bl_idname == "NodeReroute" for n in context.selected_nodes) and context.selected_nodes

    @staticmethod
    def zigzag(seq, groups):
        results = [[] for i in range(groups)]
        for i, e in enumerate(seq):
            results[i % groups].append(e)
        return results

    @staticmethod
    def batched(seq, groups):
        results = [[] for i in range(groups)]
        batch_size = ceil(len(seq) / groups)

        for i, group in enumerate(zip_longest(*[iter(seq)] * batch_size)):
            for e in group:
                if e is not None:
                    results[i].append(e)

        return results

    @staticmethod
    def switch_from_reroutes(tree, reroutes, switch_type):
        if switch_type == "MENU":
            switch = tree.nodes.new("GeometryNodeMenuSwitch")
            switch_items = switch.enum_definition.enum_items
        elif switch_type == "INDEX":
            switch = tree.nodes.new("GeometryNodeIndexSwitch")
            switch_items = switch.index_switch_items
        else:
            raise ValueError

        switch_items.clear()
        data_type = reroutes[0].outputs[0].type
        if data_type == "VALUE":
            data_type = "FLOAT"
        switch.data_type = data_type

        if switch_type == "MENU":
            for i, reroute in enumerate(reroutes):
                switch_items.new(str(i))
        elif switch_type == "INDEX":
            for i, reroute in enumerate(reroutes):
                switch_items.new()
        else:
            raise ValueError

        reroute_sockets = (r.outputs[0] for r in reroutes)
        for reroute_socket, switch_socket in zip(reroute_sockets, switch.inputs[1:]):
            tree.links.new(reroute_socket, switch_socket)

        switch.location.x = max(r.location.x for r in reroutes) + 400
        switch.location.y = sum(r.location.y for r in reroutes) / len(reroutes)

        return switch

    def execute(self, context):
        reroutes = tuple(n for n in context.selected_nodes if n.bl_idname == "NodeReroute")
        prefs = utils.fetch_user_preferences()

        func = getattr(self, prefs.reroute_merge_type.lower())

        with utils.TemporaryUnframe(nodes=reroutes):
            reroutes = sorted(reroutes, key=lambda n: -n.location.y)

            reroute_groups = func(reroutes, groups=prefs.switch_count)
            tree = context.space_data.edit_tree

            switches = []
            for group in reroute_groups:
                switches.append(self.switch_from_reroutes(tree, group, switch_type=prefs.switch_type))

        return {"FINISHED"}


class NODE_OT_convert_switch_type(Operator):
    bl_idname = "node.convert_switch_type"
    bl_label = "Convert Switch Type"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return getattr(context.active_node, "bl_idname", None) in {
            "GeometryNodeMenuSwitch",
            "GeometryNodeIndexSwitch",
        }

    def execute(self, context):
        tree = context.space_data.edit_tree
        node = context.active_node

        if node.bl_idname == "GeometryNodeMenuSwitch":
            switch = tree.nodes.new("GeometryNodeIndexSwitch")
            utils.transfer_properties(node, target=switch, props=("parent", "location", "width", "hide", "data_type"))
            switch_items = switch.index_switch_items
            switch_items.clear()

            for item in node.enum_definition.enum_items:
                switch_items.new()

            for node_sock, switch_sock in zip(node.inputs[1:], switch.inputs[1:]):
                for link in node_sock.links:
                    tree.links.new(link.from_socket, switch_sock)

                if hasattr(switch_sock, "default_value"):
                    switch_sock.default_value = node_sock.default_value

            for node_sock, switch_sock in zip(node.outputs, switch.outputs):
                for link in node_sock.links:
                    tree.links.new(switch_sock, link.to_socket)

            tree.nodes.remove(node)
            tree.nodes.active = switch

        elif node.bl_idname == "GeometryNodeIndexSwitch":
            switch = tree.nodes.new("GeometryNodeMenuSwitch")
            utils.transfer_properties(node, target=switch, props=("parent", "location", "width", "hide", "data_type"))
            switch_items = switch.enum_definition.enum_items
            switch_items.clear()

            for i, item in enumerate(node.index_switch_items):
                switch_items.new(str(i))

            for node_sock, switch_sock in zip(node.inputs[1:], switch.inputs[1:]):
                for link in node_sock.links:
                    tree.links.new(link.from_socket, switch_sock)

                if hasattr(switch_sock, "default_value"):
                    switch_sock.default_value = node_sock.default_value

            for node_sock, switch_sock in zip(node.outputs, switch.outputs):
                for link in node_sock.links:
                    tree.links.new(switch_sock, link.to_socket)

            tree.nodes.remove(node)
            tree.nodes.active = switch
        else:
            raise ValueError

        return {"FINISHED"}


class NODE_OT_menu_switch_to_enum(Operator):
    bl_idname = "node.menu_switch_to_enum"
    bl_label = "Menu Switch to Enum"
    bl_options = {"REGISTER", "UNDO"}

    group_name: StringProperty(name="", default="", options={"SKIP_SAVE"})
    is_hidden: BoolProperty(name="Is Hidden", default=True, options={"SKIP_SAVE"})

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        if context.selected_nodes:
            row.label(icon="NODETREE")
            row.activate_init = True
            row.prop(self, "group_name")
            layout.prop(self, "is_hidden")
        else:
            row.label(icon="ERROR")
            row.label(text="No nodes selected")

    @classmethod
    def poll(cls, context):
        return getattr(context.active_node, "bl_idname", None) == "GeometryNodeMenuSwitch"

    @staticmethod
    def transfer_menu_switch_items(source, target):
        source_items = source.enum_definition.enum_items
        target_items = target.enum_definition.enum_items

        target_items.clear()

        for old_item in source_items:
            new_item = target_items.new(old_item.name)
            new_item.description = old_item.description

    @staticmethod
    def convert_to_enum_switch(node):
        node.data_type = "INT"
        for index, socket in enumerate(node.inputs[1:-1]):
            socket.default_value = index

    @staticmethod
    def init_internal_tree(tree):
        group_input = tree.nodes.new("NodeGroupInput")
        group_output = tree.nodes.new("NodeGroupOutput")
        new_switch = tree.nodes.new("GeometryNodeMenuSwitch")

        group_input.location = (-230.0, 44.5)
        new_switch.location = (-70.0, 93.5)
        group_output.location = (90.0, 93.5)

        return group_input, group_output, new_switch

    def generate_group_name(self):
        group_name = f"ENUM_{self.group_name}"
        if self.is_hidden:
            group_name = "." + group_name

        return group_name

    def execute(self, context):
        bpy.ops.node.select_all(action="DESELECT")

        old_switch = context.active_node
        groups = context.blend_data.node_groups
        internal_tree = groups.new(self.generate_group_name(), "GeometryNodeTree")
        group_input, group_output, new_switch = self.init_internal_tree(internal_tree)

        self.transfer_menu_switch_items(old_switch, new_switch)
        
        try:
            new_switch.inputs[0].default_value = old_switch.inputs[0].default_value
        except TypeError:
            new_switch.inputs[0].default_value = old_switch.enum_items[0].name

        self.convert_to_enum_switch(new_switch)

        group_sockets = internal_tree.interface
        group_sockets.new_socket(self.group_name, in_out="INPUT", socket_type="NodeSocketMenu")
        group_sockets.new_socket("Output", in_out="OUTPUT", socket_type="NodeSocketInt")

        internal_tree.links.new(group_input.outputs[0], new_switch.inputs[0])
        internal_tree.links.new(new_switch.outputs[0], group_output.inputs[0])

        tree = context.space_data.edit_tree
        group_node = tree.nodes.new("GeometryNodeGroup")
        group_node.node_tree = internal_tree
        group_node.inputs[0].default_value = new_switch.inputs[0].default_value

        # Create index switch
        index_switch = tree.nodes.new("GeometryNodeIndexSwitch")
        index_switch_items = index_switch.index_switch_items
        index_switch_items.clear()

        for item in old_switch.enum_definition.enum_items:
            index_switch_items.new()

        # Transfer Links and properties
        utils.transfer_properties(old_switch, group_node, props=["parent", "width", "location", "label"])
        utils.transfer_properties(old_switch, index_switch, props=["parent", "location", "data_type"])
        utils.transfer_node_links(tree, old_switch.inputs[0], group_node.inputs[0])
        utils.transfer_node_links(tree, old_switch.outputs[0], index_switch.outputs[0])
        for source, target in zip(old_switch.inputs[1:-1], index_switch.inputs[1:-1]):
            utils.transfer_node_links(tree, source, target)
            if hasattr(source, "default_value") and hasattr(target, "default_value"):
                target.default_value = source.default_value

        index_switch.location.x += group_node.width + 20

        # Center New Nodes on Old Switch
        total_width = index_switch.width + group_node.width + 20
        for node in (index_switch, group_node):
            node.location.x -= total_width / 2 - old_switch.width / 2

        tree.links.new(group_node.outputs[0], index_switch.inputs[0])
        tree.nodes.remove(old_switch)
        tree.nodes.active = group_node

        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, title="Create Enum Group")


class NodeOperatorBaseclass:
    @classmethod
    @return_false_when(AttributeError)
    def poll(cls, context):
        space = context.space_data
        tree_exists = space.node_tree is not None
        is_node_editor = space.type == "NODE_EDITOR"
        return tree_exists and is_node_editor


# TODO - Refactor this operator to run modal (this might avoids ZeroDivisionError due to node.dimensions not being refreshed yet)
class NODE_OT_split_group_input(NodeOperatorBaseclass, Operator):
    """Splits Group Input nodes into individual nodes based on sockets/links"""

    bl_idname = "node.split_group_input"
    bl_label = "Split Group Input"
    bl_options = {"REGISTER", "UNDO_GROUPED"}

    group_input_idname = "NodeGroupInput"

    split_by: EnumProperty(name="Split By", items=(("SOCKETS", "Sockets", ""), ("LINKS", "Links", "")))

    @staticmethod
    def is_group_input(node):
        return node.bl_idname == "NodeGroupInput"

    @staticmethod
    def is_valid_socket(socket):
        return not (socket.hide or isinstance(socket, NodeSocketVirtual))

    @classmethod
    def poll(cls, context):
        if super().poll(context) is False:
            return False

        valid_nodes = tuple(filter(cls.is_group_input, context.selected_nodes))
        has_selection = len(valid_nodes) > 0

        return has_selection

    @staticmethod
    def arrange_nodes(tree, added_links, padding=0.0):
        with utils.TemporaryUnframe(tree.nodes):
            for link in added_links:
                node = link.from_node
                to_socket = link.to_socket

                # Since this is a newly added node, all location/dimension values are (0.0, 0.0)
                # But since the sizes of the nodes in these contexts are identical, they can be precalculated
                node_pos_minus_socket_pos = Vector((-140.0 - padding, 35.0))
                node.location = utils.get_socket_location(to_socket) + node_pos_minus_socket_pos

    def execute(self, context):
        tree = utils.fetch_active_nodetree(context)
        selected_nodes = context.selected_nodes
        group_inputs = filter(self.is_group_input, selected_nodes)

        # TODO - Make this controllable by user preference
        replace_selection = True
        if replace_selection:
            for node in selected_nodes:
                if not self.is_group_input(node) or len(tuple(filter(self.is_valid_socket, node.outputs))) > 1:
                    node.select = False

        for old_node in group_inputs:
            added_nodes = []

            if self.split_by == "SOCKETS":
                if len(tuple(filter(self.is_valid_socket, old_node.outputs))) <= 1:
                    continue

                for index, old_socket in enumerate(old_node.outputs):
                    if not self.is_valid_socket(old_socket):
                        continue

                    new_node = tree.nodes.new(self.group_input_idname)
                    utils.transfer_properties(old_node, target=new_node, props=("parent", "width", "label"))
                    new_node_sockets = filter(self.is_valid_socket, new_node.outputs)

                    for soc in new_node_sockets:
                        soc.hide = True

                    new_socket = new_node.outputs[index]
                    new_socket.hide = False

                    utils.transfer_node_links(tree, old_socket, new_socket)
                    added_nodes.append(new_node)

                if added_nodes:
                    utils.arrange_along_column(added_nodes, spacing=20)
                    utils.align_by_bounding_box(target_nodes=[old_node], nodes_to_move=added_nodes)

                tree.nodes.remove(old_node)

            elif self.split_by == "LINKS":
                added_links = []

                if len(tuple(filter(self.is_valid_socket, old_node.outputs))) <= 0:
                    continue

                for index, old_socket in enumerate(old_node.outputs):
                    if (not self.is_valid_socket(old_socket)) or (not old_socket.links):
                        continue

                    for link in sorted(old_socket.links, key=lambda x: -x.to_node.location.y):
                        new_node = tree.nodes.new(self.group_input_idname)
                        utils.transfer_properties(old_node, target=new_node, props=("width", "label"))
                        new_node_sockets = filter(self.is_valid_socket, new_node.outputs)

                        for soc in new_node_sockets:
                            soc.hide = True

                        to_socket = link.to_socket
                        new_socket = new_node.outputs[index]
                        new_socket.hide = False

                        link = tree.links.new(new_socket, to_socket)
                        new_node.parent = link.to_node.parent
                        added_links.append(link)
                        added_nodes.append(new_node)

                tree.nodes.remove(old_node)

                # TODO - Make this padding controllable by user preference
                self.arrange_nodes(tree, added_links, padding=30)

            else:
                raise ValueError

        return {"FINISHED"}


# TODO - Refactor this operator to run modal (this might avoids ZeroDivisionError due to node.dimensions not being refreshed yet)
class NODE_OT_merge_group_input(NodeOperatorBaseclass, Operator):
    """Merge separate Group Input nodes into one whole node"""

    bl_idname = "node.merge_group_input"
    bl_label = "Merge Group Input"
    bl_options = {"REGISTER", "UNDO_GROUPED"}

    group_input_idname = "NodeGroupInput"

    @staticmethod
    def is_group_input(node):
        return node.bl_idname == "NodeGroupInput"

    @staticmethod
    def is_valid_socket(socket):
        return not (socket.hide or isinstance(socket, NodeSocketVirtual))

    @classmethod
    def poll(cls, context):
        if super().poll(context) is False:
            return False

        valid_nodes = tuple(filter(cls.is_group_input, context.selected_nodes))
        has_selection = len(valid_nodes) > 0

        return has_selection

    def execute(self, context):
        tree = utils.fetch_active_nodetree(context)
        selected_nodes = context.selected_nodes
        group_inputs = tuple(filter(self.is_group_input, selected_nodes))

        active_node = context.active_node
        has_active = active_node in group_inputs

        if len(group_inputs) <= 1:
            return {"CANCELLED"}

        # TODO - Make this controllable by user preference
        replace_selection = True
        if replace_selection:
            for node in selected_nodes:
                if not self.is_group_input(node):
                    node.select = False

        new_node = tree.nodes.new(self.group_input_idname)
        for socket in new_node.outputs:
            if not isinstance(socket, NodeSocketVirtual):
                socket.hide = True

        target = active_node if has_active else group_inputs
        tree.nodes.active = new_node

        for old_node in group_inputs:
            for index, old_socket in filter(lambda x: self.is_valid_socket(x[1]), enumerate(old_node.outputs)):
                new_socket = new_node.outputs[index]
                new_socket.hide = old_socket.hide

                utils.transfer_node_links(tree, old_socket, new_socket)

        with utils.TemporaryUnframe(nodes=group_inputs):
            utils.align_by_bounding_box(target_nodes=target, nodes_to_move=new_node)

        if has_active:
            utils.transfer_properties(active_node, target=new_node, props=("parent", "width", "label", "location"))
        else:
            parents = Counter(node.parent for node in group_inputs)
            parent = parents.most_common(1)[0][0]
            new_node.parent = parent
            new_node.width = sum(n.width for n in group_inputs) / len(group_inputs)

        for old_node in group_inputs:
            tree.nodes.remove(old_node)

        return {"FINISHED"}


class NODE_OT_batch_replace_group(Operator):
    bl_idname = "node.batch_replace_group"
    bl_label = "Batch Replace Group"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        active_node = context.active_node
        wm = context.window_manager
        tree = context.space_data.edit_tree
        group = wm.nodegroup_to_replace

        if group is None:
            return False

        is_valid_group = group.bl_idname == tree.bl_idname and not group.contains_tree(tree)

        return all(
            (
                hasattr(active_node, "node_tree"),
                active_node.select,
                wm.nodegroup_to_replace is not None,
                is_valid_group,
            )
        )

    def execute(self, context):
        wm = context.window_manager
        group_nodes = utils.filter_group_nodes(context.selected_nodes, as_tuple=True)

        for node in group_nodes:
            node.node_tree = wm.nodegroup_to_replace

        return {"FINISHED"}


class NODE_OT_convert_math_node(Operator):
    bl_idname = "node.convert_math_node"
    bl_label = "Convert Math Node"
    bl_options = {"REGISTER", "UNDO"}

    @staticmethod
    def is_convertable(node):
        is_valid_node = getattr(node, "bl_idname", None) in {
            "ShaderNodeMath",
            "FunctionNodeIntegerMath",
        }
        if not is_valid_node:
            return False

        is_valid_operation = node.operation in (
            "ADD",
            "SUBTRACT",
            "MULTIPLY",
            "DIVIDE",
            "MULTIPLY_ADD",
            "ABSOLUTE",
            "POWER",
            "MINIMUM",
            "MAXIMUM",
            "SIGN",
            # TODO - Find a way to convert one int math node to two float math nodes for these operations
            #'DIVIDE_ROUND',
            #'DIVIDE_FLOOR',
            #'DIVIDE_CEIL',
            "FLOORED_MODULO",
            "MODULO",
        )

        return is_valid_operation

    @classmethod
    def poll(cls, context):
        nodes = tuple(filter(cls.is_convertable, context.selected_nodes))

        return len(nodes) > 0

    @staticmethod
    def convert_node(tree, node):
        if node.bl_idname == "ShaderNodeMath":
            switch = tree.nodes.new("FunctionNodeIntegerMath")
            utils.transfer_properties(node, target=switch, props=("parent", "location", "hide", "width", "operation"))

            for old_sock, new_sock in zip(node.inputs, switch.inputs):
                for link in old_sock.links:
                    new_link = tree.links.new(link.from_socket, new_sock)
                    new_link.is_muted = link.is_muted

                if hasattr(new_sock, "default_value"):
                    new_sock.default_value = int(old_sock.default_value)

            # TODO - For some reason .is_muted does not always propagate correctly, invesigate that
            for old_sock, new_sock in zip(node.outputs, switch.outputs):
                for link in old_sock.links:
                    new_link = tree.links.new(new_sock, link.to_socket)
                    new_link.is_muted = link.is_muted

            tree.nodes.remove(node)
            tree.nodes.active = switch

        elif node.bl_idname == "FunctionNodeIntegerMath":
            switch = tree.nodes.new("ShaderNodeMath")
            utils.transfer_properties(node, target=switch, props=("parent", "location", "hide", "width", "operation"))

            for old_sock, new_sock in zip(node.inputs, switch.inputs):
                for link in old_sock.links:
                    new_link = tree.links.new(link.from_socket, new_sock)
                    new_link.is_muted = link.is_muted

                if hasattr(new_sock, "default_value"):
                    new_sock.default_value = old_sock.default_value

            for old_sock, new_sock in zip(node.outputs, switch.outputs):
                for link in old_sock.links:
                    new_link = tree.links.new(new_sock, link.to_socket)
                    new_link.is_muted = link.is_muted

            tree.nodes.remove(node)
            tree.nodes.active = switch
        else:
            raise ValueError

    def execute(self, context):
        tree = context.space_data.edit_tree
        nodes = tuple(filter(self.is_convertable, context.selected_nodes))

        for node in nodes:
            self.convert_node(tree, node)

        return {"FINISHED"}


def refresh_ui(context):
    for region in context.area.regions:
        region.tag_redraw()
    return None


classes = (
    NODE_OT_pin_node_editor,
    NODE_OT_hide_unused_group_inputs,
    # NODE_OT_troubleshoot_corners,
    NODE_OT_copy_to_clipboard,
    NODE_OT_multiple_asset_mark,
    NODE_OT_multiple_asset_clear,
    NODE_OT_multiple_fake_user_set,
    NODE_OT_multiple_fake_user_clear,
    NODE_OT_merge_reroutes_to_switch,
    NODE_OT_convert_switch_type,
    NODE_OT_menu_switch_to_enum,
    NODE_OT_convert_math_node,
    NODE_OT_merge_group_input,
    NODE_OT_split_group_input,
    NODE_OT_multiple_make_local,
    NODE_OT_multiple_make_local_all,
    NODE_OT_batch_replace_group,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
