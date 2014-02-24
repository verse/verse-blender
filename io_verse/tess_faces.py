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
This module tries to reconstruct tessellated faces
"""

def sorted_edge(edge):
    """
    This function returns sorted edge; e.g.: (4, 1) -> (1, 4).
    """
    return tuple(sorted(edge))


def face_edges(face):
    """
    Generate list of face edges. TODO: return iterator
    """
    face_edges = []
    prev_vert = None
    for vert in face:
        if prev_vert is not None:
            edge = (prev_vert, vert)
            face_edges.append(sorted_edge(edge))
        prev_vert = vert
    face_edges.append(sorted_edge((face[-1], face[0])))
    return face_edges


def extend_polygon(polygon, face, inner_edge):
    """
    """
    polygon.extend([ vert for vert in face if vert not in inner_edge ])


class Mesh(object):
    """
    Class representing Mesh
    """

    def __init__(self):
        """
        Constructor
        """
        self.verticies = {}
        self.edges = []
        self.polygons = []
        self.tess_faces = {}

    def add_verticies(self, verts):
        """
        """
        for index, vert in enumerate(verts):
            self.verticies[index] = vert

    def add_edges(self, edges):
        """
        """
        self.edges.extend([sorted_edge(edge) for edge in edges])

    def add_tess_face(self, face):
        """
        """
        # Create list of inner edges of polygon from face
        inner_edges = [ edge for edge in face_edges(face) if edge not in self.edges ]
        # Try to find existing inner edges
        for inner_edge in inner_edges:
            if inner_edge in self.tess_faces.keys():
                polygon = self.tess_faces[inner_edge]
                extend_polygon(polygon, face, inner_edge)
                self.tess_faces.pop(inner_edge)
                if polygon not in self.tess_faces.values():
                    self.polygons.append(polygon)
            else:
                self.tess_faces[inner_edge] = list(face)


def main():
    """
    """
    mesh = Mesh()
    mesh.add_verticies(((0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)))
    mesh.add_edges(((0, 1), (1, 2), (2, 3), (3, 0)))
    mesh.add_tess_face((0, 1, 2))
    mesh.add_tess_face((0, 2, 3))
    print(mesh.verticies)
    print(mesh.edges)
    print(mesh.tess_faces)
    print(mesh.polygons)

if __name__ == '__main__':
    main()
