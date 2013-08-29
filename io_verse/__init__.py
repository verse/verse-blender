# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

"""
Blender Add-on with Verse integration
"""

bl_info = {
    "name": "Verse Client",
    "author": "Jiri Hnidek",
    "version": (0, 1),
    "blender": (2, 6, 5),
    "location": "File > Verse",
    "description": "Adds integration of Verse protocol",
    "warning": "Alpha quality, Works only at Linux OS, Requires verse module",
    "wiki_url": "",
    "tracker_url": "",
    "category": "System"}


if "bpy" in locals():
    import imp
    imp.reload(vrs)
    imp.reload(session)
    imp.reload(connection)
    imp.reload(scene)
    imp.reload(avatar_view)
else:
    import bpy
    import verse as vrs
    from . import session
    from . import connection
    from . import scene
    from . import avatar_view


def register():
    """
    Call register methods in submodules 
    """
    session.register()
    connection.register()
    scene.register()
    avatar_view.register()


def unregister():
    """
    Call unregister methods in submodules
    """
    session.unregister()
    connection.unregister()
    scene.unregister()
    avatar_view.unregister()


# Print all debug messages
vrs.set_debug_level(vrs.PRINT_DEBUG_MSG)
vrs.set_client_info("Blender", bpy.app.version_string)

if __name__ == "__main__":
    register()
