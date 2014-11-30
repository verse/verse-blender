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
        self.bmesh = None
        self.cache = None
        self.last_vert_ID = None
        self.last_edge_ID = None
        self.last_face_ID = None

        if self.mesh is not None:
            # TODO: make following code working in edit mode too
            self.mesh.update(calc_tessface=True)
            self.bmesh = bmesh.new()
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
            self.last_vert_ID = self.__create_bpy_layer_ids('verts', 'VertIDs')
            self.last_edge_ID = self.__create_bpy_layer_ids('edges', 'EdgeIDs')
            self.last_face_ID = self.__create_bpy_layer_ids('faces', 'FaceIDs')

            # Safe blender layers containing IDs to original mesh
            self.bmesh.to_mesh(self.mesh)
            self.bmesh.free()

    def __create_bpy_layer_ids(self, elems_name, layer_name):
        """
        This method create Blender layer storing IDs of vertices or edges or faces
        :elems_name: this could be 'verts', 'edges' or 'faces'
        """
        elems_iter = getattr(self.bmesh, elems_name)
        lay = elems_iter.layers.int.new(layer_name)
        # Set values in layer
        last_elem_id = None
        for elem in elems_iter:
            last_elem_id = elem.index
            elem[lay] = elem.index + 1

        return last_elem_id

    def get_verse_id_of_vertex(self, bpy_vert):
        """
        Return ID of blender vertex at Verse server
        """
        layer = self.bmesh.verts.layers.int.get('VertIDs')
        # Fast hack (probably not reliable), because Blender duplicates values in layers :-(
        verse_id = bpy_vert[layer] - 1
        if verse_id < bpy_vert.index:
            return -1
        else:
            return verse_id

    def get_verse_id_of_edge(self, bpy_edge):
        """
        Return ID of blender edge at Verse server
        """
        layer = self.bmesh.edges.layers.int.get('EdgeIDs')
        # Fast hack
        verse_id = bpy_edge[layer] - 1
        if verse_id < bpy_edge.index:
            return -1
        else:
            return verse_id

    def get_verse_id_of_face(self, bpy_face):
        """
        Return ID of blender face at Verse server
        """
        layer = self.bmesh.faces.layers.int.get('FaceIDs')
        # Fast hack
        verse_id = bpy_face[layer] - 1
        if verse_id < bpy_face.index:
            return -1
        else:
            return verse_id

    def __send_vertex_updates(self):
        """
        Try to send updates of geometry and positions of vertices
        """

        alive_verts = {}

        # Go through bmesh and try to detect new positions of vertices,
        # deleted vertices and newly created vertices
        for b3d_vert in self.bmesh.verts:
            verse_id = self.get_verse_id_of_vertex(b3d_vert)
            # New vertex was created. Try to send it to Verse server, store it in cache and save verse ID
            if verse_id == -1:
                # Update the last vertex ID
                self.last_vert_ID += 1
                verse_id = self.last_vert_ID
                # Send new vertex position to Verse server
                self.vertices.items[verse_id] = tuple(b3d_vert.co)
                # Store verse vertex ID in bmesh layer
                layer = self.bmesh.verts.layers.int.get('VertIDs')
                b3d_vert[layer] = verse_id + 1
            # Position of vertex was changed?
            elif self.vertices.items[verse_id] != tuple(b3d_vert.co):
                # This will send updated position of vertex
                self.vertices.items[verse_id] = tuple(b3d_vert.co)

            # Mark vertex as alive
            alive_verts[verse_id] = True

        # When length of vertices and cached vertices differs now, then
        # it means that some vertex was deleted in bmesh. Find cached
        # vertex/vertices and destroy them at Verse server too
        if len(self.bmesh.verts) != len(self.vertices.items):
            for vert_id in self.vertices.items.keys():
                if vert_id not in alive_verts.keys():
                    # This will send unset command
                    self.vertices.items.pop(vert_id)

    def __send_edge_updates(self):
        """
        Try to send updates of topology (edges)
        """

        alive_edges = {}

        # Go through bmesh and try to detect changes in edges (new created edges or deleted edges)
        for b3d_edge in self.bmesh.edges:
            verse_id = self.get_verse_id_of_edge(b3d_edge)
            # New edge was created. Try to send it to Verse server
            if verse_id == -1:
                self.last_edge_ID += 1
                verse_id = self.last_edge_ID
                # Send new edge to Verse server
                self.edges.items[verse_id] = (
                    self.get_verse_id_of_vertex(b3d_edge.verts[0]),
                    self.get_verse_id_of_vertex(b3d_edge.verts[1])
                )
                # Store edge ID in bmesh layer
                layer = self.bmesh.edges.layers.int.get('EdgeIDs')
                b3d_edge[layer] = verse_id + 1

            alive_edges[verse_id] = True

        if len(self.bmesh.edges) != len(self.edges.items):
            for edge_id in self.edges.items.keys():
                if edge_id not in alive_edges.keys():
                    # This will send unset command
                    self.edges.items.pop(edge_id)

    def __send_face_updates(self):
        """
        Try to send updates of topology (faces)
        """

        alive_faces = {}

        # Go through bmesh faces and try to detect changes (newly created or destroyed faces)
        for b3d_face in self.bmesh.faces:
            verse_id = self.get_verse_id_of_face(b3d_face)
            # New face was created. Try to send it to Verse server
            if verse_id == -1:
                self.last_edge_ID += 1
                verse_id = self.last_edge_ID
                # Send new face to Verse server
                if len(b3d_face.verts) == 3:
                    self.quads.items[verse_id] = (
                        self.get_verse_id_of_vertex(b3d_face.verts[0]),
                        self.get_verse_id_of_vertex(b3d_face.verts[1]),
                        self.get_verse_id_of_vertex(b3d_face.verts[2]),
                        0
                    )
                elif len(b3d_face.verts) == 4:
                    self.quads.items[verse_id] = tuple(self.get_verse_id_of_vertex(vert) for vert in b3d_face.verts)
                else:
                    # TODO: tesselate face
                    print('Error: Face with more than 4 vertices not supported')
                # Store edge ID in bmesh layer
                layer = self.bmesh.faces.layers.int.get('FaceIDs')
                b3d_face[layer] = verse_id + 1

            alive_faces[verse_id] = True

        if len(self.bmesh.faces) != len(self.quads.items):
            for face_id in self.quads.items.keys():
                if face_id not in alive_faces.keys():
                    # This will send unset command
                    self.edges.items.pop(face_id)

    def send_updates(self):
        """
        Try to send update of edit mesh to Verse server
        """
        # Check if bmesh is still fresh
        try:
            self.bmesh.verts
        except ReferenceError:
            self.bmesh = bmesh.from_edit_mesh(self.mesh)
        self.__send_vertex_updates()
        self.__send_edge_updates()
        self.__send_face_updates()

    @classmethod
    def cb_receive_node_create(cls, session, node_id, parent_id, user_id, custom_type):
        """
        When new mesh node is created or verse server, then this callback method is called.
        """
        # Call parent class
        mesh_node = super(VerseMesh, cls).cb_receive_node_create(
            session=session,
            node_id=node_id,
            parent_id=parent_id,
            user_id=user_id,
            custom_type=custom_type
        )

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
