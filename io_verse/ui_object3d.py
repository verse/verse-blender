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
from . import session
from . import object3d
from . import mesh
from . import ui


class VERSE_OBJECT_OT_subscribe(bpy.types.Operator):
    """
    This operator tries to subscribe to Blender Mesh object at Verse server.
    """
    bl_idname = 'object.mesh_object_subscribe'
    bl_label = "Subscribe"
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
        if wm.verse_connected is True and \
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
    bl_idname = 'object.mesh_object_share'
    bl_label = "Share at Verse"
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
            object_node = object3d.VerseObject(
                session=vrs_session,
                parent=scene_data_node,
                obj=context.active_object
            )
            object_node.mesh_node = mesh.VerseMesh(
                session=vrs_session,
                parent=object_node,
                mesh=context.active_object.data,
                autosubscribe=True
            )
            object_node.lock()
            # TODO: lock mesh_node too
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        """
        This class method is used, when Blender check, if this operator can be
        executed
        """
        # Return true only in situation, when client is connected to Verse server
        wm = context.window_manager
        if wm.verse_connected is True and \
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
        scene = context.scene

        # Return true only in situation, when client is connected to Verse server
        if scene.cur_verse_object_index >= 0 and \
                len(scene.verse_objects) > 0:
            return True
        else:
            return False


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
                # Owner
                if verse_object.user_id == vrs_session.user_id:
                    layout.label('Me')
                else:
                    layout.label(str(verse_object.owner.name))
                # Read permissions
                perm_str = ''
                if verse_object.can_read(vrs_session.user_id):
                    perm_str += 'r'
                else:
                    perm_str += '-'
                # Write permissions
                if verse_object.can_write(vrs_session.user_id):
                    perm_str += 'w'
                else:
                    perm_str += '-'
                # Locked/unlocked?
                if verse_object.locked is True:
                    layout.label(perm_str, icon='LOCKED')
                else:
                    layout.label(perm_str, icon='UNLOCKED')
                # Subscribed?
                if verse_object.mesh_node is not None:
                    layout.label('', icon='FILE_TICK')
            elif self.layout_type in {'GRID'}:
                layout.alignment = 'CENTER'
                layout.label(verse_object.name)


class VIEW3D_PT_tools_VERSE_object(bpy.types.Panel):
    """
    Panel with Verse tools for Mesh Object
    """
    bl_category = "Relations"
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
        if wm.verse_connected is True and \
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


class VERSE_OBJECT_panel(bpy.types.Panel):
    """
    GUI of Blender objects shared at Verse server
    """
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'scene'
    bl_label = 'Verse Objects'
    bl_description = 'Panel with Blender objects shared at Verse server'

    @classmethod
    def poll(cls, context):
        """
        Can be this panel visible
        """
        # Return true only in situation, when client is connected
        # to Verse server and it is subscribed to data of some scene
        wm = context.window_manager
        if wm.verse_connected is True and \
                context.scene.subscribed is not False:
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

        row.template_list(
            'VERSE_OBJECT_UL_slot',
            'verse_objects_widget_id',
            scene,
            'verse_objects',
            scene,
            'cur_verse_object_index',
            rows=3
        )

        col = row.column(align=True)
        col.menu('object.verse_object_menu', icon='DOWNARROW_HLT', text="")


# List of Blender classes in this submodule
classes = (
    VERSE_OBJECT_OT_share,
    VERSE_OBJECT_OT_subscribe,
    VIEW3D_PT_tools_VERSE_object,
    VERSE_OBJECT_panel,
    VERSE_OBJECT_UL_slot,
    VERSE_OBJECT_MT_menu
)


def register():
    """
    This method register all methods of this submodule
    """
    for c in classes:
        bpy.utils.register_class(c)
    ui.init_object_properties()


def unregister():
    """
    This method unregister all methods of this submodule
    """
    for c in classes:
        bpy.utils.unregister_class(c)
    ui.reset_object_properties()


if __name__ == '__main__':
    register()

