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
This module is used for connecting to Verse server. It adds some
menu items and there are class operator definition for connect
dialogs.
"""


if "bpy" in locals():
    import imp
    imp.reload(vrsent)
    imp.reload(session)
else:
    import bpy
    import verse as vrs
    from .vrsent import vrsent
    from . import session


class VerseError(bpy.types.Operator):
    """
    Operator that is used for reporting Verse errors
    """
    bl_idname = "wm.verse_error"
    bl_label = "Verse Error"
    
    error_string = bpy.props.StringProperty(name="Error")
    
    def execute(self, context):
        # TODO: display popup, report doesn't work :-(
        self.report({'ERROR'}, "%s" % (self.error_string))
    
    def invoke(self, context, event):
        self.execute(context)    
        return {'FINISHED'}


class VerseAuthDialogOperator(bpy.types.Operator):
    """
    Class with user authenticate dialog (username and password)
    """
    bl_idname = "scene.verse_auth_dialog_operator" 
    bl_label = "User Authenticate dialog" 

    dialog_username = bpy.props.StringProperty(name="Username")
    dialog_password = bpy.props.StringProperty(name="Password", subtype='PASSWORD')

    def __init__(self):
        pass

    def execute(self, context):
        vrs_session = session.VerseSession.instance()
        if(vrs_session is not None):
            vrs_session.my_username = self.dialog_username
            vrs_session.my_password = self.dialog_password
            vrs_session.send_user_authenticate(self.dialog_username, vrs.UA_METHOD_NONE, "")
        return {'FINISHED'} 

    def invoke(self, context, event): 
        wm = context.window_manager 
        return wm.invoke_props_dialog(self)


class VerseConnectDialogOperator(bpy.types.Operator):
    """
    Class with connect dialog, where user can choose URL of
    Verse server
    """
    bl_idname = "scene.verse_connect_dialog_operator" 
    bl_label = "Connect dialog" 

    vrs_server_name = bpy.props.StringProperty(name="Verse Server")
    vrs_server_port = bpy.props.StringProperty(name="Port")

    def execute(self, context):
        # Connect to Verse server
        session.VerseSession(self.vrs_server_name, self.vrs_server_port, vrs.DGRAM_SEC_NONE)
        # Start timer
        bpy.ops.wm.modal_timer_operator()
        self.report({'INFO'}, "Connecting to: '%s'" % (self.vrs_server_name))
        return {'FINISHED'} 

    def invoke(self, context, event): 
        wm = context.window_manager 
        return wm.invoke_props_dialog(self)


class VerseClientDisconnect(bpy.types.Operator):
    """
    This class will try to disconnect Blender from Verse server
    """
    bl_idname = "scene.verse_client_disconnect"
    bl_label = "Disconnect"
    bl_description = "Disconnect from Verse server"
    
    @classmethod
    def poll(cls, context): # NOT sure about this
        if session.VerseSession.instance() is not None:
            state = session.VerseSession.instance().state
        else:
            return False
        if state == 'CONNECTING' or state == 'CONNECTED':
            return True
        else:
            return False
    
    def execute(self, context):
        vrs_session = session.VerseSession.instance()
        vrs_session.send_connect_terminate()
        return {'FINISHED'}


class VerseClientConnect(bpy.types.Operator):
    """
    This class will try to connect Blender to Verse server
    """
    bl_idname = "scene.verse_client_connect" # NOT sure about this
    bl_label = "Connect ..."
    bl_description = "Connect to Verse server"

    @classmethod    
    def poll(cls, context):
        if session.VerseSession.instance() is not None:
            state = session.VerseSession.instance().state
        else:
            return True
        if state == 'DISCONNECTED':
            return True
        else:
            return False
    
    def execute(self, context):
        bpy.ops.scene.verse_connect_dialog_operator('INVOKE_DEFAULT', \
            vrs_server_name='localhost', \
            vrs_server_port='12344')
        return {'FINISHED'}
        

class VerseMenu(bpy.types.Menu):
    """
    Main Verse menu (it contains Connect... and Disconnect...)
    """
    bl_label = "Verse Menu"
    bl_idname = "INFO_MT_verse"

    def draw(self, context):
        layout = self.layout

        layout.operator("scene.verse_client_connect")
        layout.operator("scene.verse_client_disconnect")


def draw_item(self, context):
    """
    This function draw item with Verse submenu
    """
    layout = self.layout
    layout.menu(VerseMenu.bl_idname)


def init_properties():
    """
    This method initialize properties related to connection
    """
    bpy.types.WindowManager.verse_connected = bpy.props.BoolProperty( \
        name = "Connected to Server", \
        default = False, \
        description = "Is Blender connected to Verse server"
    )


# List of Blender classes in this submodule
classes = (
    VerseAuthDialogOperator,
    VerseConnectDialogOperator,
    VerseClientConnect,
    VerseClientDisconnect,
    VerseMenu,
    VerseError
)


def register():
    """
    This method register all methods of this submodule and 
    adds Verse submenu to the File menu
    """
    
    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.INFO_MT_file.append(draw_item)

    init_properties()


def unregister():
    """
    This method unregister all methods of this submodule and
    removes Verse submenu from File menu
    """

    for c in classes:
        bpy.utils.unregister_class(c)

        # 
    bpy.types.INFO_MT_file.remove(draw_item)
