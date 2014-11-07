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
from . import object3d
from . import avatar_view
from . import ui


VERSE_SCENE_CT = 123
TG_INFO_CT = 0
TAG_SCENE_NAME_CT = 0

VERSE_SCENE_DATA_CT = 124


def scene_update(node_id):
    """
    This function tries to send differencies between current scene
    and scene node
    """
    vrs_session = session.VerseSession.instance()
    try:
        scene_node = vrs_session.nodes[node_id]
    except KeyError:
        pass
    else:
        try:
            current_name = scene_node.name
        except AttributeError:
            pass
        else:
            if current_name != bpy.context.scene.name:
                scene_node.name = bpy.context.scene.name


def cb_scene_update(context):
    """
    This function is used as callback function. It is called,
    when something is changed in the scene
    """

    objects = bpy.data.objects
    scenes = bpy.data.scenes
    wm = bpy.context.window_manager

    if wm.verse_connected is True:
        # Was any object updated?
        if objects.is_updated:
            for obj in objects:
                if obj.is_updated and obj.verse_node_id != -1:
                    object3d.object_update(obj.verse_node_id)

        # TODO: Make this part of Blender API working
        # if scenes.is_updated:
        #     print('### Some scene is updated')
        #     for sce in scenes:
        #         print('### Scene is updated:', sce.name)
        #         if sce.is_updated and sce.verse_node_id != -1:
        #             print('### Scene ID:', sce.verse_node_id)
        #             scene_update(sce.verse_node_id)


class VerseSceneData(vrsent.VerseNode):
    """
    Custom VerseNode subclass storing Blender data
    """

    custom_type = VERSE_SCENE_DATA_CT

    def __init__(self, session, node_id=None, parent=None, user_id=None, custom_type=VERSE_SCENE_DATA_CT, autosubscribe=False):
        """
        Constructor of VerseSceneData
        """
        super(VerseSceneData, self).__init__(session, node_id, parent, user_id, custom_type)
        self.objects = {}
        self.meshes = {}
        self._autosubscribe = autosubscribe

    def _auto_subscribe(self):
        """
        User has to subscribe to this node manualy, when it is node created by
        other Blender.
        """
        try:
            autosubscribe = self._autosubscribe
        except AttributeError:
            autosubscribe = False
        return autosubscribe

    def subscribe(self):
        """
        This method is called, when Blender user wants to subscribe to the
        scene data shared at Verse server.
        """
        # Send subscribe command to Verse server
        subscribed = super(VerseSceneData, self).subscribe()
        if subscribed is True:
            # Save information about subscription to Blender scene too
            bpy.context.scene.subscribed = True
            # Save ID of scene node in current scene
            bpy.context.scene.verse_node_id = self.parent.id
            # Save node ID of data node in current scene
            bpy.context.scene.verse_data_node_id = self.id
            # Save hostname of server in current scene
            bpy.context.scene.verse_server_hostname = self.session.hostname
            # Save port (service) of server in current scene
            bpy.context.scene.verse_server_service = self.session.service
            # Store/share id of the verse_scene in the AvatarView
            avatar = avatar_view.AvatarView.my_view()
            avatar.scene_node_id.value = (self.parent.id,)
            # Add Blender callback function that sends scene updates to Verse server
            bpy.app.handlers.scene_update_post.append(cb_scene_update)
        # Force redraw of 3D view
        ui.update_all_views(('VIEW_3D',))
        return subscribed

    def unsubscribe(self):
        """
        This method is called, when Blender user wants to unsubscribe
        from scene data.
        """
        # Send unsubscribe command to Verse server
        subscribed = super(VerseSceneData, self).unsubscribe()
        if subscribed is False:
            # Save information about subscription to Blender scene too
            bpy.context.scene.subscribed = False
            # Reset id of the verse_scene in the AvatarView
            avatar = avatar_view.AvatarView.my_view()
            avatar.scene_node_id.value = (0,)
            # Remove Blender callback function
            bpy.app.handlers.scene_update_post.remove(cb_scene_update)
            # TODO: switch all shared data to right state
            # (nodes of objects, nodes of meshes, etc.) or destroy them
        # Force redraw of 3D view
        ui.update_all_views(('VIEW_3D',))
        return subscribed

    def __update_item_slot(self):
        """
        This method tries to update properties in slot of scene list
        """
        try:
            scene_node_id = self.parent.id
        except AttributeError:
            pass
        else:
            scene_item = None
            for _scene_item in bpy.context.scene.verse_scenes:
                if _scene_item.node_id == scene_node_id:
                    scene_item = _scene_item
                    break
            if scene_item is not None:
                # Add ID of this node to the coresponding group of properties
                scene_item.data_node_id = self.id

    @classmethod
    def _receive_node_create(cls, session, node_id, parent_id, user_id, custom_type):
        """
        When new node is created or verse server confirms creating of data node
        for current scene, than this callback method is called.
        """
        # Call parent class
        scene_data_node = super(VerseSceneData, cls)._receive_node_create(session=session,
            node_id=node_id,
            parent_id=parent_id,
            user_id=user_id,
            custom_type=custom_type)
        scene_data_node.__update_item_slot()
        return scene_data_node

    @classmethod
    def _receive_node_link(cls, session, parent_node_id, child_node_id):
        """
        When parent node of this type of node is chaned at Verse server, then
        this callback method is called, when coresponding command is received.
        """
        # Call parent class
        scene_data_node = super(VerseSceneData, cls)._receive_node_link(session=session,
            parent_node_id=parent_node_id,
            child_node_id=child_node_id)
        scene_data_node.__update_item_slot()
        return scene_data_node


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

    @classmethod
    def _receive_tag_set_values(cls, session, node_id, tg_id, tag_id, value):
        """
        This method is called, when name of scene is set
        """
        tag = super(VerseSceneName, cls)._receive_tag_set_values(session, node_id, tg_id, tag_id, value)
        # Update name of scene, when name of current scene was changed by other Blender
        if node_id == bpy.context.scene.verse_node_id:
            try:
                verse_scene = session.nodes[node_id]
            except KeyError:
                pass
            else:
                bpy.context.scene.name = verse_scene.name
        # Update list of scenes shared at Verse server
        ui.update_all_views(('PROPERTIES',))
        return tag


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

        if node_id is None:
            # Create node with data, when this node was created by this Blender
            self.data_node = VerseSceneData(session=session, parent=self, autosubscribe=True)
            #self.data_node._autosubscribe = True
        else:
            self.data_node = None

    @classmethod
    def _receive_node_create(cls, session, node_id, parent_id, user_id, custom_type):
        """
        When new node is created or verse server confirms creating of node for current
        scene, than this callback method is called.
        """

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

    def invoke(self, context, event):
        """
        Operator for subscribing to Verse scene node
        """
        vrs_session = session.VerseSession.instance()
        scene = context.scene
        scene_item = scene.verse_scenes[scene.cur_verse_scene_index]
        try:
            verse_scene_data = vrs_session.nodes[scene_item.data_node_id]
        except KeyError:
            return {'CANCELLED'}
        else:
            # Send node subscribe to the selected scene data node
            verse_scene_data.subscribe()
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        """
        This class method is used, when Blender check, if this operator can be
        executed
        """
        # Allow this operator only in situation, when Blender is not subscribed
        # to any scene node
        wm = context.window_manager
        scene = context.scene
        if wm.verse_connected == True and scene.cur_verse_scene_index != -1:
            vrs_session = session.VerseSession.instance()
            for scene_item in scene.verse_scenes:
                try:
                    verse_scene_data = vrs_session.nodes[scene_item.data_node_id]
                except KeyError:
                    continue
                if verse_scene_data.subscribed is True:
                    return False
            return True
        else:
            return False


