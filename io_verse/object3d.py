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


VERSE_OBJECT_CT = 125
TG_TRANSFORM_CT = 0
TAG_POSITION_CT = 0
TAG_ROTATION_CT = 1
TAG_SCALE_CT = 2


def object_update(node_id):
    """
    This function is called by callback function, when
    shared object is changed by user.
    """
    # TODO: send changed properties to Verse server
    pass


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

    def __init__(self, session, node_id=None, parent=None, user_id=None, custom_type=VERSE_OBJECT_CT):
        """
        Constructor of VerseObject
        """
        super(VerseObject, self).__init__(session, node_id, parent, user_id, custom_type)
        self.mesh = None
        self.transform = vrsent.VerseTagGroup(node=self, custom_type=TG_TRANSFORM_CT)
        self.transform.pos = None
        self.transform.rot = None
        self.transform.scale = None


# List of Blender classes in this submodule
classes = ()


def init_properties():
    """
    Init properties in blender object data type
    """
    bpy.types.Object.verse_node_id = bpy.props.IntProperty( \
        name = "ID of verse object node", \
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
