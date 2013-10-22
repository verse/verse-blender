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


import bpy
from .vrsent import vrsent


class VerseScene(vrsent.VerseNode):
    """
    Custom subclass of VerseNode representing Blender scene
    """

    custom_type = 123 # Add some more reliable method


class VERSE_SCENE_NODES_list_item(bpy.types.PropertyGroup):
    """
    Group of properties with representation of Verse scene node
    """
    node_id = bpy.props.IntProperty( \
        name = "Node ID", \
        description = "ID of scene node", \
        default = -1)


class BLENDER_SCENE_OT_share(bpy.types.Operator):
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
        scene = context.scene
        # Create new verse scene node
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        """
        This class method is used, when Blender check, if this operator can be
        executed
        """
        # Return true only in situation, when client is connected to Verse server
        wm = context.window_manager
        if wm.verse_connected == True and not context.scene.shared_at_verse_server:
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
        # Send node subscribe to scene node
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        """
        This class method is used, when Blender check, if this operator can be
        executed
        """
        # Return true only in situation, when client is connected to Verse server
        wm = context.window_manager
        if wm.verse_connected == True and not context.scene.shared_at_verse_server:
            return True
        else:
            return False

class VERSE_SCENE_UL_slot(bpy.types.UIList):
    """
    A custom slot with information about Verse scene node
    """
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        verse_scene = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(verse_scene.name, icon='SCENE_DATA')
            layout.label(str(verse_scene.count_of_subscribers))
            # TODO: test if this scene can be shared
            layout.label(text='', icon='LOCKED')
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(verse_scene.name)


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

        layout.operator('scene.blender_scene_share')

        layout.template_list('VERSE_SCENE_UL_slot', \
            'verse_scenes_widget_id', \
            scene, \
            'verse_scenes', \
            scene, \
            'cur_verse_scene_index', \
            rows = 3)

        if scene.cur_verse_scene_index >= 0 and \
                len(scene.verse_scenes) > 0:
            cur_verse_scene = scene.verse_scenes[scene.cur_verse_scene_index]
            layout.separator()
            layout.operator('scene.verse_scene_node_subscribe')


# List of Blender classes in this submodule
classes = (VERSE_SCENE_NODES_list_item, \
    VERSE_SCENE_UL_slot, \
    VERSE_SCENE_panel, \
    BLENDER_SCENE_OT_share, \
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
    bpy.types.Scene.shared_at_verse_server = bpy.props.BoolProperty( \
        name = "Shared at Verse server", \
        default = False,
        description = "The indication if this scene is just now shared at Verse server" \
    )
    bpy.types.Scene.verse_scene_node_id = bpy.props.IntProperty( \
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
