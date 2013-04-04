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


if "bpy" in locals():
    import imp
    imp.reload(model)
else:
    import bpy
    import verse as vrs
    from . import model


# VerseSession class
class VerseSession(vrs.Session):
    """
    Class Session for this Python client
    """
    
    # State of connection
    __state = 'DISCONNECTED'
    
    # Blender could be connected only to one Verse server
    __instance = None
    

    def state():
        """
        state() -> string
        Class getter of state
        """
        return __class__.__state
    

    def instance():
        """
        instance() -> object
        Class getter of instance
        """
        return __class__.__instance
    

    def __init__(self, hostname, service, flag):
        """
        __init__(hostname, service, flag) -> None
        """
        # Call __init__ from parent class to connect to Verse server
        super(VerseSession, self).__init__(hostname, service, flag)
        __class__.__state = 'CONNECTING'
        __class__.__instance = self
        self.fps = 60 # TODO: get current FPS
        # Create empty dictionary of nodes
        self.my_username = ''
        self.my_password = ''


    def __del__(self):
        """
        __del__() -> None
        """
        __class__.__state = 'DISCONNECTED'
        __class__.__instance = None
    

    def _receive_node_create(self, node_id, parent_id, user_id, custom_type):
        """
        receive_node_create(node_id, parent_id, user_id, type) -> None
        """
        print('receive_node_create()', node_id, parent_id, user_id, custom_type)
        # Automatically subscribe to all nodes
        self.send_node_subscribe(vrs.DEFAULT_PRIORITY, node_id, 0, 0)
        # Try to find parent node
        try:
            parent_node = MyNode.nodes[parent_id]
        except KeyError:
            parent_node = None
        # Add node to the dictionary of nodes
        self.nodes[node_id] = MyNode(node_id, parent_node, user_id, custom_type)
        
    
    def _receive_node_destroy(self, node_id):
        """
        receive_node_destroy(node_id) -> None
        """
        print('receive_node_destroy()', node_id)

        node = None
        # Try to find node in dict of nodes
        try:
            node = MyNode.nodes.[node_id]
        except KeyError:
            return

        # Delete node
        if node is not None:
            del node
        
    
    def _receive_connect_terminate(self, error):
        """
        receive_connect_terminate(error) -> none
        """
        print('receive_connect_terminate', error)
        __class__.__state = 'DISCONNECTED'
        __class__.__instance = None
        # Print error message
        bpy.ops.wm.verse_error('INVOKE_DEFAULT', error_string="Disconnected")
        # Clear dictionary of nodes
        MyNode.nodes.clear()
        # TODO: stop timer
  
    
    def _receive_connect_accept(self, user_id, avatar_id):
        """
        receive_connect_accept(user_id, avatar_id) -> None
        """
        print('receive_connect_accept()', user_id, avatar_id)
        __class__.__state = 'CONNECTED'
        self.user_id = user_id
        self.avatar_id = avatar_id
        
        # Subscribe to the root node (ID of this node is always 0)
        self.send_node_subscribe(prio=vrs.DEFAULT_PRIORITY, node_id=0, version=0, crc32=0)
        # Add root node to the dictionary of nodes
        self.nodes[0] = MyNode(node_id=0, parent=None, user_id=0, custom_type=0)

        # TODO: Create tag groups with views to the scene
        
        # Subscribe to the root of scene node
        self.send_node_subscribe(prio=vrs.DEFAULT_PRIORITY, node_id=3, version=0, crc32=0)
 
    
    def _receive_user_authenticate(self, username, methods):
        """
        receive_user_authenticate(username, methods) -> None
        Callback function for user authenticate
        """
        print('receive_user_authenticate()', username, methods)
        if username == '':
            bpy.ops.scene.verse_auth_dialog_operator('INVOKE_DEFAULT')
        else:
            if username == self.my_username:
                self.send_user_authenticate(self.my_username, vrs.UA_METHOD_PASSWORD, self.my_password)
    
    def send_connect_terminate(self):
        """
        send_connect_terminate() -> None
        
        """
        __class__.__state = 'DISCONNECTING'
        vrs.Session.send_connect_terminate(self)


# Class with timer modal operator running callback_update
class ModalTimerOperator(bpy.types.Operator):
    """Operator which runs its self from a timer"""
    bl_idname = "wm.modal_timer_operator"
    bl_label = "Modal Timer Operator"

    _timer = None

    def modal(self, context, event):
        if event.type == 'TIMER':
            vrs_session = VerseSession.instance()
            if vrs_session is not None:
                try:
                    vrs_session.callback_update()
                except vrs.VerseError:
                    del vrs_session
                    return {'CANCELLED'}
        return {'PASS_THROUGH'}

    def execute(self, context):
        self._timer = context.window_manager.event_timer_add(0.1, context.window)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        context.window_manager.event_timer_remove(self._timer)
        return {'CANCELLED'}


# List of Blender classes in this submodule
classes = (
    ModalTimerOperator,
)


def register():
    """
    This method register all methods of this submodule
    """

    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    """
    This method unregister all methods of this submodule
    """

    for c in classes:
        bpy.utils.unregister_class(c)
