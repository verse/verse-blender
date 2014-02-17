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


VERSE_OBJECT_CT = 125
# Tranformation
TG_TRANSFORM_CT = 0
TAG_POSITION_CT = 0
TAG_ROTATION_CT = 1
TAG_SCALE_CT = 2
# Info
TG_INFO_CT = 1
TAG_NAME_CT = 0
LAYER_BB_CT = 0


def draw_cb(self, context):
    """
    This callback function is called, when view to 3d scene is changed
    """

    # This callback works only for 3D View
    if context.area.type != 'VIEW_3D':
        return

    for obj in VerseObject.objects.values():
        obj.draw(context.area, context.region_data)


def update_all_3dview():
    """
    This method updates all 3D View.
    """
    # Force redraw of all 3D view in all screens
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                # Tag area to redraw
                area.tag_redraw()


def update_all_properties_view():
    """
    This method updates all Properties View.
    """
    # Force redraw of all Properties View in all screens
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'PROPERTIES':
                # Tag area to redraw
                area.tag_redraw()


def update_3dview(node):
    """
    This method updates all 3D View but not in case, when object is selected/locked
    """
    # 3DView should be updated only in situation, when position/rotation/etc
    # of other objects is changed
    if node.obj.select is False:
        update_all_3dview()



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
        if tag.tg.node.obj.select is False:
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
        if tag.tg.node.obj.select is False:
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
        if tag.tg.node.obj.select is False:
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
        This method is called, when new value of verse tag was set
        """
        layer = super(VerseObjectBoundingBox, cls)._receive_layer_set_value(session, node_id, layer_id, item_id, value)
        update_3dview(layer.node)
        return layer


class VerseObjectName(vrsent.VerseTag):
    """
    Custom VerseTag cubclass representing name of Blender object name
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
        update_all_properties_view()
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
        self.mesh_node = None
        self.transform = vrsent.VerseTagGroup(node=self, custom_type=TG_TRANSFORM_CT)
        self.info = vrsent.VerseTagGroup(node=self, custom_type=TG_INFO_CT)
        self.bb = VerseObjectBoundingBox(node=self)
        if obj is not None:
            # Transformation
            self.transform.pos = VerseObjectPosition(tg=self.transform, value=tuple(obj.location))
            self.transform.rot = VerseObjectRotation(tg=self.transform, value=tuple(obj.matrix_local.to_quaternion().normalized()))
            self.transform.scale = VerseObjectScale(tg=self.transform, value=tuple(obj.scale))
            # Information
            self.info.name = VerseObjectName(tg=self.info, value=(str(obj.name),))
            # Boundind Box
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
        if object_node.obj is not None:
            object_node.obj.verse_node_id = node_id
        else:
            mesh = bpy.data.meshes.new('Verse')
            obj = bpy.data.objects.new('Verse', mesh)
            bpy.context.scene.objects.link(obj)
            obj.verse_node_id = node_id
            object_node.obj = obj
        cls.objects[node_id] = object_node
        bpy.context.object.verse_objects.add()
        bpy.context.object.verse_objects[-1].node_id = node_id
        update_all_3dview()
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
        update_all_3dview()
        return object_node

    @classmethod
    def _receive_node_unlock(cls, session, node_id, avatar_id):
        """
        When some object was unlocked, then it should be able to select it again
        """
        object_node = super(VerseObject, cls)._receive_node_unlock(session, node_id, avatar_id)
        if object_node.session.avatar_id != avatar_id:
            object_node.obj.hide_select = False
        update_all_3dview()
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
            if self.bb.items[item_id] != (bb_point[0], bb_point[1], bb_point[2]):
                self.bb.items[item_id] = (bb_point[0], bb_point[1], bb_point[2])
            item_id += 1

        # TODO: Blender doesn't mark object as changed, when object is selected or
        # unselected :-(. Thus following block of code is not called :-(

        # # When object is selected and it is not locket yet, then try to lock it
        # if self.locked is False and \
        #         self.obj.select is True:
        #     self.lock()


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
        perspMatrix = region_data.perspective_matrix
        tempMat = [perspMatrix[j][i] for i in range(4) for j in range(4)]
        perspBuff = bgl.Buffer(bgl.GL_FLOAT, 16, tempMat)

        # Store previous OpenGL settings.
        # Store MatrixMode
        MatrixMode_prev = bgl.Buffer(bgl.GL_INT, [1])
        bgl.glGetIntegerv(bgl.GL_MATRIX_MODE, MatrixMode_prev)
        MatrixMode_prev = MatrixMode_prev[0]

        # Store projection matrix
        ProjMatrix_prev = bgl.Buffer(bgl.GL_DOUBLE, [16])
        bgl.glGetFloatv(bgl.GL_PROJECTION_MATRIX, ProjMatrix_prev)

        # Store Line width
        lineWidth_prev = bgl.Buffer(bgl.GL_FLOAT, [1])
        bgl.glGetFloatv(bgl.GL_LINE_WIDTH, lineWidth_prev)
        lineWidth_prev = lineWidth_prev[0]

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
        bgl.glLoadMatrixf(perspBuff)
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glEnable(bgl.GL_DEPTH_TEST)

        # Compute transformation matrix
        matrix = mathutils.Matrix().Translation(self.transform.pos.value) * \
            mathutils.Quaternion(self.transform.rot.value).to_matrix().to_4x4() * \
            mathutils.Matrix(( \
                (self.transform.scale.value[0], 0, 0, 0), \
                (0, self.transform.scale.value[1], 0, 0), \
                (0, 0, self.transform.scale.value[2], 0), \
                (0, 0, 0, 1)))

        # Transform points of bounding box
        points = tuple(matrix * mathutils.Vector(item) for item in self.bb.items.values())

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
        bgl.glMatrixMode(MatrixMode_prev)
        bgl.glLoadMatrixf(ProjMatrix_prev)
        bgl.glLineWidth(lineWidth_prev)
        if not blend_prev:
            bgl.glDisable(bgl.GL_BLEND)
        if not line_stipple_prev:
            bgl.glDisable(bgl.GL_LINE_STIPPLE)
        if not depth_test_prev:
            bgl.glDisable(bgl.GL_DEPTH_TEST)
        bgl.glColor4f(col_prev[0], col_prev[1], col_prev[2], col_prev[3])


