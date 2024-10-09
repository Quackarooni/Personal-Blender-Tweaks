import bpy
from bpy.props import BoolProperty, EnumProperty, IntProperty

from .keymaps import keymap_layout


class PBTweaksPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    unhide_virtual_sockets: BoolProperty(
        name="Unhide Virtual Sockets",
        default=True,
        description="When hiding unused group sockets, unhide any hidden virtual socket",
    )

    show_invisible_links: BoolProperty(
        name="",
        default=False,
        description="Show Invisible Links",
    )

    show_hidden_data_blocks: BoolProperty(
        name="",
        default=False,
        description="Show Hidden Data-Blocks",
    )

    show_group_data_block_defaults: BoolProperty(
        name="",
        default=False,
        description="Show Group Data-Block Defaults",
    )

    switch_count: IntProperty(
        name="No. of Switches",
        default=1,
        min=0,
        soft_max=50,
        max=100,
        description="Specifies how many Switch nodes will the selected reroutes be merged to",
    )

    switch_type: EnumProperty(
        name="Switch Type",
        items=(
            ("MENU", "Menu Switch", "Use the 'Menu Switch' node"),
            ("INDEX", "Index Switch", "Use the 'Index Switch' node"),
        ),
        default="MENU",
        description="Specifies which Switch node type selected reroutes will be merged to",
    )

    reroute_merge_type: EnumProperty(
        name="Merge Type",
        items=(
            (
                "ZIGZAG",
                "Zigzag",
                "Interweave subsequent reroutes to different switches",
            ),
            ("BATCHED", "Batched", "Clump subsequent reroutes to different switches"),
        ),
        default="BATCHED",
        description="How the reroutes are going to be linked to their respective switch nodes",
    )

    def draw_enum_property(self, layout, prop_name):
        prop_label = self.__annotations__[prop_name].keywords["name"]
        layout.label(text=f"{prop_label}:")
        layout.prop(self, prop_name, text="")

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "unhide_virtual_sockets")

        keymap_layout.draw_keyboard_shorcuts(self, layout, context)


keymap_layout.register_properties(preferences=PBTweaksPreferences)


def register():
    bpy.utils.register_class(PBTweaksPreferences)


def unregister():
    bpy.utils.unregister_class(PBTweaksPreferences)
