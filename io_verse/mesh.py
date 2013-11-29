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
This module implements sharing Blender meshes at Verse server
"""


import bpy
import verse as vrs
from .vrsent import vrsent


VERSE_MESH_CT = 126
LAYER_VERTEXES_CT = 0
LAYER_EDGES_CT = 1
LAYER_QUADS_CT = 2


class VerseMesh(vrsent.VerseNode):
    """
    Custom VerseNode subclass representing Blender mesh data structure
    """

    custom_type = VERSE_MESH_CT
    
    def __init__(self, session, node_id=None, parent=None, user_id=None, custom_type=VERSE_MESH_CT):
        super(VerseMesh, self).__init__(session, node_id, parent, user_id, custom_type)
        self.vertexes = None
        self.edges = None
        self.quads = None


# List of Blender classes in this submodule
classes = ()


def init_properties():
    """
    Init properties in blender object data type
    """
    bpy.types.Mesh.verse_node_id = bpy.props.IntProperty( \
        name = "ID of verse mesh node", \
        default = -1, \
        description = ""
    )


def register():
    """
    This method register all methods of this submodule
    """
    for c in classes:
        bpy.utils.register_class(c)
    init_properties()


def unregister():
    """
    This method unregister all methods of this submodule
    """
    for c in classes:
        bpy.utils.unregister_class(c)


if __name__ == '__main__':
    register()