class VERSE_OBJECT_OT_unlock(bpy.types.Operator):
    """
    This operator tries to unlock node representing Blender Mesh object.
    """
    bl_idname      = 'object.mesh_object_unlock'
    bl_label       = "UnLock"
    bl_description = "UnLock node representing Mesh Object at Verse server"

    def invoke(self, context, event):
        """
        This method will try to unlock node representing Mesh Object
        at Verse server
        """
        vrs_session = session.VerseSession.instance()
        node = vrs_session.nodes[context.active_object.verse_node_id]
        node.unlock()
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        """
        This class method is used, when Blender check, if this operator can be
        executed
        """
        # Return true only in situation, when client is connected to Verse server
        wm = context.window_manager
        if wm.verse_connected == True and \
                context.active_object is not None and \
                context.active_object.verse_node_id != -1:
            vrs_session = session.VerseSession.instance()
            try:
                node = vrs_session.nodes[context.active_object.verse_node_id]
            except KeyError:
                return False
            else:
                if node.locked is True:
                    return True
                else:
                    return False
            return True
        else:
            return False


class VERSE_OBJECT_OT_lock(bpy.types.Operator):
    """
    This operator tries to lock node representing Blender Mesh object.
    """
    bl_idname      = 'object.mesh_object_lock'
    bl_label       = "Lock"
    bl_description = "Lock node representing Mesh Object at Verse server"

    def invoke(self, context, event):
        """
        This method will try to lock node representing Mesh Object
        at Verse server
        """
        vrs_session = session.VerseSession.instance()
        node = vrs_session.nodes[context.active_object.verse_node_id]
        node.lock()
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        """
        This class method is used, when Blender check, if this operator can be
        executed
        """
        # Return true only in situation, when client is connected to Verse server
        wm = context.window_manager
        if wm.verse_connected == True and \
                context.active_object is not None and \
                context.active_object.verse_node_id != -1:
            vrs_session = session.VerseSession.instance()
            try:
                node = vrs_session.nodes[context.active_object.verse_node_id]
            except KeyError:
                return False
            else:
                if node.locked is not True:
                    return True
                else:
                    return False
            return True
        else:
            return False


class VERSE_OBJECT_OT_subscribe(bpy.types.Operator):
    """
    This operator tries to subscribe to Blender Mesh object at Verse server.
    """
    bl_idname      = 'object.mesh_object_subscribe'
    bl_label       = "Subscribe"
    bl_description = "Subscribe to data of active Mesh Object at Verse server"

    def invoke(self, context, event):
        """
        This method will try to create new node representing Mesh Object
        at Verse server
        """
        # TODO: add something here
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        """
        This class method is used, when Blender check, if this operator can be
        executed
        """
        # Return true only in situation, when client is connected to Verse server
        wm = context.window_manager
        if wm.verse_connected == True and \
                context.scene.subscribed is not False and \
                context.active_object is not None and \
                context.active_object.verse_node_id != -1:
            vrs_session = session.VerseSession.instance()
            try:
                node = vrs_session.nodes[context.active_object.verse_node_id]
            except KeyError:
                return False
            else:
                if node.subscribed is not True:
                    return True
                else:
                    return False
        else:
            return False


class VERSE_OBJECT_OT_share(bpy.types.Operator):
    """
    This operator tries to share Blender Mesh object at Verse server.
    """
    bl_idname      = 'object.mesh_object_share'
    bl_label       = "Share at Verse"
    bl_description = "Share active Mesh Object at Verse server"

    def invoke(self, context, event):
        """
        This method will try to create new node representing Mesh Object
        at Verse server
        """
        vrs_session = session.VerseSession.instance()
        # Get node with scene data
        try:
            scene_data_node = vrs_session.nodes[context.scene.verse_data_node_id]
        except KeyError:
            return {'CANCELLED'}
        else:
            # Share active mesh object at Verse server
            node = VerseObject(session=vrs_session, parent=scene_data_node, obj=context.active_object)
            #node.lock()
            # TODO: Create node representing mesh data
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        """
        This class method is used, when Blender check, if this operator can be
        executed
        """
        # Return true only in situation, when client is connected to Verse server
        wm = context.window_manager
        if wm.verse_connected == True and \
                context.scene.subscribed is not False and \
                context.active_object is not None and \
                context.active_object.type == 'MESH' and \
                context.active_object.verse_node_id == -1:
            return True
        else:
            return False


