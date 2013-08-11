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
    imp.reload(vrsent)
    imp.reload(avatar_view)
else:
    import bpy
    import verse as vrs
    from .vrsent import vrsent
    from .avatar_view import AvatarView


# VerseSession class
class VerseSession(vrsent.VerseSession):
    """
    Class Session for this Python client
    """
        
    # Blender could be connected only to one Verse server
    __instance = None
    
 
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
        __class__.__instance = self
        self.debug_print = True


    def __del__(self):
        """
        __del__() -> None
        """
        __class__.__instance = None


    def _receive_connect_terminate(self, error):
        """
        receive_connect_terminate(error) -> none
        """
        # Call parent method to print debug information
        super(VerseSession, self)._receive_connect_terminate(error)
        __class__.__instance = None
        # Clear dictionary of nodes
        self.nodes.clear()
        # TODO: stop timer, disable view3d.verse_avatar() operator
  
    
    def _receive_connect_accept(self, user_id, avatar_id):
        """
        _receive_connect_accept(self, user_id, avatar_id) -> None
        """
        super(VerseSession, self)._receive_connect_accept(user_id, avatar_id)

        # Create avatar node with representation of current view to the scene
        avatar_node = AvatarView(my_view=True, session=self, node_id=avatar_id)

        # TODO: Automaticaly start capturing of curent view to 3D View
        #bpy.ops.view3d.verse_avatar()

        # TODO: Popup dialog to choose scene at Verse server
        # (subscribe to parent of scene nodes)
 
    
    def _receive_user_authenticate(self, username, methods):
        """
        _receive_user_authenticate(self, username, methods) -> None
        """
        if username == '':
            bpy.ops.scene.verse_auth_dialog_operator('INVOKE_DEFAULT')
        else:
            if username == self.my_username:
                self.send_user_authenticate(self.my_username, vrs.UA_METHOD_PASSWORD, self.my_password)
    

    def _receive_node_create(self, node_id, parent_id, user_id, custom_type):
        """
        _receive_node_create(self, node_id, parent_id, user_id, type) -> None
        """
        # Is parent node parent of avatar nodes and it is not avatar node of
        # this client
        if parent_id == 1:
            if node_id != self.avatar_id:
                avatar_node = AvatarView(my_view=False,
                    session=self,
                    node_id=node_id,
                    parent_id=parent_id,
                    user_id=user_id,
                    custom_type=custom_type)
        else:
            # Call parent method to print debug information
            node = super(VerseSession, self)._receive_node_create(node_id, parent_id, user_id, custom_type)    
    
    def _receive_node_destroy(self, node_id):
        """
        _receive_node_destroy(self, node_id) -> None
        """
        # Call parent method to print debug information
        node = super(VerseSession, self)._receive_node_destroy(node_id)

    
    def _receive_node_link(self, parent_node_id, child_node_id):
        """
         _receive_node_link(self, parent_node_id, child_node_id) -> None
        """
        # Call parent method to print debug information
        child_node = super(VerseSession, self)._receive_node_link(parent_node_id, child_node_id)


    def _receive_node_perm(self, node_id, user_id, perm):
        """
        _receive_node_perm(self, node_id, user_id, perm) -> None
        """
        # Call parent method to print debug information
        node = super(VerseSession, self)._receive_node_perm(node_id, user_id, perm)


    def _receive_taggroup_create(self, node_id, taggroup_id, custom_type):
        """
        _receive_taggroup_create(self, node_id, taggroup_id, custom_type) -> None
        """
        # Call parent method to print debug information
        tg = super(VerseSession, self)._receive_taggroup_create(node_id, taggroup_id, custom_type)

        # Try to find node representing avatar
        avatar_node = AvatarView.other_views().get(node_id)
        if avatar_node is not None and avatar_node.my_view == False and custom_type == 321:
            avatar_node.view_tg = tg


    def _receive_taggroup_destroy(self, node_id, taggroup_id):
        """
        _receive_taggroup_destroy(self, node_id, taggroup_id) -> None
        """
        # Call parent method to print debug information
        tg = super(VerseSession, self)._receive_taggroup_destroy(node_id, taggroup_id)


    def _receive_tag_create(self, node_id, taggroup_id, tag_id, data_type, count, custom_type):
        """
        _receive_tag_create(self, node_id, taggroup_id, tag_id, data_type, count, custom_type) -> None
        """
        # Call parent method to print debug information
        tag = super(VerseSession, self)._receive_tag_create(node_id, taggroup_id, tag_id, data_type, count, custom_type)
        # Try to get node and tg representing view of avatar to 3D view
        avatar_node = AvatarView.other_views().get(node_id)
        if avatar_node is not None and avatar_node.my_view == False and tag.tg.custom_type == 321:
            # TODO: assign tag to avatar view node
            pass


    def _receive_tag_destroy(self, node_id, taggroup_id, tag_id):
        """
        _receive_tag_destroy(self, node_id, taggroup_id, tag_id) -> None
        """
        # Call parent method to print debug information
        tag = super(VerseSession, self)._receive_tag_destroy(node_id, taggroup_id, tag_id)


    def _receive_tag_set_values(self, node_id, taggroup_id, tag_id, value):
        """
        Custom callback method that is called, when client reveived command tag set value
        """
        # Call parent method to print debug information and get modified tag
        tag = super(VerseSession, self)._receive_tag_set_values(node_id, taggroup_id, tag_id, value)
        # TODO: try to get node and tg representing view of avatar to 3D view


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
