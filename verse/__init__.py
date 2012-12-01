bl_info = {
    "name": "Verse Client",
    "author": "Jiri Hnidek",
    "version": (0, 1),
    "blender": (2, 6, 4),
    "location": "File > Verse",
    "description": "Adds integration of Verse protocol",
    "warning": "Alpha quality, Works only at Linux OS, Requires verse module",
    "wiki_url": "",
    "tracker_url": "",
    "category": "System"}


import bpy
import verse as vrs


# VerseNode class
class MyNode():
    def __init__(self, node_id, parent, user_id, type):
        self.id = node_id
        self.parent = parent
        self.user_id = user_id
        self.type = type
        self.taggroups = {}
        self.layers = {}


# VerseSession class
class VerseSession(vrs.Session):
    '''Class Session for this Python client'''
    
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
        vrs.Session.__init__(self, hostname, service, flag)
        __class__.__state = 'CONNECTING'
        __class__.__instance = self
        self.fps = 60 # TODO: get current FPS
        # Create empty dictionary of nodes
        self.nodes = {}
        self.my_username = ''
        self.my_password = ''

    
    def _receive_node_create(self, node_id, parent_id, user_id, type):
        """
        receive_node_create(node_id, parent_id, user_id, type) -> None
        """
        print('receive_node_create()', node_id, parent_id, user_id, type)
        # Automatically subscribe to all nodes
        self.send_node_subscribe(vrs.DEFAULT_PRIORITY, node_id, 0)
        # Try to find parent node
        try:
            parent_node = self.nodes[parent_id]
        except KeyError:
            parent_node = None
        # Add node to the dictionary of nodes
        self.nodes[node_id] = MyNode(node_id, parent_node, user_id, type)
        
        if node_id == self.avatar_id :
            # Create TagGroup in Avatar node representing current view to the 3d View
            self.send_taggroup_create(prio=vrs.DEFAULT_PRIORITY, node_id=self.avatar_id, custom_type=53)
        
    
    def _receive_node_destroy(self, node_id):
        """
        receive_node_destroy(node_id) -> None
        """
        print('receive_node_destroy()', node_id)
        # Try to remove node from dictionary of nodes
        try:
            self.nodes.pop(node_id)
        except KeyError:
            pass
        
    
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
        self.nodes.clear()
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
        self.send_node_subscribe(prio=vrs.DEFAULT_PRIORITY, node_id=0, version=0)
        # Add root node to the dictionary of nodes
        self.nodes[0] = MyNode(0, None, 0, 0)
        
        # Create new empty scene
        bpy.ops.scene.new(type='EMPTY')
        # Name scene
        self.scene = bpy.context.scene
        self.scene.name = self.hostname
 
    
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


# Class for reporting errors
class VerseError(bpy.types.Operator):
    """Operator that is used for reporting Verse errors"""
    bl_idname = "wm.verse_error"
    bl_label = "Verse Error"
    
    error_string = bpy.props.StringProperty(name="Error")
    
    def execute(self, context):
        # TODO: display popup, report doesn't work :-(
        self.report({'ERROR'}, "%s" % (self.error_string))
    
    def invoke(self, context, event):
        self.execute(context)    
        return {'FINISHED'}


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
                vrs_session.callback_update()
        return {'PASS_THROUGH'}

    def execute(self, context):
        self._timer = context.window_manager.event_timer_add(0.1, context.window)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        context.window_manager.event_timer_remove(self._timer)
        return {'CANCELLED'}


# Class for displaying Login dialog
class VerseAuthDialogOperator(bpy.types.Operator):
    '''User Authenticate dialog'''
    bl_idname = "scene.verse_auth_dialog_operator" 
    bl_label = "User Authenticate dialog" 

    dialog_username = bpy.props.StringProperty(name="Username")
    dialog_password = bpy.props.StringProperty(name="Password", subtype='PASSWORD')

    def __init__(self):
        pass

    def execute(self, context):
        vrs_session = VerseSession.instance()
        if(vrs_session is not None):
            vrs_session.my_username = self.dialog_username
            vrs_session.my_password = self.dialog_password
            vrs_session.send_user_authenticate(self.dialog_username, vrs.UA_METHOD_NONE, "")
        return {'FINISHED'} 

    def invoke(self, context, event): 
        wm = context.window_manager 
        return wm.invoke_props_dialog(self)


# Class for own connecting to Verse server and displaying Connect dialog
class VerseConnectDialogOperator(bpy.types.Operator):
    '''Connect dialog'''
    bl_idname = "scene.verse_connect_dialog_operator" 
    bl_label = "Connect dialog" 

    vrs_server_name = bpy.props.StringProperty(name="Verse Server")

    def execute(self, context):
        VerseSession(self.vrs_server_name, "12345", 0)
        # Start timer
        bpy.ops.wm.modal_timer_operator()
        self.report({'INFO'}, "Connecting to: '%s'" % (self.vrs_server_name))
        return {'FINISHED'} 

    def invoke(self, context, event): 
        wm = context.window_manager 
        return wm.invoke_props_dialog(self)


# Class for disconnecting from Verse server
class VerseClientDisconnect(bpy.types.Operator):
    '''This class will try to disconnect Blender from Verse server'''
    bl_idname = "scene.verse_client_disconnect"
    bl_label = "Disconnect"
    bl_description = "Disconnect from Verse server"
    
    @classmethod
    def poll(cls, context): # NOT sure about this
        if VerseSession.state() == 'CONNECTING' or VerseSession.state() == 'CONNECTED':
            return True
        else:
            return False
    
    def execute(self, context):
        vrs_session = VerseSession.instance()
        vrs_session.send_connect_terminate()
        return {'FINISHED'}


# Class that tries to connect to Verse server
class VerseClientConnect(bpy.types.Operator):
    '''This class will try to connect Blender to Verse server'''
    bl_idname = "scene.verse_client_connect" # NOT sure about this
    bl_label = "Connect ..."
    bl_description = "Connect to Verse server"

    @classmethod    
    def poll(cls, context):
        if VerseSession.state() == 'DISCONNECTED':
            return True
        else:
            return False
    
    def execute(self, context):
        bpy.ops.scene.verse_connect_dialog_operator('INVOKE_DEFAULT', vrs_server_name = 'localhost')
        return {'FINISHED'}
        

# Class for drawing Verse submenu
class VerseMenu(bpy.types.Menu):
    '''Main Verse menu'''
    bl_label = "Verse Menu"
    bl_idname = "INFO_MT_verse" # NOT sure about this

    def draw(self, context):
        layout = self.layout

        layout.operator("scene.verse_client_connect")
        layout.operator("scene.verse_client_disconnect")


# Verse submenu
def draw_item(self, context):
    layout = self.layout
    layout.menu(VerseMenu.bl_idname)


# List of Blender classes
classes = (
    ModalTimerOperator,
    VerseAuthDialogOperator,
    VerseConnectDialogOperator,
    VerseClientConnect,
    VerseClientDisconnect,
    VerseMenu,
    VerseError
)


def register():
    # Register all classes listed in the tuple classes
    for c in classes:
        bpy.utils.register_class(c)

    # Adds Verse submenu to the File menu
    bpy.types.INFO_MT_file.append(draw_item)



def unregister():
    # Unregister all classes listed in the tuple classes
    for c in classes:
        bpy.utils.unregister_class(c)
    # Removes verse submenu from File menu
    bpy.types.INFO_MT_file.remove(draw_item)


if __name__ == "__main__":
    register()
