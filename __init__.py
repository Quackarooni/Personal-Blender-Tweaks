# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name": "Blender Tweaks",
    "author": "Quackers",
    "description": "Just a personal add-on for changing Blender to how I want it to be",
    "blender": (3, 4, 0),
    "version": (0, 0, 1),
    "location": "Node Editor",
    "category": "Personal",
}


from . import prefs, keymaps, operators, ui

modules = (ui, keymaps, operators, prefs)


def register():
    for module in modules:
        module.register()


def unregister():
    for module in modules:
        module.unregister()


if __name__ == "__main__":
    register()
