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


class VerseMeshCache(object):
    """
    This class stores last state of edit mesh that was sent to Verse server.
    Instance of this class could be only one in memory, when MESH object is in edit mode.
    """

    def __init__(self, verse_mesh):
        """
        Constructor of VerseMeshCache
        """
        self.verse_mesh = verse_mesh
        self.verse_mesh.bmesh = bmesh.from_edit_mesh(self.verse_mesh.mesh)
        # Create dictionary of vertices
        self.vertices = {vert.index: tuple(vert.co)
                         for vert in self.verse_mesh.bmesh.verts}
        # Create dictionary of edges
        self.edges = {edge.index: (edge.verts[0].index, edge.verts[1].index)
                      for edge in self.verse_mesh.bmesh.edges}
        # Create dictionary of faces
        self.faces = {face.index: tuple(vert.index for vert in face.verts)
                      for face in self.verse_mesh.bmesh.faces}

    def __send_vertex_updates(self):
        """
        Try to send updates of geometry (positions of vertices)
        """

        # Go through bmesh and try to detect new positions of vertices
        # and newly created vertexes
        for b3d_vert in self.verse_mesh.bmesh.verts:
            verse_ID = self.verse_mesh.get_verse_id_of_vertex(b3d_vert)
            if verse_ID is None:
                # TODO: new vertex was created. Send it to Verse server, store in cache and save verse ID
                pass
            else:
                cache_vert_co = self.vertices[verse_ID]
                if cache_vert_co != tuple(b3d_vert.co):
                    self.verse_mesh.vertices.items[verse_ID] = \
                        self.vertices[verse_ID] = \
                        tuple(b3d_vert.co)

        # When length of vertices and cached vertices differs now, then
        # it means that some vertex was deleted in bmesh. Find cached
        # vertex/vertices and destroy them at Verse server too
        if len(self.verse_mesh.bmesh.verts) != len(self.vertices):
            # TODO: at least one vertex was deleted. Find it and send layer_unset command
            pass
            # for vert_id, vert_co in self.vertices.items():

    def send_updates(self):
        """
        Try to send update of edit mesh to Verse server
        """
        # Check if bmesh is still fresh
        try:
            self.verse_mesh.bmesh.verts
        except ReferenceError:
            self.verse_mesh.bmesh = bmesh.from_edit_mesh(self.verse_mesh.mesh)
        self.__send_vertex_updates()
        # TODO: send edge and face updates too


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
        self.cache = None

        if self.mesh is not None:
            self.mesh.update(calc_tessface=True)
            self.bmesh.from_mesh(self.mesh)
            # TODO: do not do it in this way for huge mesh (do not send whole mesh), but use
            # vrs.get to get free space in outgoing queue.

            # Send all Vertices
            for vert in mesh.vertices:
                self.vertices.items[vert.index] = tuple(vert.co)
            # Send all Edges
            for edge in mesh.edges:
                self.edges.items[edge.index] = (edge.vertices[0], edge.vertices[1])
            # Send all Faces
            for face in mesh.tessfaces:
                if len(face.vertices) == 3:
                    self.quads.items[face.index] = (face.vertices[0], face.vertices[1], face.vertices[2], 0)
                else:
                    self.quads.items[face.index] = tuple(vert for vert in face.vertices)

            # Create blender layers storing Verse IDs of vertices, edges and faces
            self.__create_bpy_layer_ids('verts', 'VertIDs')
            self.__create_bpy_layer_ids('edges', 'EdgeIDs')
            self.__create_bpy_layer_ids('faces', 'FaceIDs')
            # Safe blender layers with to original mesh
            self.bmesh.to_mesh(self.mesh)

    def __create_bpy_layer_ids(self, elems_name, layer_name):
        """
        This method create Blender layer storing IDs of vertices or edges or faces
        :elems_name: this could be 'verts', 'edges' or 'faces'
        """
        lay = self.bmesh.loops.layers.int.new(layer_name)
        # Set values in layer
        elems_iter = getattr(self.bmesh, elems_name)
        for elem in elems_iter:
            if elems_name == 'faces':
                for loop in elem.loops:
                    # Value 0 is always default value
                    loop[lay] = elem.index + 1
            else:
                for loop in elem.link_loops:
                    # Value 0 is always default value
                    loop[lay] = elem.index + 1

    def get_verse_id_of_vertex(self, bpy_vert):
        """
        Return ID of blender vertex at Verse server
        """
        layer = self.bmesh.loops.layers.int.get('VertIDs')
        for loop in bpy_vert.link_loops:
            if loop[layer] != 0:
                return loop[layer] - 1
        return None

    def get_verse_id_of_edge(self, bpy_edge):
        """
        Return ID of blender edge at Verse server
        """
        layer = self.bmesh.loops.layers.int.get('EdgeIDs')
        for loop in bpy_edge.link_loops:
            if loop[layer] != 0:
                return loop[layer] - 1
        return None

    def get_verse_id_of_face(self, bpy_face):
        """
        Return ID of blender face at Verse server
        """
        layer = self.bmesh.loops.layers.int.get('FaceIDs')
        for loop in bpy_face.link_loops:
            if loop[layer] != 0:
                return loop[layer] - 1
        return None

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