class VERSE_OBJECT_MT_menu(bpy.types.Menu):
    """
    Menu for object list
    """
    bl_idname = 'object.verse_object_menu'
    bl_label = 'Verse Object Specials'
    bl_description = 'Menu for list of Verse objects'

    def draw(self, context):
        """
        Draw menu
        """
        layout = self.layout
        layout.operator('object.mesh_object_subscribe')

    @classmethod
    def poll(cls, context):
        """
        This class method is used, when Blender check, if this operator can be
        executed
        """
        obj = context.active_object

        # Return true only in situation, when client is connected to Verse server
        if obj.cur_verse_object_index >= 0 and \
                len(obj.verse_objects) > 0:
            return True
        else:
            return False


class VERSE_OBJECT_NODES_list_item(bpy.types.PropertyGroup):
    """
    Group of properties with representation of Verse scene node
    """
    node_id = bpy.props.IntProperty( \
        name = "Node ID", \
        description = "ID of object node", \
        default = -1)


class VERSE_OBJECT_UL_slot(bpy.types.UIList):
    """
    A custom slot with information about Verse object node
    """
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        """
        This method draw one list item representing node
        """
        vrs_session = session.VerseSession.instance()
        if vrs_session is not None:
            try:
                verse_object = vrs_session.nodes[item.node_id]
            except KeyError:
                return
            if self.layout_type in {'DEFAULT', 'COMPACT'}:
                layout.label(verse_object.name, icon='OBJECT_DATA')
            elif self.layout_type in {'GRID'}:
                layout.alignment = 'CENTER'
                layout.label(verse_object.name)


class VIEW3D_PT_tools_VERSE_object(bpy.types.Panel):
    """
    Panel with Verse tools for Mesh Object
    """
    bl_context = 'objectmode'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = 'Verse'

    @classmethod
    def poll(cls, context):
        """
        Can this panel visible
        """
        # Return true only in situation, when client is connected to Verse server
        wm = context.window_manager
        if wm.verse_connected == True and \
                context.scene.subscribed is not False and \
                context.active_object is not None and \
                context.active_object.type == 'MESH':
            return True
        else:
            return False

    def draw(self, context):
        """
        Definition of panel layout
        """
        layout = self.layout

        col = layout.column(align=True)
        col.operator("object.mesh_object_share")
        col.operator("object.mesh_object_subscribe")
        col.operator("object.mesh_object_lock")
        col.operator("object.mesh_object_unlock")


class VERSE_OBJECT_panel(bpy.types.Panel):
    """
    GUI of Blender objects shared at Verse server
    """
    bl_space_type  = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context     = 'object'
    bl_label       = 'Verse'
    bl_description = 'Panel with Blender objects shared at Verse server'

    def draw(self, context):
        """
        This method draw panel of Verse scenes
        """
        obj = context.active_object
        layout = self.layout

        row = layout.row()

        row.template_list('VERSE_OBJECT_UL_slot', \
            'verse_objects_widget_id', \
            obj, \
            'verse_objects', \
            obj, \
            'cur_verse_object_index', \
            rows = 3)

        col = row.column(align=True)
        col.menu('object.verse_object_menu', icon='DOWNARROW_HLT', text="")

# List of Blender classes in this submodule
classes = (VERSE_OBJECT_OT_share, \
        VERSE_OBJECT_OT_lock, \
        VERSE_OBJECT_OT_unlock, \
        VERSE_OBJECT_OT_subscribe, \
        VIEW3D_PT_tools_VERSE_object, \
        VERSE_OBJECT_panel, \
        VERSE_OBJECT_NODES_list_item, \
        VERSE_OBJECT_UL_slot, \
        VERSE_OBJECT_MT_menu
    )


def init_properties():
    """
    Init properties in blender object data type
    """
    bpy.types.Object.verse_objects = bpy.props.CollectionProperty( \
        type =  VERSE_OBJECT_NODES_list_item, \
        name = "Verse Objects", \
        description = "The list of verse object nodes shared at Verse server" \
    )
    bpy.types.Object.cur_verse_object_index = bpy.props.IntProperty( \
        name = "Index of current Verse object", \
        default = -1, \
        min = -1, \
        max = 1000, \
        description = "The index of curently selected Verse object node"
    )
    bpy.types.Object.verse_node_id = bpy.props.IntProperty( \
        name = "ID of verse node", \
        default = -1, \
        description = "The node ID representing this Object at Verse server"
    )
    bpy.types.Object.subscribed = bpy.props.BoolProperty( \
        name = "Subscribed to data of object node", \
        default = False, \
        description = "Is Blender subscribed to data of mesh object"
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
