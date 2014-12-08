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
import blf
import bgl
import mathutils
import bmesh
from bpy_extras.view3d_utils import location_3d_to_region_2d
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
        self.id_cache = {}

    def b3d_vertex(self, item_id):
        """
        This method tries to find Blender vertex in bmesh and cache
        """
        _bmesh = self.node.bmesh
        try:
            # Try to find blender vertex at cache first
            b3d_vert = self.id_cache[item_id]
        except KeyError:
            try:
                # Then try to find it in bmesh at the index==item_id
                b3d_vert = _bmesh.verts[item_id]
            except IndexError:
                # When vertex was not found in cache nor bmesh, then try to
                # find it using loop over all vertices
                id_layer = _bmesh.verts.layers.int.get('VertIDs')
                for b3d_vert in _bmesh.verts:
                    verse_id = b3d_vert[id_layer]
                    self.id_cache[item_id] = b3d_vert
                    if verse_id == item_id:
                        return b3d_vert
                return None
            else:
                # Update cache
                self.id_cache[item_id] = b3d_vert
                return b3d_vert
        else:
            return b3d_vert

    @classmethod
    def cb_receive_layer_set_value(cls, session, node_id, layer_id, item_id, value):
        """
        This method is called, when new value of verse layer was set
        """
        vert_layer = super(VerseVertices, cls).cb_receive_layer_set_value(session, node_id, layer_id, item_id, value)

        # Update mesh only in situation, when it was changed by someone else
        if vert_layer.node.locked_by_me is False:

            edge_layer = vert_layer.node.edges
            face_layer = vert_layer.node.quads

            if vert_layer.node.bmesh is None:
                vert_layer.node.bmesh = bmesh.new()
                vert_layer.node.bmesh.from_mesh(vert_layer.node.mesh)
                vert_layer.node.bm_from_edit_mesh = False
            else:
                try:
                    vert_layer.node.bmesh.verts
                except ReferenceError:
                    vert_layer.node.bmesh = bmesh.new()
                    vert_layer.node.bmesh = vert_layer.node.bmesh.from_mesh(vert_layer.node.mesh)
                    vert_layer.id_cache = {}
                    edge_layer.id_cache = {}
                    face_layer.id_cache = {}

            _bmesh = vert_layer.node.bmesh

            b3d_vert = vert_layer.b3d_vertex(item_id)

            # Try to update last vertex ID
            if vert_layer.node.last_vert_ID is None or \
                    vert_layer.node.last_vert_ID < item_id:
                vert_layer.node.last_vert_ID = item_id

            if b3d_vert is not None:
                # Update position
                b3d_vert.co = mathutils.Vector(value)
            else:
                # When vertex was not found, then it is new vertex. Create it.
                _bmesh.verts.new(value)
                b3d_vert = vert_layer.id_cache[item_id] = _bmesh.verts[-1]
                id_layer = _bmesh.verts.layers.int.get('VertIDs')
                b3d_vert[id_layer] = item_id

            # Update Blender mesh
            _bmesh.to_mesh(vert_layer.node.mesh)
            vert_layer.node.mesh.update()

        return vert_layer

    @classmethod
    def cb_receive_layer_unset_value(cls, session, node_id, layer_id, item_id):
        """
        This method is called, when some vertex was deleted
        """
        vert_layer = super(VerseVertices, cls).cb_receive_layer_unset_value(session, node_id, layer_id, item_id)

        # Update mesh only in situation, when it was changed by someone else
        if vert_layer.node.locked_by_me is False:

            edge_layer = vert_layer.node.edges
            face_layer = vert_layer.node.quads

            if vert_layer.node.bmesh is None:
                vert_layer.node.bmesh = bmesh.new()
                vert_layer.node.bmesh.from_mesh(vert_layer.node.mesh)
                vert_layer.node.bm_from_edit_mesh = False
            else:
                try:
                    vert_layer.node.bmesh.verts
                except ReferenceError:
                    vert_layer.node.bmesh = bmesh.new()
                    vert_layer.node.bmesh = vert_layer.node.bmesh.from_mesh(vert_layer.node.mesh)
                    vert_layer.id_cache = {}
                    edge_layer.id_cache = {}
                    face_layer.id_cache = {}

            # Try to delete vertex
            _bmesh = vert_layer.node.bmesh

            # Try to delete vertex
            b3d_vert = vert_layer.b3d_vertex(item_id)
            if b3d_vert is not None:
                bmesh.ops.delete(_bmesh, geom=[b3d_vert], context=1)

            # Update Blender mesh
            _bmesh.to_mesh(vert_layer.node.mesh)
            vert_layer.node.mesh.update()

        return vert_layer


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
        self.id_cache = {}

    def b3d_edge(self, item_id):
        """
        This method tries to find Blender edge in bmesh and cache
        """
        _bmesh = self.node.bmesh
        try:
            # Try to find blender vertex at cache first
            b3d_edge = self.id_cache[item_id]
        except KeyError:
            try:
                # Then try to find it in bmesh at the index==item_id
                b3d_edge = _bmesh.edges[item_id]
            except IndexError:
                # When edge was not found in cache nor bmesh, then try to
                # find it using loop over all edges
                id_layer = _bmesh.edges.layers.int.get('EdgeIDs')
                for b3d_edge in _bmesh.edges:
                    verse_id = b3d_edge[id_layer]
                    self.id_cache[item_id] = b3d_edge
                    if verse_id == item_id:
                        return b3d_edge
                return None
            else:
                # Update cache
                self.id_cache[item_id] = b3d_edge
                return b3d_edge
        else:
            return b3d_edge

    @classmethod
    def cb_receive_layer_set_value(cls, session, node_id, layer_id, item_id, value):
        """
        This method is called, when new value of verse layer was set
        """
        edge_layer = super(VerseEdges, cls).cb_receive_layer_set_value(session, node_id, layer_id, item_id, value)

        # Update mesh only in situation, when it was changed by someone else
        if edge_layer.node.locked_by_me is False:

            vert_layer = edge_layer.node.vertices
            face_layer = edge_layer.node.quads

            if edge_layer.node.bmesh is None:
                edge_layer.node.bmesh = bmesh.new()
                edge_layer.node.bmesh.from_mesh(edge_layer.node.mesh)
                edge_layer.node.bm_from_edit_mesh = False
            else:
                try:
                    edge_layer.node.bmesh.edges
                except ReferenceError:
                    edge_layer.node.bmesh = bmesh.new()
                    edge_layer.node.bmesh = edge_layer.node.bmesh.from_mesh(edge_layer.node.mesh)
                    vert_layer.id_cache = {}
                    edge_layer.id_cache = {}
                    face_layer.id_cache = {}

            _bmesh = edge_layer.node.bmesh

            b3d_edge = edge_layer.b3d_edge(item_id)

            # Try to update last vertex ID
            if edge_layer.node.last_edge_ID is None or \
                    edge_layer.node.last_edge_ID < item_id:
                edge_layer.node.last_edge_ID = item_id

            if b3d_edge is not None:
                # Delete edge
                _bmesh.edges.remove(b3d_edge)

            # When vertex was not found, then it is new vertex. Create it.
            _bmesh.edges.new([vert_layer.b3d_vertex(vert_id) for vert_id in value])
            b3d_edge = edge_layer.id_cache[item_id] = _bmesh.edges[-1]
            id_layer = _bmesh.edges.layers.int.get('EdgeIDs')
            b3d_edge[id_layer] = item_id

            # Update Blender mesh
            _bmesh.to_mesh(edge_layer.node.mesh)
            edge_layer.node.mesh.update()

        return edge_layer

    @classmethod
    def cb_receive_layer_unset_value(cls, session, node_id, layer_id, item_id):
        """
        This method is called, when some vertex was deleted
        """
        edge_layer = super(VerseEdges, cls).cb_receive_layer_unset_value(session, node_id, layer_id, item_id)

        # Update mesh only in situation, when it was changed by someone else
        if edge_layer.node.locked_by_me is False:

            vert_layer = edge_layer.node.vertices
            face_layer = edge_layer.node.quads

            if edge_layer.node.bmesh is None:
                edge_layer.node.bmesh = bmesh.new()
                edge_layer.node.bmesh.from_mesh(edge_layer.node.mesh)
                edge_layer.node.bm_from_edit_mesh = False
            else:
                try:
                    edge_layer.node.bmesh.edges
                except ReferenceError:
                    edge_layer.node.bmesh = bmesh.new()
                    edge_layer.node.bmesh = edge_layer.node.bmesh.from_mesh(edge_layer.node.mesh)
                    vert_layer.id_cache = {}
                    edge_layer.id_cache = {}
                    face_layer.id_cache = {}

            _bmesh = edge_layer.node.bmesh

            b3d_edge = edge_layer.b3d_edge(item_id)

            # Try to update last vertex ID
            if edge_layer.node.last_vert_ID is None or \
                    edge_layer.node.last_edge_ID < item_id:
                edge_layer.node.last_edge_ID = item_id

            if b3d_edge is not None:
                # Delete edge
                _bmesh.edges.remove(b3d_edge)
                # Update Blender mesh
                _bmesh.to_mesh(edge_layer.node.mesh)
                edge_layer.node.mesh.update()

        return edge_layer


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
        self.id_cache = {}

    def find_b3d_face(self, item_id):
        """
        This method tries to find Blender vertex in bmesh and cache
        """
        _bmesh = self.node.bmesh
        try:
            # Try to find blender face at cache first
            b3d_face = self.id_cache[item_id]
        except KeyError:
            try:
                # Then try to find it in bmesh at the index==item_id
                b3d_face = _bmesh.faces[item_id]
            except IndexError:
                # When face was not found in cache nor bmesh, then try to
                # find it using loop over all faces
                id_layer = _bmesh.faces.layers.int.get('FaceIDs')
                for b3d_face in _bmesh.faces:
                    verse_id = b3d_face[id_layer]
                    self.id_cache[item_id] = b3d_face
                    if verse_id == item_id:
                        return b3d_face
                return None
            else:
                # Update cache
                self.id_cache[item_id] = b3d_face
                return b3d_face
        else:
            return b3d_face

    @classmethod
    def cb_receive_layer_set_value(cls, session, node_id, layer_id, item_id, value):
        """
        This method is called, when new value of verse layer was set
        """
        face_layer = super(VerseFaces, cls).cb_receive_layer_set_value(session, node_id, layer_id, item_id, value)

        # Update mesh only in situation, when it was changed by someone else
        if face_layer.node.locked_by_me is False:

            vert_layer = face_layer.node.vertices
            edge_layer = face_layer.node.edges

            if face_layer.node.bmesh is None:
                face_layer.node.bmesh = bmesh.new()
                face_layer.node.bmesh.from_mesh(face_layer.node.mesh)
                face_layer.node.bm_from_edit_mesh = False
            else:
                try:
                    face_layer.node.bmesh.faces
                except ReferenceError:
                    face_layer.node.bmesh = bmesh.new()
                    face_layer.node.bmesh = face_layer.node.bmesh.from_mesh(face_layer.node.mesh)
                    vert_layer.id_cache = {}
                    edge_layer.id_cache = {}
                    face_layer.id_cache = {}

            _bmesh = face_layer.node.bmesh

            b3d_face = face_layer.find_b3d_face(item_id)

            # When face already exists, then remove the face
            if b3d_face is not None:
                _bmesh.faces.remove(b3d_face)

            # Add new one
            if value[3] == 0:
                _bmesh.faces.new([vert_layer.b3d_vertex(vert_id) for vert_id in value[0:3]])
            else:
                _bmesh.faces.new([vert_layer.b3d_vertex(vert_id) for vert_id in value])

            # Try to update last face ID
            if face_layer.node.last_face_ID is None or \
                    face_layer.node.last_face_ID < item_id:
                face_layer.node.last_face_ID = item_id

            b3d_face = face_layer.id_cache[item_id] = _bmesh.faces[-1]
            id_layer = _bmesh.faces.layers.int.get('FaceIDs')
            b3d_face[id_layer] = item_id

            # Update Blender mesh
            _bmesh.to_mesh(face_layer.node.mesh)
            face_layer.node.mesh.update()

        return face_layer

    @classmethod
    def cb_receive_layer_unset_value(cls, session, node_id, layer_id, item_id):
        """
        This method is called, when some vertex was deleted
        """
        face_layer = super(VerseFaces, cls).cb_receive_layer_unset_value(session, node_id, layer_id, item_id)

        # Update mesh only in situation, when it was changed by someone else
        if face_layer.node.locked_by_me is False:

            vert_layer = face_layer.node.vertices
            edge_layer = face_layer.node.edges

            if face_layer.node.bmesh is None:
                face_layer.node.bmesh = bmesh.new()
                face_layer.node.bmesh.from_mesh(face_layer.node.mesh)
                face_layer.node.bm_from_edit_mesh = False
            else:
                try:
                    face_layer.node.bmesh.faces
                except ReferenceError:
                    face_layer.node.bmesh = bmesh.new()
                    face_layer.node.bmesh = face_layer.node.bmesh.from_mesh(face_layer.node.mesh)
                    vert_layer.id_cache = {}
                    edge_layer.id_cache = {}
                    face_layer.id_cache = {}

            _bmesh = face_layer.node.bmesh

            b3d_face = face_layer.find_b3d_face(item_id)

            # Remove face
            if b3d_face is not None:
                _bmesh.faces.remove(b3d_face)
                # Update Blender mesh
                _bmesh.to_mesh(face_layer.node.mesh)
                face_layer.node.mesh.update()

        return face_layer


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
        self.bm_from_edit_mesh = False
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
            self.bmesh = None

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
            elem[lay] = elem.index

        return last_elem_id

    def get_verse_id_of_vertex(self, bpy_vert, alive_verts):
        """
        Return ID of blender vertex at Verse server
        """
        layer = self.bmesh.verts.layers.int.get('VertIDs')
        verse_id = bpy_vert[layer]
        # It is necessary to detect uniqueness of vertex verse IDs, because Blender
        # duplicates values of layers, when vertex/edge/face is duplicated
        if verse_id in alive_verts:
            return -1
        else:
            return verse_id

    def get_verse_id_of_edge(self, bpy_edge, alive_edges):
        """
        Return ID of blender edge at Verse server
        """
        layer = self.bmesh.edges.layers.int.get('EdgeIDs')
        verse_id = bpy_edge[layer]
        if verse_id in alive_edges:
            return -1
        else:
            return verse_id

    def get_verse_id_of_face(self, bpy_face, alive_faces):
        """
        Return ID of blender face at Verse server
        """
        layer = self.bmesh.faces.layers.int.get('FaceIDs')
        verse_id = bpy_face[layer]
        if verse_id in alive_faces:
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
            verse_id = self.get_verse_id_of_vertex(b3d_vert, alive_verts)
            # New vertex was created. Try to send it to Verse server, store it in cache and save verse ID
            if verse_id == -1:
                # Update the last vertex ID
                self.last_vert_ID += 1
                verse_id = self.last_vert_ID
                # Send new vertex position to Verse server
                self.vertices.items[verse_id] = tuple(b3d_vert.co)
                # Store verse vertex ID in bmesh layer
                layer = self.bmesh.verts.layers.int.get('VertIDs')
                b3d_vert[layer] = verse_id
            # Position of vertex was changed?
            elif self.vertices.items[verse_id] != tuple(b3d_vert.co):
                # This will send updated position of vertex
                self.vertices.items[verse_id] = tuple(b3d_vert.co)

            # Mark vertex as alive
            alive_verts[verse_id] = b3d_vert.index

        # Try to find deleted vertices
        rem_verts = [vert_id for vert_id in self.vertices.items.keys() if vert_id not in alive_verts]
        # This will send unset commands for deleted vertices
        for vert_id in rem_verts:
            self.vertices.items.pop(vert_id)

    def __send_edge_updates(self):
        """
        Try to send updates of topology (edges)
        """

        alive_edges = {}

        # Go through bmesh and try to detect changes in edges (new created edges or deleted edges)
        for b3d_edge in self.bmesh.edges:
            verse_id = self.get_verse_id_of_edge(b3d_edge, alive_edges)
            # New edge was created. Try to send it to Verse server
            if verse_id == -1:
                self.last_edge_ID += 1
                verse_id = self.last_edge_ID
                # Send new edge to Verse server
                self.edges.items[verse_id] = (
                    self.get_verse_id_of_vertex(b3d_edge.verts[0], {}),
                    self.get_verse_id_of_vertex(b3d_edge.verts[1], {})
                )
                # Store edge ID in bmesh layer
                layer = self.bmesh.edges.layers.int.get('EdgeIDs')
                b3d_edge[layer] = verse_id
            else:
                # Was edge changed?
                edge = (
                    self.get_verse_id_of_vertex(b3d_edge.verts[0], {}),
                    self.get_verse_id_of_vertex(b3d_edge.verts[1], {})
                )
                if self.edges.items[verse_id] != edge:
                    self.edges.items[verse_id] = edge

            alive_edges[verse_id] = b3d_edge.index

        # Try to find deleted edges
        rem_edges = [edge_id for edge_id in self.edges.items.keys() if edge_id not in alive_edges]
        # This will send unset commands for deleted edges
        for edge_id in rem_edges:
            self.edges.items.pop(edge_id)

    def __send_face_updates(self):
        """
        Try to send updates of topology (faces)
        """

        def b3d_face_to_tuple(_b3d_face):
            _face = None
            if len(_b3d_face.verts) == 3:
                _face = (
                    self.get_verse_id_of_vertex(_b3d_face.verts[0], {}),
                    self.get_verse_id_of_vertex(_b3d_face.verts[1], {}),
                    self.get_verse_id_of_vertex(_b3d_face.verts[2], {}),
                    0
                )
            elif len(b3d_face.verts) == 4:
                _face = tuple(self.get_verse_id_of_vertex(vert, {}) for vert in _b3d_face.verts)
                # The last item of tuple can not be zero, because it indicates triangle.
                if _face[3] == 0:
                    # Rotate the face to get zero to the beginning of the tuple
                    _face = (_face[3], _face[0], _face[1], _face[2])
            else:
                # TODO: tesselate face
                print('Error: Face with more than 4 vertices is not supported')
            return _face

        alive_faces = {}

        # Go through bmesh faces and try to detect changes (newly created)
        for b3d_face in self.bmesh.faces:
            verse_id = self.get_verse_id_of_face(b3d_face, alive_faces)
            # New face was created. Try to send it to Verse server
            if verse_id == -1:
                self.last_face_ID += 1
                verse_id = self.last_face_ID
                self.quads.items[verse_id] = b3d_face_to_tuple(b3d_face)
                # Store edge ID in bmesh layer
                layer = self.bmesh.faces.layers.int.get('FaceIDs')
                b3d_face[layer] = verse_id
            else:
                # Was face changed?
                face = b3d_face_to_tuple(b3d_face)
                if self.quads.items[verse_id] != face:
                    self.quads.items[verse_id] = face

            alive_faces[verse_id] = b3d_face.index

        # Try to find deleted faces
        rem_faces = [face_id for face_id in self.quads.items.keys() if face_id not in alive_faces]
        # This will send unset commands for deleted faces
        for face_id in rem_faces:
            self.quads.items.pop(face_id)

    def send_updates(self):
        """
        Try to send update of edit mesh to Verse server
        """
        if self.bmesh is None:
            self.bmesh = bmesh.from_edit_mesh(self.mesh)
            self.bm_from_edit_mesh = True
        else:
            if self.bm_from_edit_mesh is False:
                self.bmesh = bmesh.from_edit_mesh(self.mesh)
                self.bm_from_edit_mesh = True
            else:
                # Check if bmesh is still fresh
                try:
                    self.bmesh.verts
                except ReferenceError:
                    self.bmesh = bmesh.from_edit_mesh(self.mesh)
        self.__send_vertex_updates()
        self.__send_edge_updates()
        self.__send_face_updates()

    def create_empty_b3d_mesh(self, object_node):
        """
        Create empty mesh and create blender layers for entity IDs
        """
        # Mesh should be empty ATM
        self.mesh = object_node.obj.data
        self.bmesh = bmesh.new()
        self.bmesh.from_mesh(self.mesh)
        # Create layers for verse IDs
        self.bmesh.verts.layers.int.new('VertIDs')
        self.bmesh.edges.layers.int.new('EdgeIDs')
        self.bmesh.faces.layers.int.new('FaceIDs')
        # Safe blender layers containing IDs to original mesh
        self.bmesh.to_mesh(self.mesh)
        self.bmesh.free()
        self.bmesh = None

    @classmethod
    def cb_receive_node_link(cls, session, parent_node_id, child_node_id):
        """
        When link between nodes is changed, then try to create mesh.
        """
        mesh_node = super(VerseMesh, cls).cb_receive_node_link(
            session=session,
            parent_node_id=parent_node_id,
            child_node_id=child_node_id
        )

        try:
            object_node = object3d.VerseObject.objects[parent_node_id]
        except KeyError:
            pass
        else:
            mesh_node.create_empty_b3d_mesh(object_node)
            mesh_node.mesh.verse_node_id = child_node_id
            object_node.mesh_node = mesh_node

        return mesh_node

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
            try:
                object_node = object3d.VerseObject.objects[parent_id]
            except KeyError:
                # The object was not created yet
                pass
            else:
                mesh_node.create_empty_b3d_mesh(object_node)
                mesh_node.mesh.verse_node_id = node_id
                object_node.mesh_node = mesh_node

        return mesh_node

    def draw_IDs(self, context, obj):
        """
        This method draws Verse IDs of vertices, edges and faces
        """

        font_id, font_size, my_dpi = 0, 12, 72

        bgl.glColor3f(1.0, 1.0, 0.0)

        for vert_id, vert_co in self.vertices.items.items():

            coord_2d = location_3d_to_region_2d(
                context.region,
                context.space_data.region_3d,
                obj.matrix_world * mathutils.Vector(vert_co))

            # When coordinates are not outside window, then draw the name of avatar
            if coord_2d is not None:
                # TODO: add to Add-on options
                blf.size(font_id, font_size, my_dpi)
                # text_width, text_height = blf.dimensions(font_id, self.username)
                blf.position(font_id, coord_2d[0] + 2, coord_2d[1] + 2, 0)
                blf.draw(font_id, str(vert_id))

        bgl.glColor3f(0.0, 1.0, 0.0)

        for edge_id, edge_ids in self.edges.items.items():
            vert1 = self.vertices.items[edge_ids[0]]
            vert2 = self.vertices.items[edge_ids[1]]

            edge_co = mathutils.Vector(((vert2[0] + vert1[0])/2.0, (vert2[1] + vert1[1])/2.0, (vert2[2] + vert1[2])/2.0))

            # Draw username
            coord_2d = location_3d_to_region_2d(
                context.region,
                context.space_data.region_3d,
                obj.matrix_world * edge_co)

            # When coordinates are not outside window, then draw the name of avatar
            if coord_2d is not None:
                # TODO: add to Add-on options
                blf.size(font_id, font_size, my_dpi)
                # text_width, text_height = blf.dimensions(font_id, self.username)
                blf.position(font_id, coord_2d[0] + 2, coord_2d[1] + 2, 0)
                blf.draw(font_id, str(edge_id))

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
