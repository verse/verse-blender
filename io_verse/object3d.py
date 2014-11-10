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
This module implements sharing Blender objects at Verse server
"""


import bpy
import bgl
import mathutils
import verse as vrs
from .vrsent import vrsent
from . import session
from . import ui


VERSE_OBJECT_CT = 125
# Transformation
TG_TRANSFORM_CT = 0
TAG_POSITION_CT = 0
TAG_ROTATION_CT = 1
TAG_SCALE_CT = 2
# Info
TG_INFO_CT = 1
TAG_NAME_CT = 0
LAYER_BB_CT = 0


def update_3dview(node):
    """
    This method updates all 3D View but not in case, when object is selected/locked
    """
    # 3DView should be updated only in situation, when position/rotation/etc
    # of other objects is changed
    if node.obj.select is False:
        ui.update_all_views(('VIEW_3D',))



def object_update(node_id):
    """
    This function is called by Blender callback function, when
    shared object is changed by user.
    """
    # Send changed properties to Verse server
    vrs_session = session.VerseSession.instance()
    try:
        object_node = vrs_session.nodes[node_id]
    except KeyError:
        pass
    else:
        object_node.update()


class VerseObjectPosition(vrsent.VerseTag):
    """
    Custom VerseTag subclass representing Blender object position
    """

    node_custom_type = VERSE_OBJECT_CT
    tg_custom_type = TG_TRANSFORM_CT
    custom_type = TAG_POSITION_CT

    def __init__(self, tg, tag_id=None, data_type=vrs.VALUE_TYPE_REAL32, count=3, custom_type=TAG_POSITION_CT, value=None):
        """
        Constructor of VerseObjectPosition
        """
        super(VerseObjectPosition, self).__init__(tg, tag_id, data_type, count, custom_type, value)

    @classmethod
    def _receive_tag_set_values(cls, session, node_id, tg_id, tag_id, value):
        """
        This method is called, when new value of verse tag was set
        """
        tag = super(VerseObjectPosition, cls)._receive_tag_set_values(session, node_id, tg_id, tag_id, value)
        # Update position of Blender object that are not locked (not selected)
        if tag.tg.node.locked is False:
            tag.tg.node.obj.location = mathutils.Vector(value)
        # Redraw all 3D views
        update_3dview(tag.tg.node)
        return tag


class VerseObjectRotation(vrsent.VerseTag):
    """
    Custom VerseTag subclass representing Blender object rotation
    """

    node_custom_type = VERSE_OBJECT_CT
    tg_custom_type = TG_TRANSFORM_CT
    custom_type = TAG_ROTATION_CT

    def __init__(self, tg, tag_id=None, data_type=vrs.VALUE_TYPE_REAL32, count=4, custom_type=TAG_ROTATION_CT, value=None):
        """
        Constructor of VerseObjectRotation
        """
        super(VerseObjectRotation, self).__init__(tg, tag_id, data_type, count, custom_type, value)

    @classmethod
    def _receive_tag_set_values(cls, session, node_id, tg_id, tag_id, value):
        """
        This method is called, when new value of verse tag was set
        """
        tag = super(VerseObjectRotation, cls)._receive_tag_set_values(session, node_id, tg_id, tag_id, value)
        # Update rotation of Blender object that are not locked (not selected)
        if tag.tg.node.locked is False:
            tag.tg.node.obj.rotation_quaternion = mathutils.Quaternion(value)
        update_3dview(tag.tg.node)
        return tag


class VerseObjectScale(vrsent.VerseTag):
    """
    Custom VerseTag subclass representing Blender object scale
    """

    node_custom_type = VERSE_OBJECT_CT
    tg_custom_type = TG_TRANSFORM_CT
    custom_type = TAG_SCALE_CT

    def __init__(self, tg, tag_id=None, data_type=vrs.VALUE_TYPE_REAL32, count=3, custom_type=TAG_SCALE_CT, value=None):
        """
        Constructor of VerseObjectScale
        """
        super(VerseObjectScale, self).__init__(tg, tag_id, data_type, count, custom_type, value)

    @classmethod
    def _receive_tag_set_values(cls, session, node_id, tg_id, tag_id, value):
        """
        This method is called, when new value of verse tag was set
        """
        tag = super(VerseObjectScale, cls)._receive_tag_set_values(session, node_id, tg_id, tag_id, value)
        # Update scale of Blender object that are not locked (not selected)
        if tag.tg.node.locked is False:
            tag.tg.node.obj.scale = mathutils.Vector(value)
        update_3dview(tag.tg.node)
        return tag


class VerseObjectBoundingBox(vrsent.VerseLayer):
    """
    Custom VerseLayer subclass representing Blender object bounding box
    """

    node_custom_type = VERSE_OBJECT_CT
    custom_type = LAYER_BB_CT

    def __init__(self, node, parent_layer=None, layer_id=None, data_type=vrs.VALUE_TYPE_REAL32, count=3, custom_type=LAYER_BB_CT):
        """
        Constructor of VerseObjectBoundingBox
        """
        super(VerseObjectBoundingBox, self).__init__(node, parent_layer, layer_id, data_type, count, custom_type)

    @classmethod
    def _receive_layer_set_value(cls, session, node_id, layer_id, item_id, value):
        """
        This method is called, when new value of verse layer was set
        """
        layer = super(VerseObjectBoundingBox, cls)._receive_layer_set_value(session, node_id, layer_id, item_id, value)
        update_3dview(layer.node)
        return layer


class VerseObjectName(vrsent.VerseTag):
    """
    Custom VerseTag subclass representing name of Blender object name
    """

    node_custom_type = VERSE_OBJECT_CT
    tg_custom_type = TG_INFO_CT
    custom_type = TAG_NAME_CT

    def __init__(self, tg, tag_id=None, data_type=vrs.VALUE_TYPE_STRING8, count=1, custom_type=TAG_NAME_CT, value=None):
        """
        Constructor of VerseObjectName
        """
        super(VerseObjectName, self).__init__(tg, tag_id, data_type, count, custom_type, value)

    @classmethod
    def _receive_tag_set_values(cls, session, node_id, tg_id, tag_id, value):
        """
        This method is called, when name of object is set
        """
        tag = super(VerseObjectName, cls)._receive_tag_set_values(session, node_id, tg_id, tag_id, value)
        # Update name of object, when name of the object was changed by other Blender
        try:
            node = session.nodes[node_id]
        except KeyError:
            pass
        else:
            obj = node.obj
            if obj.name != value[0]:
                obj.name = value[0]
        # Update list of scenes shared at Verse server
        ui.update_all_views(('PROPERTIES',))
        return tag


class VerseObject(vrsent.VerseNode):
    """
    Custom VerseNode subclass representing Blender object
    """

    node_custom_type = VERSE_OBJECT_CT
    tg_custom_type = TG_TRANSFORM_CT
    custom_type = VERSE_OBJECT_CT

    objects = {}

    def __init__(self, session, node_id=None, parent=None, user_id=None, custom_type=VERSE_OBJECT_CT, obj=None):
        """
        Constructor of VerseObject
        """
        super(VerseObject, self).__init__(session, node_id, parent, user_id, custom_type)
        self.obj = obj
        self.transform = vrsent.VerseTagGroup(node=self, custom_type=TG_TRANSFORM_CT)
        self.info = vrsent.VerseTagGroup(node=self, custom_type=TG_INFO_CT)
        self.bb = VerseObjectBoundingBox(node=self)
        self.mesh_node = None
        if obj is not None:
            # Transformation
            self.transform.pos = VerseObjectPosition(tg=self.transform, value=tuple(obj.location))
            self.transform.rot = VerseObjectRotation(tg=self.transform, value=tuple(obj.matrix_local.to_quaternion().normalized()))
            self.transform.scale = VerseObjectScale(tg=self.transform, value=tuple(obj.scale))
            # Information
            self.info.name = VerseObjectName(tg=self.info, value=(str(obj.name),))
            # Bounding Box
            item_id = 0
            for bb_point in obj.bound_box:
                self.bb.items[item_id] = (bb_point[0], bb_point[1], bb_point[2])
                item_id += 1
            # Scene
            self.parent = session.nodes[bpy.context.scene.verse_data_node_id]
        else:
            self.transform.pos = VerseObjectPosition(tg=self.transform)
            self.transform.rot = VerseObjectRotation(tg=self.transform)
            self.transform.scale = VerseObjectScale(tg=self.transform)
            self.info.name = VerseObjectName(tg=self.info)

    @property
    def name(self):
        """
        Property of object name
        """
        try:
            name = self.info.name.value
        except AttributeError:
            return ""
        else:
            try:
                return name[0]
            except TypeError:
                return ""

    @classmethod
    def _receive_node_create(cls, session, node_id, parent_id, user_id, custom_type):
        """
        When new object node is created or verse server, then this callback method is called.
        """
        # Call parent class
        object_node = super(VerseObject, cls)._receive_node_create(session=session,
            node_id=node_id,
            parent_id=parent_id,
            user_id=user_id,
            custom_type=custom_type)
        # Create binding between Blender object and node
        if object_node.obj is None:
            # Create Blender mesh
            mesh = bpy.data.meshes.new('Verse')
            # Create Blender object
            obj = bpy.data.objects.new('Verse', mesh)
            # Link Blender object to Blender scene
            bpy.context.scene.objects.link(obj)
            object_node.obj = obj
        object_node.obj.verse_node_id = node_id
        cls.objects[node_id] = object_node
        bpy.context.scene.verse_objects.add()
        bpy.context.scene.verse_objects[-1].node_id = node_id
        ui.update_all_views(('VIEW_3D',))
        return object_node

    @classmethod
    def _receive_node_lock(cls, session, node_id, avatar_id):
        """
        When some object is locked by other user, then it should not
        be selectable
        """
        object_node = super(VerseObject, cls)._receive_node_lock(session, node_id, avatar_id)
        if object_node.session.avatar_id != avatar_id:
            # Only in case, that two clients tried to select one object
            # at the same time and this client didn't win
            object_node.obj.select = False
            if object_node.obj == bpy.context.active_object:
                bpy.context.scene.objects.active = None
            object_node.obj.hide_select = True
        ui.update_all_views(('PROPERTIES', 'VIEW_3D'))
        return object_node

    @classmethod
    def _receive_node_unlock(cls, session, node_id, avatar_id):
        """
        When some object was unlocked, then it should be able to select it again
        """
        object_node = super(VerseObject, cls)._receive_node_unlock(session, node_id, avatar_id)
        if object_node.session.avatar_id != avatar_id:
            object_node.obj.hide_select = False
        ui.update_all_views(('PROPERTIES', 'VIEW_3D'))
        return object_node

    def update(self):
        """
        This method tries to send fresh properties of mesh object to Verse server
        """

        # Position
        if self.transform.pos.value != tuple(self.obj.location):
            self.transform.pos.value = tuple(self.obj.location)

        # Rotation
        if self.transform.rot.value != tuple(self.obj.matrix_local.to_quaternion().normalized()):
            self.transform.rot.value = tuple(self.obj.matrix_local.to_quaternion().normalized())

        # Scale
        if self.transform.scale.value != tuple(self.obj.scale):
            self.transform.scale.value = tuple(self.obj.scale)

        # Bounding box
        item_id = 0
        for bb_point in self.obj.bound_box:
            try:
                if self.bb.items[item_id] != (bb_point[0], bb_point[1], bb_point[2]):
                    self.bb.items[item_id] = (bb_point[0], bb_point[1], bb_point[2])
            except KeyError:
                # Bounding box was not received yet
                break
            item_id += 1

        # TODO: Blender doesn't mark object as changed, when object is selected or
        # unselected :-(. Thus following block of code is not called :-(
        #
        # # When object is selected and it is not locket yet, then try to lock it
        # if self.locked is False and \
        #         self.obj.select is True:
        #     self.lock()
        #
        # # When object is locked by this client and it is not selected anymore,
        # # then unlock it. Other users will be able to work with it.
        # if self.locked is True:
        #     if self.locker == self.session.avatar:
        #         if self.obj.select is False:
        #             self.unlock()

    def draw(self, area, region_data):
        """
        Draw bounding box of object with unsubscribed mesh
        """
        if self.locked is True:
            color = (1.0, 0.0, 0.0, 1.0)
        else:
            color = (0.0, 1.0, 1.0, 1.0)

        # Get & convert the Perspective Matrix of the current view/region.
        persp_matrix = region_data.perspective_matrix
        temp_mat = [persp_matrix[j][i] for i in range(4) for j in range(4)]
        persp_buff = bgl.Buffer(bgl.GL_FLOAT, 16, temp_mat)

        # Store previous OpenGL settings.
        # Store MatrixMode
        matrix_mode_prev = bgl.Buffer(bgl.GL_INT, [1])
        bgl.glGetIntegerv(bgl.GL_MATRIX_MODE, matrix_mode_prev)
        matrix_mode_prev = matrix_mode_prev[0]

        # Store projection matrix
        proj_matrix_prev = bgl.Buffer(bgl.GL_DOUBLE, [16])
        bgl.glGetFloatv(bgl.GL_PROJECTION_MATRIX, proj_matrix_prev)

        # Store Line width
        line_width_prev = bgl.Buffer(bgl.GL_FLOAT, [1])
        bgl.glGetFloatv(bgl.GL_LINE_WIDTH, line_width_prev)
        line_width_prev = line_width_prev[0]

        # Store GL_BLEND
        blend_prev = bgl.Buffer(bgl.GL_BYTE, [1])
        bgl.glGetFloatv(bgl.GL_BLEND, blend_prev)
        blend_prev = blend_prev[0]

        # Store GL_DEPTH_TEST
        depth_test_prev = bgl.Buffer(bgl.GL_BYTE, [1])
        bgl.glGetFloatv(bgl.GL_DEPTH_TEST, depth_test_prev)
        depth_test_prev = depth_test_prev[0]

        # Store GL_LINE_STIPPLE
        line_stipple_prev = bgl.Buffer(bgl.GL_BYTE, [1])
        bgl.glGetFloatv(bgl.GL_LINE_STIPPLE, line_stipple_prev)
        line_stipple_prev = line_stipple_prev[0]

        # Store glColor4f
        col_prev = bgl.Buffer(bgl.GL_FLOAT, [4])
        bgl.glGetFloatv(bgl.GL_COLOR, col_prev)

        # Prepare for 3D drawing
        bgl.glLoadIdentity()
        bgl.glMatrixMode(bgl.GL_PROJECTION)
        bgl.glLoadMatrixf(persp_buff)
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glEnable(bgl.GL_DEPTH_TEST)

        # Compute transformation matrix
        matrix = mathutils.Matrix().Translation(self.transform.pos.value) * \
            mathutils.Quaternion(self.transform.rot.value).to_matrix().to_4x4() * \
            mathutils.Matrix((
                (self.transform.scale.value[0], 0, 0, 0),
                (0, self.transform.scale.value[1], 0, 0),
                (0, 0, self.transform.scale.value[2], 0),
                (0, 0, 0, 1)
            ))

        # Transform points of bounding box
        points = tuple(matrix * mathutils.Vector(item) for item in self.bb.items.values())

        if len(points) == 8:
            # TODO: Draw Bounding box only for unsubscribed objects
            bgl.glLineWidth(1)
            bgl.glColor4f(color[0], color[1], color[2], color[3])
            bgl.glBegin(bgl.GL_LINE_LOOP)
            bgl.glVertex3f(points[0][0], points[0][1], points[0][2])
            bgl.glVertex3f(points[1][0], points[1][1], points[1][2])
            bgl.glVertex3f(points[2][0], points[2][1], points[2][2])
            bgl.glVertex3f(points[3][0], points[3][1], points[3][2])
            bgl.glEnd()
            bgl.glBegin(bgl.GL_LINE_LOOP)
            bgl.glVertex3f(points[4][0], points[4][1], points[4][2])
            bgl.glVertex3f(points[5][0], points[5][1], points[5][2])
            bgl.glVertex3f(points[6][0], points[6][1], points[6][2])
            bgl.glVertex3f(points[7][0], points[7][1], points[7][2])
            bgl.glEnd()
            bgl.glBegin(bgl.GL_LINES)
            bgl.glVertex3f(points[0][0], points[0][1], points[0][2])
            bgl.glVertex3f(points[4][0], points[4][1], points[4][2])
            bgl.glVertex3f(points[1][0], points[1][1], points[1][2])
            bgl.glVertex3f(points[5][0], points[5][1], points[5][2])
            bgl.glVertex3f(points[2][0], points[2][1], points[2][2])
            bgl.glVertex3f(points[6][0], points[6][1], points[6][2])
            bgl.glVertex3f(points[3][0], points[3][1], points[3][2])
            bgl.glVertex3f(points[7][0], points[7][1], points[7][2])
            bgl.glEnd()

        # Restore previous OpenGL settings
        bgl.glLoadIdentity()
        bgl.glMatrixMode(matrix_mode_prev)
        bgl.glLoadMatrixf(proj_matrix_prev)
        bgl.glLineWidth(line_width_prev)
        if not blend_prev:
            bgl.glDisable(bgl.GL_BLEND)
        if not line_stipple_prev:
            bgl.glDisable(bgl.GL_LINE_STIPPLE)
        if not depth_test_prev:
            bgl.glDisable(bgl.GL_DEPTH_TEST)
        bgl.glColor4f(col_prev[0], col_prev[1], col_prev[2], col_prev[3])
