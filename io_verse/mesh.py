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
import mathutils
import bmesh
import verse as vrs
from .vrsent import vrsent
from . import object3d


VERSE_MESH_CT = 126
LAYER_VERTEXES_CT = 0
LAYER_EDGES_CT = 1
LAYER_QUADS_CT = 2


class VerseVertices(vrsent.VerseLayer):
    """
    Custom VerseLayer subclass representing position of vertexes
    """

    node_custom_type = VERSE_MESH_CT
    custom_type = LAYER_VERTEXES_CT

    def __init__(self, node, parent_layer=None, layer_id=None, data_type=vrs.VALUE_TYPE_REAL64,
                 count=3, custom_type=LAYER_VERTEXES_CT):
        """
        Constructor of VerseVertices
        """
        super(VerseVertices, self).__init__(node, parent_layer, layer_id, data_type, count, custom_type)

    @classmethod
    def cb_receive_layer_set_value(cls, session, node_id, layer_id, item_id, value):
        """
        This method is called, when new value of verse layer was set
        """
        layer = super(VerseVertices, cls).cb_receive_layer_set_value(session, node_id, layer_id, item_id, value)

        # Update mesh only in situation, when it was changed by someone else
        if layer.node.locked_by_me is False:
            _bmesh = layer.node.bmesh
            # When this is known vertex ID, then update position. Otherwise create new vertex.
            if item_id < len(_bmesh.verts):
                _bmesh.verts[item_id].co = mathutils.Vector(value)
            else:
                _bmesh.verts.new(value)
            _bmesh.to_mesh(layer.node.mesh)
            layer.node.mesh.update()

        return layer

    @classmethod
    def cb_receive_layer_unset_value(cls, session, node_id, layer_id, item_id):
        """
        This method is called, when some vertex was deleted
        """
        layer = super(VerseVertices, cls).cb_receive_layer_unset_value(session, node_id, layer_id, item_id)

        # TODO: delete vertex

        return layer


class VerseEdges(vrsent.VerseLayer):
    """
    Custom VerseLayer subclass representing edges (indexes to vertexes)
    """

    node_custom_type = VERSE_MESH_CT
    custom_type = LAYER_EDGES_CT

    def __init__(self, node, parent_layer=None, layer_id=None, data_type=vrs.VALUE_TYPE_UINT32,
                 count=2, custom_type=LAYER_EDGES_CT):
        """
        Constructor of VerseEdges
        """
        super(VerseEdges, self).__init__(node, parent_layer, layer_id, data_type, count, custom_type)

    @classmethod
    def cb_receive_layer_set_value(cls, session, node_id, layer_id, item_id, value):
        """
        This method is called, when new value of verse layer was set
        """
        layer = super(VerseEdges, cls).cb_receive_layer_set_value(session, node_id, layer_id, item_id, value)
        # TODO: not sure, what to do here. Probably only check, if new face could be created from
        # fragments of tessellated polygon
        return layer

    @classmethod
    def cb_receive_layer_unset_value(cls, session, node_id, layer_id, item_id):
        """
        This method is called, when some vertex was deleted
        """
        layer = super(VerseEdges, cls).cb_receive_layer_unset_value(session, node_id, layer_id, item_id)

        # TODO: delete edge

        return layer


class VerseFaces(vrsent.VerseLayer):
    """
    Custom VerseLayer subclass representing tessellated faces (indexes to vertexes).
    Tessellated mesh contains only triangles and quads.
    """

    node_custom_type = VERSE_MESH_CT
    custom_type = LAYER_QUADS_CT

    def __init__(self, node, parent_layer=None, layer_id=None, data_type=vrs.VALUE_TYPE_UINT32,
                 count=4, custom_type=LAYER_QUADS_CT):
        """
        Constructor of VerseFaces
        """
        super(VerseFaces, self).__init__(node, parent_layer, layer_id, data_type, count, custom_type)

    @classmethod
    def cb_receive_layer_set_value(cls, session, node_id, layer_id, item_id, value):
        """
        This method is called, when new value of verse layer was set
        """
        layer = super(VerseFaces, cls).cb_receive_layer_set_value(session, node_id, layer_id, item_id, value)

        # Update mesh only in situation, when it was changed by someone else
        if layer.node.locked_by_me is False:
            _bmesh = layer.node.bmesh
            if item_id < len(_bmesh.faces):
                pass
            else:
                try:
                    if value[3] == 0:
                        _bmesh.faces.new([_bmesh.verts[vert_id] for vert_id in value[0:3]])
                    else:
                        _bmesh.faces.new([_bmesh.verts[vert_id] for vert_id in value])
                except IndexError:
                    print('Wrong index of vertex')
            _bmesh.to_mesh(layer.node.mesh)
            layer.node.mesh.update()

        return layer

    @classmethod
    def cb_receive_layer_unset_value(cls, session, node_id, layer_id, item_id):
        """
        This method is called, when some vertex was deleted
        """
        layer = super(VerseFaces, cls).cb_receive_layer_unset_value(session, node_id, layer_id, item_id)

        # TODO: delete vertex

        return layer


class VerseMesh(vrsent.VerseNode):
    """
    Custom VerseNode subclass representing Blender mesh data structure
    """

    custom_type = VERSE_MESH_CT
    
    def __init__(self, session, node_id=None, parent=None, user_id=None, custom_type=VERSE_MESH_CT,
                 mesh=None, autosubscribe=False):
        """
        Constructor of VerseMesh
        """
        super(VerseMesh, self).__init__(session, node_id, parent, user_id, custom_type)

        self.mesh = mesh
        self.vertices = VerseVertices(node=self)
        self.edges = VerseEdges(node=self)
        self.quads = VerseFaces(node=self)
        self._autosubscribe = autosubscribe
        self.bmesh = bmesh.new()

        if self.mesh is not None:
            self.mesh.update(calc_tessface=True)
            self.bmesh.from_mesh(self.mesh)
            # TODO: do not do it in this way for huge mesh
            # Vertices
            for vert in mesh.vertices:
                self.vertices.items[vert.index] = tuple(vert.co)
            # Edges
            for edge in mesh.edges:
                self.edges.items[edge.index] = (edge.vertices[0], edge.vertices[1])
            # Faces
            for face in mesh.tessfaces:
                if len(face.vertices) == 3:
                    self.quads.items[face.index] = (face.vertices[0], face.vertices[1], face.vertices[2], 0)
                else:
                    self.quads.items[face.index] = tuple(vert for vert in face.vertices)

    @classmethod
    def cb_receive_node_create(cls, session, node_id, parent_id, user_id, custom_type):
        """
        When new mesh node is created or verse server, then this callback method is called.
        """
        # Call parent class
        mesh_node = super(VerseMesh, cls).cb_receive_node_create(session=session,
            node_id=node_id,
            parent_id=parent_id,
            user_id=user_id,
            custom_type=custom_type)

        # When this mesh was created at different Blender, then mesh_node does
        # not have valid reference at blender mesh data block
        if mesh_node.mesh is None:
            object_node = object3d.VerseObject.objects[parent_id]
            mesh_node.mesh = object_node.obj.data
            mesh_node.bmesh.from_mesh(mesh_node.mesh)

        mesh_node.mesh.verse_node_id = node_id
        return mesh_node


# List of Blender classes in this submodule
classes = ()


def init_properties():
    """
    Init properties in blender object data type
    """
    bpy.types.Mesh.verse_node_id = bpy.props.IntProperty(
        name="ID of verse mesh node",
        default=-1,
        description="ID of node representing mesh at Verse server"
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