class VERSE_SCENE_OT_unsubscribe(bpy.types.Operator):
    """
    This operator unsubscribes from scene node.
    """
    bl_idname      = 'scene.verse_scene_node_unsubscribe'
    bl_label       = "Unsubscribe from Scene"
    bl_description = "Unsubscribe from Verse scene node"

    def invoke(self, context, event):
        """
        Operator for unsubscribing from Verse scene node
        """
        vrs_session = session.VerseSession.instance()
        scene = context.scene
        scene_item = scene.verse_scenes[scene.cur_verse_scene_index]
        try:
            verse_scene_data = vrs_session.nodes[scene_item.data_node_id]
        except KeyError:
            return {'CANCELLED'}
        else:
            # Send node unsubscribe to the selected scene data node
            verse_scene_data.unsubscribe()
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        """
        This class method is used, when Blender check, if this operator can be
        executed
        """
        # Allow this operator only in situation, when scene with subscribed
        # data node is selected
        wm = context.window_manager
        scene = context.scene
        if wm.verse_connected == True and scene.cur_verse_scene_index != -1:
            scene_item = scene.verse_scenes[scene.cur_verse_scene_index]
            vrs_session = session.VerseSession.instance()
            try:
                verse_scene_data = vrs_session.nodes[scene_item.data_node_id]
            except KeyError:
                return False
            if verse_scene_data.subscribed is True:
                return True
            else:
                return False
        else:
            return False


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
                try:
                    verse_scene_data = vrs_session.nodes[item.data_node_id]
                except KeyError:
                    pass
                else:
                    if verse_scene_data.subscribed is True:
                        layout.label('', icon='FILE_TICK')
            elif self.layout_type in {'GRID'}:
                layout.alignment = 'CENTER'
                layout.label(verse_scene.name)


class VERSE_SCENE_MT_menu(bpy.types.Menu):
    """
    Menu for scene list
    """
    bl_idname = 'scene.verse_scene_menu'
    bl_label = 'Verse Scene Specials'
    bl_description = 'Menu for list of Verse scenes'

    def draw(self, context):
        """
        Draw menu
        """
        layout = self.layout
        layout.operator('scene.blender_scene_share')
        layout.operator('scene.verse_scene_node_subscribe')
        layout.operator('scene.verse_scene_node_unsubscribe')

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
    bl_label       = 'Verse Scenes'
    bl_description = 'Panel with Verse scenes shared at Verse server'

    @classmethod
    def poll(cls, context):
        """
        Can be this panel visible?
        """
        # Return true only in situation, when client is connected to Verse server
        wm = context.window_manager
        if wm.verse_connected == True:
            return True
        else:
            return False

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
classes = (VERSE_SCENE_UL_slot, \
    VERSE_SCENE_MT_menu, \
    VERSE_SCENE_panel, \
    VERSE_SCENE_OT_share, \
    VERSE_SCENE_OT_subscribe, \
    VERSE_SCENE_OT_unsubscribe
)


def register():
    """
    This method register all methods of this submodule
    """
    for c in classes:
        bpy.utils.register_class(c)
    ui.init_scene_properties()


def unregister():
    """
    This method unregister all methods of this submodule
    """
    for c in classes:
        bpy.utils.unregister_class(c)
    ui.reset_scene_properties()


if __name__ == '__main__':
    register()
