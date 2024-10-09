from .keymap_ui import KeymapItemDef, KeymapStructure, KeymapLayout
from .operators import (
    NODE_OT_pin_node_editor,
    NODE_OT_hide_unused_group_inputs,
    NODE_OT_troubleshoot_corners,
)


keymap_info = {
    "keymap_name": "Node Editor",
    "space_type": "NODE_EDITOR",
}


keymap_structure = KeymapStructure(
    [
        KeymapItemDef(NODE_OT_pin_node_editor.bl_idname, **keymap_info),
        KeymapItemDef(NODE_OT_hide_unused_group_inputs.bl_idname, **keymap_info),
        # KeymapItemDef(NODE_OT_troubleshoot_corners.bl_idname, **keymap_info),
    ]
)


keymap_layout = KeymapLayout(layout_structure=keymap_structure)


def register():
    keymap_structure.register()


def unregister():
    keymap_structure.unregister()
