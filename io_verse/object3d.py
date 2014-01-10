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
import verse as vrs
from .vrsent import vrsent
from . import session


VERSE_OBJECT_CT = 125
TG_TRANSFORM_CT = 0
TAG_POSITION_CT = 0
TAG_ROTATION_CT = 1
TAG_SCALE_CT = 2


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


class VerseObject(vrsent.VerseNode):
    """
    Custom VerseNode subclass representing Blender object
    """

    node_custom_type = VERSE_OBJECT_CT
    tg_custom_type = TG_TRANSFORM_CT
    custom_type = VERSE_OBJECT_CT

    def __init__(self, session, node_id=None, parent=None, user_id=None, custom_type=VERSE_OBJECT_CT, obj=None):
        """
        Constructor of VerseObject
        """
        super(VerseObject, self).__init__(session, node_id, parent, user_id, custom_type)
        self.obj = obj
        self.mesh = None
        self.transform = vrsent.VerseTagGroup(node=self, custom_type=TG_TRANSFORM_CT)
        if obj is not None:
            self.transform.pos = VerseObjectPosition(tg=self.transform, value=tuple(obj.location))
            self.transform.rot = VerseObjectRotation(tg=self.transform, value=tuple(obj.matrix_local.to_quaternion().normalized()))
            self.transform.scale = VerseObjectScale(tg=self.transform, value=tuple(obj.scale))
        else:
            self.transform.pos = VerseObjectPosition(tg=self.transform)
            self.transform.rot = VerseObjectRotation(tg=self.transform)
            self.transform.scale = VerseObjectScale(tg=self.transform)

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
        object_node.obj.verse_node_id = node_id
        return object_node

    def update(self):
        """
        This method tries to semd fresh properties of mesh object to Verse server
        """

        if self.transform.pos.value != tuple(self.obj.location):
            self.transform.pos.value = tuple(self.obj.location)

        if self.transform.rot.value != tuple(self.obj.matrix_local.to_quaternion().normalized()):
            self.transform.rot.value = tuple(self.obj.matrix_local.to_quaternion().normalized())

        if self.transform.scale.value != tuple(self.obj.scale):
            self.transform.scale.value = tuple(self.obj.scale)


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
                context.active_object.verse_node_id != -1 and \
                context.active_object.subscribed is False:
            return True
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
            VerseObject(session=vrs_session, parent=scene_data_node, obj=context.active_object)
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
                context.active_object.type == 'MESH' and \
                context.active_object.verse_node_id == -1:
            return True
        else:
            return False


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


# List of Blender classes in this submodule
classes = (VERSE_OBJECT_OT_share, \
        VERSE_OBJECT_OT_subscribe, \
        VIEW3D_PT_tools_VERSE_object
    )


def init_properties():
    """
    Init properties in blender object data type
    """
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
