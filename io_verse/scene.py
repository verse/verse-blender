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
This module implements sharing Blender scenes at Verse server
"""

import bpy
import verse as vrs
from .vrsent import vrsent
from . import session


VERSE_SCENE_CT = 123
TG_INFO_CT = 0
TAG_SCENE_NAME_CT = 0

VERSE_SCENE_DATA_CT = 124


class VerseSceneData(vrsent.VerseNode):
    """
    Custom VerseNode subclass storing Blender data
    """

    custom_type = VERSE_SCENE_DATA_CT

    def __init__(self, session, node_id=None, parent=None, user_id=None, custom_type=VERSE_SCENE_DATA_CT):
        """
        Constructor of VerseSceneData
        """
        super(VerseSceneData, self).__init__(session, node_id, parent, user_id, custom_type)
        self.objects = {}
        self.meshes = {}


class VerseSceneName(vrsent.VerseTag):
    """
    Custom subclass of VerseTag representing name of scene
    """

    node_custom_type = VERSE_SCENE_CT
    tg_custom_type = TG_INFO_CT
    custom_type = TAG_SCENE_NAME_CT

    def __init__(self, tg, tag_id=None, data_type=vrs.VALUE_TYPE_STRING8, count=1, custom_type=TAG_SCENE_NAME_CT, value=None):
        """
        Constructor of VerseSceneName
        """
        super(VerseSceneName, self).__init__(tg=tg, tag_id=tag_id, data_type=data_type, count=count, custom_type=custom_type, value=value)


class VerseScene(vrsent.VerseNode):
    """
    Custom subclass of VerseNode representing Blender scene
    """

    custom_type = VERSE_SCENE_CT

    scenes = {}

    def __init__(self, session, node_id=None, parent=None, user_id=None, custom_type=VERSE_SCENE_CT, name=""):
        """
        Constructor of VerseScene
        """
        # When parent is not specified, then set parent node as parent of scene nodes
        if parent is None:
            parent = session.nodes[vrs.SCENE_PARENT_NODE_ID]
        # Call parent init method
        super(VerseScene, self).__init__(session, node_id, parent, user_id, custom_type)
        # Create tag group and tag with name of scene
        self._tg_info = vrsent.VerseTagGroup(node=self, custom_type=TG_INFO_CT)
        self._tg_info._tag_name = VerseSceneName(tg=self._tg_info, value=name)

    @classmethod
    def _receive_node_create(cls, session, node_id, parent_id, user_id, custom_type):
        """
        When new node is created or verse server confirms creating of node for current
        scene, than this callback method is called.
        """

        # When this client created this scene, then assign node_id to coresponding
        # property of current scene
        if parent_id == session.avatar_id:
            bpy.context.scene.verse_node_id = node_id

        # Call parent class
        scene_node = super(VerseScene, cls)._receive_node_create(session=session,
            node_id=node_id,
            parent_id=parent_id,
            user_id=user_id,
            custom_type=custom_type)

        # Add the scene to the dictionary of scenes
        cls.scenes[node_id] = scene_node

        # Add this node to the list of scenes visualized in scene panel
        bpy.context.scene.verse_scenes.add()
        bpy.context.scene.verse_scenes[-1].node_id = node_id

        return scene_node

    @property
    def name(self):
        """
        Property of scene name
        """
        try:
            name = self._tg_info._tag_name.value
        except AttributeError:
            return ""
        else:
            try:
                return name[0]
            except TypeError:
                return ""


class VERSE_SCENE_OT_share(bpy.types.Operator):
    """
    This operator starts to share current Blender scene at Verse server.
    """
    bl_idname      = 'scene.blender_scene_share'
    bl_label       = "Share at Verse"
    bl_description = "Share current Blender scene at Verse scene as new Verse scene node"

    def invoke(self, context, event):
        """
        Operator for subscribing to Verse scene node
        """
        vrs_session = session.VerseSession.instance()
        VerseScene(session=vrs_session, name=(context.scene.name,))
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        """
        This class method is used, when Blender check, if this operator can be
        executed
        """
        # Return true only in situation, when client is connected to Verse server
        wm = context.window_manager
        if wm.verse_connected == True and context.scene.verse_node_id == -1:
            return True
        else:
            return False


class VERSE_SCENE_OT_subscribe(bpy.types.Operator):
    """
    This operator subscribes to existing scene shared at Verse server.
    It will create new Blender scene in current .blend file.
    """
    bl_idname      = 'scene.verse_scene_node_subscribe'
    bl_label       = "Subscribe to Scene"
    bl_description = "Subscribe to verse scene node"

    """Operator for subscribing to Verse scene node"""
    def invoke(self, context, event):
        scene = context.scene
        # TODO: Send node subscribe to the selected scene data node
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        """
        This class method is used, when Blender check, if this operator can be
        executed
        """
        # TODO: allow this operator only in situation, when unsubscribed scene
        # is selected
        wm = context.window_manager
        if wm.verse_connected == True:
            return True
        else:
            return False


class VERSE_SCENE_NODES_list_item(bpy.types.PropertyGroup):
    """
    Group of properties with representation of Verse scene node
    """
    node_id = bpy.props.IntProperty( \
        name = "Node ID", \
        description = "ID of scene node", \
        default = -1)


class VERSE_SCENE_UL_slot(bpy.types.UIList):
    """
    A custom slot with information about Verse scene node
    """
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        vrs_session = session.VerseSession.instance()
        if vrs_session is not None:
            try:
                verse_scene = vrs_session.nodes[item.node_id]
            except KeyError:
                return
            if self.layout_type in {'DEFAULT', 'COMPACT'}:
                layout.label(verse_scene.name, icon='SCENE_DATA')
            elif self.layout_type in {'GRID'}:
                layout.alignment = 'CENTER'
                layout.label(verse_scene.name)


class VERSE_SCENE_MT_menu(bpy.types.Menu):
    """
    Menu for scene list
    """
    bl_idname = 'scene.verse_scene_menu'
    bl_label = "Verse Scene Specials"

    def draw(self, context):
        """
        Draw menu
        """
        layout = self.layout
        layout.operator('scene.blender_scene_share')
        layout.operator('scene.verse_scene_node_subscribe')

    @classmethod
    def poll(cls, context):
        """
        This class method is used, when Blender check, if this operator can be
        executed
        """
        scene = context.scene

        # Return true only in situation, when client is connected to Verse server
        if scene.cur_verse_scene_index >= 0 and \
                len(scene.verse_scenes) > 0:
            return True
        else:
            return False


class VERSE_SCENE_panel(bpy.types.Panel):
    """
    GUI of Verse scene shared at Verse server
    """
    bl_space_type  = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context     = 'scene'
    bl_label       = "Verse Scenes"
 
    def draw(self, context):
        """
        This method draw panel of Verse scenes
        """
        scene = context.scene
        layout = self.layout

        row = layout.row()

        row.template_list('VERSE_SCENE_UL_slot', \
            'verse_scenes_widget_id', \
            scene, \
            'verse_scenes', \
            scene, \
            'cur_verse_scene_index', \
            rows = 3)

        col = row.column(align=True)
        col.menu('scene.verse_scene_menu', icon='DOWNARROW_HLT', text="")


# List of Blender classes in this submodule
classes = (VERSE_SCENE_NODES_list_item, \
    VERSE_SCENE_UL_slot, \
    VERSE_SCENE_MT_menu, \
    VERSE_SCENE_panel, \
    VERSE_SCENE_OT_share, \
    VERSE_SCENE_OT_subscribe
)


def init_properties():
    """
    Init properties in blender scene data type
    """
    bpy.types.Scene.verse_scenes = bpy.props.CollectionProperty( \
        type =  VERSE_SCENE_NODES_list_item, \
        name = "Verse Scenes", \
        description = "The list of verse scene nodes shared at Verse server" \
    )
    bpy.types.Scene.cur_verse_scene_index = bpy.props.IntProperty( \
        name = "Index of current Verse scene", \
        default = -1, \
        min = -1, \
        max = 1000, \
        description = "The index of curently selected Verse scene node"
    )
    bpy.types.Scene.verse_node_id = bpy.props.IntProperty( \
        name = "ID of verse scene node", \
        default = -1, \
        description = "The ID of the verse node representing current Blender scene"
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
