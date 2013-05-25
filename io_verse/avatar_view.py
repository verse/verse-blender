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


#
# This file contain methods and classes for visualization of other
# users connected to Verse server. It visualize their position and
# current view to active 3DView. Other Blender users sharing data at
# Verse server can also see, where you are and what you do.
#


if "bpy" in locals():
    import imp
    imp.reload(model)
    imp.reload(session)
else:
    import bpy
    import bgl
    import mathutils
    import math
    import verse as vrs
    from . import model
    from . import session


def draw_cb(self, context):
    """
    This callback function is called, when view to 3d scene is changed
    """

    # This callback works only for 3D View
    if context.area.type != 'VIEW_3D':
        return
    
    # Try to find avatar's view, when it doesn't exist yet, then create new one
    try:
        avatar_view = self.avatar_views[context.area]
    except KeyError:
        avatar_view = AvatarView()
        self.avatar_views[context.area] = avatar_view
    
    # Update information about avatar's view, when needed
    changed = avatar_view.update(context)
    
    # Test of drawing avatar's view
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D' and area != context.area:
                try:
                    view = self.avatar_views[area]
                except KeyError:
                    continue
                view.draw(context.area, context.region_data, context.space_data)
                if changed is True:
                    area.tag_redraw()


class AvatarView(model.VerseNode):
    """
    Representation of avatar view to 3D View
    """
    
    __active_area = None
    
    def __init__(self):
        """
        Constructor of AvatarView
        """
        self.location = None
        self.rotation = None
        self.distance = None
        self.perspective = None
        self.width = None
        self.height = None
        self.persp = None
        self.lens = None
        self.cur_screen = None
        self.cur_area = None


    def update(self, context):
        """
        This method tries to update members according context
        """
        
        changed = False
        
        self.cur_screen = context.screen
        self.cur_area = context.area
        
        # Location of avatar
        if context.space_data.region_3d.view_location != self.location:
            self.location = mathutils.Vector(context.space_data.region_3d.view_location)
            changed = True
    
        # Rotation around location point
        if context.space_data.region_3d.view_rotation != self.rotation:
            self.rotation = mathutils.Quaternion(context.space_data.region_3d.view_rotation)
            changed = True
    
        # Distance from location point
        if context.space_data.region_3d.view_distance != self.distance:
            self.distance = context.space_data.region_3d.view_distance
            changed = True
        
        # Perspective/Ortho
        if context.space_data.region_3d.view_perspective != self.persp:
            self.persp = context.space_data.region_3d.view_perspective
            changed = True
        
        # Lens
        if context.space_data.lens != self.lens:
            self.lens = context.space_data.lens
            changed = True

        # Was this view to 3D changed
        if changed == True:
            self.__class__.__active_area = context.area
                
        # Width
        if context.area.width != self.width:
            self.width = context.area.width
            changed = True
        
        # Height
        if context.area.height != self.height:
            self.height = context.area.height
            changed = True

        return changed
    
        
    def draw(self, area, region_data, space):
        """
        Draw avatar view in given context
        """
        active = False
        
        if bpy.context.screen == self.cur_screen:
            if self.cur_area == self.__class__.__active_area:
                active = True
                color = (0.0, 0.0, 1.0, 1.0)
            else:
                color = (1.0, 1.0, 0.0, 0.5)
        else:
            color = (1.0, 1.0, 1.0, 0.5)

        alpha = 2.0*math.atan((18.0/2.0)/self.lens)
        dist = 0.5/(math.tan(alpha/2.0))
        height = 1.0
        width = self.width/self.height
                    
        points = {}
        points['border'] = [None, None, None, None]
        points['center'] = [None]
        
        # Points of face
        if active is True:
            points['right_eye'] = [mathutils.Vector((0.25, 0.25, self.distance - dist)), \
                mathutils.Vector((0.3, 0.25, self.distance - dist)), \
                mathutils.Vector((0.3, 0.0, self.distance - dist)), \
                mathutils.Vector((0.25, 0.0, self.distance - dist)), \
                mathutils.Vector((0.25, 0.25, self.distance - dist))]
            points['left_eye'] = [mathutils.Vector((-0.25, 0.25, self.distance - dist)), \
                mathutils.Vector((-0.3, 0.25, self.distance - dist)), \
                mathutils.Vector((-0.3, 0.0, self.distance - dist)), \
                mathutils.Vector((-0.25, 0.0, self.distance - dist)), \
                mathutils.Vector((-0.25, 0.25, self.distance - dist))]
        else:
            points['right_eye'] = [mathutils.Vector((0.1569932997226715, 0.1604899913072586, self.distance - dist)), \
                mathutils.Vector((0.19806477427482605, 0.14419437944889069, self.distance - dist)), \
                mathutils.Vector((0.2499999850988388, 0.13702455163002014, self.distance - dist)), \
                mathutils.Vector((0.30193519592285156, 0.1441943645477295, self.distance - dist)), \
                mathutils.Vector((0.3430066704750061, 0.1604899764060974, self.distance - dist))]
            points['left_eye'] = [mathutils.Vector((-0.1569932997226715, 0.1604899913072586, self.distance - dist)), \
                mathutils.Vector((-0.19806477427482605, 0.14419437944889069, self.distance - dist)), \
                mathutils.Vector((-0.2499999850988388, 0.13702455163002014, self.distance - dist)), \
                mathutils.Vector((-0.30193519592285156, 0.1441943645477295, self.distance - dist)), \
                mathutils.Vector((-0.3430066704750061, 0.1604899764060974, self.distance - dist))]
        
        points['mouth'] = [mathutils.Vector((-0.40912365913391113, -0.11777058243751526, self.distance - dist)), \
            mathutils.Vector((-0.3441678285598755, -0.15873458981513977, self.distance - dist)), \
            mathutils.Vector((-0.2563667893409729, -0.1998385488986969, self.distance - dist)), \
            mathutils.Vector((-0.18191590905189514, -0.22385218739509583, self.distance - dist)), \
            mathutils.Vector((-0.10375960171222687, -0.23957833647727966, self.distance - dist)), \
            mathutils.Vector((0.0, -0.2464955747127533, self.distance - dist)), \
            mathutils.Vector((0.10375960171222687, -0.23957833647727966, self.distance - dist)), \
            mathutils.Vector((0.18191590905189514, -0.22385218739509583, self.distance - dist)), \
            mathutils.Vector((0.2563667893409729, -0.1998385488986969, self.distance - dist)), \
            mathutils.Vector((0.3441678285598755, -0.15873458981513977, self.distance - dist)), \
            mathutils.Vector((0.40912365913391113, -0.11777058243751526, self.distance - dist))]            
                
        # Put border points of camera to basic position
        points['border'][0] = mathutils.Vector((-width/2.0, \
            -0.5, \
            self.distance - dist,
            1.0))
        points['border'][1] = mathutils.Vector((width/2.0, \
            -0.5, \
            self.distance - dist,
            1.0))
        points['border'][2] = mathutils.Vector((width/2.0, \
            0.5, \
            self.distance - dist, \
            1.0))
        points['border'][3] = mathutils.Vector((-width/2.0, \
            0.5, \
            self.distance - dist, \
            1.0))
        
        # Center of view
        points['center'][0] = mathutils.Vector((0.0, \
            0.0, \
            self.distance, \
            1.0))        
        
        # Create transformation (rotation) matrix
        rot_matrix = self.rotation.to_matrix().to_4x4()
        
        # Transform points in all point groups
        for point_group in points.values():
            for index in range(len(point_group)):
                # Rotate points
                point_group[index] = (rot_matrix*point_group[index]).to_3d()
                # Move points
                point_group[index] += self.location
        
        # Get & convert the Perspective Matrix of the current view/region.
        perspMatrix = region_data.perspective_matrix
        tempMat = [perspMatrix[j][i] for i in range(4) for j in range(4)]
        perspBuff = bgl.Buffer(bgl.GL_FLOAT, 16, tempMat)
    
        # Store previous OpenGL settings.
        # Store MatrixMode
        MatrixMode_prev = bgl.Buffer(bgl.GL_INT, [1])
        bgl.glGetIntegerv(bgl.GL_MATRIX_MODE, MatrixMode_prev)
        MatrixMode_prev = MatrixMode_prev[0]
    
        # Store projection matrix
        ProjMatrix_prev = bgl.Buffer(bgl.GL_DOUBLE, [16])
        bgl.glGetFloatv(bgl.GL_PROJECTION_MATRIX, ProjMatrix_prev)
    
        # Store Line width
        lineWidth_prev = bgl.Buffer(bgl.GL_FLOAT, [1])
        bgl.glGetFloatv(bgl.GL_LINE_WIDTH, lineWidth_prev)
        lineWidth_prev = lineWidth_prev[0]
    
        # Store GL_BLEND
        blend_prev = bgl.Buffer(bgl.GL_BYTE, [1])
        bgl.glGetFloatv(bgl.GL_BLEND, blend_prev)
        blend_prev = blend_prev[0]
        
        # Store GL_DEPTH_TEST
        depth_test_prev = bgl.Buffer(bgl.GL_BYTE, [1])
        bgl.glGetFloatv(bgl.GL_DEPTH_TEST, depth_test_prev)
        depth_test_prev = depth_test_prev[0]
            
        # Store GL_LINE_STIPPLE
        line_stipple_prev = bgl.Buffer(bgl.GL_BYTE, [1])
        bgl.glGetFloatv(bgl.GL_LINE_STIPPLE, line_stipple_prev)
        line_stipple_prev = line_stipple_prev[0]
    
        # Store glColor4f
        col_prev = bgl.Buffer(bgl.GL_FLOAT, [4])
        bgl.glGetFloatv(bgl.GL_COLOR, col_prev)
        
        # Prepare for 3D drawing
        bgl.glLoadIdentity()
        bgl.glMatrixMode(bgl.GL_PROJECTION)
        bgl.glLoadMatrixf(perspBuff)
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glEnable(bgl.GL_DEPTH_TEST)
                
        # Draw "Look At" point
        bgl.glLineWidth(1)
        bgl.glBegin(bgl.GL_LINES)
        bgl.glColor4f(color[0], color[1], color[2], color[3])
        
        bgl.glVertex3f(self.location[0]+0.1, \
            self.location[1], \
            self.location[2])
        bgl.glVertex3f(self.location[0]-0.1, \
            self.location[1], \
            self.location[2])
        
        bgl.glVertex3f(self.location[0], \
            self.location[1]+0.1, \
            self.location[2])
        bgl.glVertex3f(self.location[0], \
            self.location[1]-0.1, \
            self.location[2])
        
        bgl.glVertex3f(self.location[0], \
            self.location[1], \
            self.location[2]+0.1)
        bgl.glVertex3f(self.location[0], \
            self.location[1], \
            self.location[2]-0.1)
        
        bgl.glEnd()
        
        border = points['border']
        center = points['center']
        
        # Draw border of camera
        bgl.glBegin(bgl.GL_LINE_STRIP)
        bgl.glVertex3f(border[0][0], border[0][1], border[0][2])
        bgl.glVertex3f(border[1][0], border[1][1], border[1][2])
        bgl.glVertex3f(border[2][0], border[2][1], border[2][2])
        bgl.glVertex3f(border[3][0], border[3][1], border[3][2])
        bgl.glVertex3f(border[0][0], border[0][1], border[0][2])
        bgl.glEnd()
        
        # Draw left eye
        bgl.glBegin(bgl.GL_LINE_STRIP)
        for point in points['left_eye']:
            bgl.glVertex3f(point[0], point[1], point[2])
        bgl.glEnd()

        # Draw right eye
        bgl.glBegin(bgl.GL_LINE_STRIP)
        for point in points['right_eye']:
            bgl.glVertex3f(point[0], point[1], point[2])
        bgl.glEnd()
        
        # Draw mouth
        bgl.glBegin(bgl.GL_LINE_STRIP)
        for point in points['mouth']:
            bgl.glVertex3f(point[0], point[1], point[2])
        bgl.glEnd()
        
        # Draw dashed lines from center of "camera" to border of camera        
        bgl.glEnable(bgl.GL_LINE_STIPPLE)
        bgl.glBegin(bgl.GL_LINES)
        bgl.glVertex3f(border[0][0], border[0][1], border[0][2])
        bgl.glVertex3f(center[0][0], center[0][1], center[0][2])
        bgl.glVertex3f(border[1][0], border[1][1], border[1][2])
        bgl.glVertex3f(center[0][0], center[0][1], center[0][2])
        bgl.glVertex3f(border[2][0], border[2][1], border[2][2])
        bgl.glVertex3f(center[0][0], center[0][1], center[0][2])
        bgl.glVertex3f(border[3][0], border[3][1], border[3][2])
        bgl.glVertex3f(center[0][0], center[0][1], center[0][2])
        bgl.glEnd()
        
        # Draw dashed line from Look At point and center of camera
        bgl.glBegin(bgl.GL_LINES)
        bgl.glVertex3f(self.location[0], \
            self.location[1], \
            self.location[2])
        bgl.glVertex3f(center[0][0], center[0][1], center[0][2])
        bgl.glEnd()
        bgl.glDisable(bgl.GL_LINE_STIPPLE)
    
        # Restore previous OpenGL settings
        bgl.glLoadIdentity()
        bgl.glMatrixMode(MatrixMode_prev)
        bgl.glLoadMatrixf(ProjMatrix_prev)
        bgl.glLineWidth(lineWidth_prev)
        if not blend_prev:
            bgl.glDisable(bgl.GL_BLEND)
        if not line_stipple_prev:
            bgl.glDisable(bgl.GL_LINE_STIPPLE)
        if not depth_test_prev:
            bgl.glDisable(bgl.GL_DEPTH_TEST)
        bgl.glColor4f(col_prev[0], col_prev[1], col_prev[2], col_prev[3])


class VerseAvatarStatus(bpy.types.Operator):
    """
    Status operator of Verse avatar
    """
    bl_idname = "view3d.verse_avatar"
    bl_label = "Capture"
    bl_description = "Capture camera position"
    last_activity = 'NONE'
    
    _handle = None
    
    def __init__(self):
        """
        Constructor of this operator
        """
        self.avatar_views = {}
    
    def modal(self, context, event):
        """
        This method is executed on events
        """
        return {'PASS_THROUGH'}
    
    def invoke(self, context, event):
        """
        This method is used, when Blender check, if this operator can be
        executed
        """
        if context.area.type == 'VIEW_3D':
            if context.window_manager.verse_avatar_capture is False:
                context.window_manager.verse_avatar_capture = True
                # Register callback function
                VerseAvatarStatus._handle = bpy.types.SpaceView3D.draw_handler_add(draw_cb, (self, context), 'WINDOW', 'POST_PIXEL')
                print('add handle ...', VerseAvatarStatus._handle)
                # Force redraw (display bgl stuff)
                for area in context.screen.areas:
                    if area.type == 'VIEW_3D':
                        area.tag_redraw()
                return {'RUNNING_MODAL'}
            else:
                context.window_manager.verse_avatar_capture = False
                # Unregister callback function
                print('remove handle ...', VerseAvatarStatus._handle)
                bpy.types.SpaceView3D.draw_handler_remove(VerseAvatarStatus._handle, 'WINDOW')
                self._handle = None
                # Force redraw (not display bgl stuff)
                for area in context.screen.areas:
                    if area.type == 'VIEW_3D':
                        area.tag_redraw()
                return {'CANCELLED'}
        else:
            self.report({'WARNING'}, "3D View not found, can't run Camera Capture")
            return {'CANCELLED'}
     
    def cancel(self, context):
        """
        This method is called, when operator is canceled.
        """
        print('cancel()')
        if context.window_manager.verse_avatar_capture is True:
            context.window_manager.verse_avatar_capture = False
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'CANCELLED'}


class VerseShowAvatars(bpy.types.Operator):
    """
    Operator for show/hide other avatars
    """
    bl_idname = "view3d.verse_show_avatars"
    bl_label = "Show Avatars"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def __init__(self):
        """
        Constructor of VerseShowAvatars
        """


class VerseAvatarPanel(bpy.types.Panel):
    """
    Panel with widgets
    """
    bl_idname = "view3d.verse_avatar"
    bl_label = "Verse Avatar"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    
    def draw(self, context):
        """
        Define drawing of widgets
        """
        
        wm = context.window_manager
        layout = self.layout
        layout.operator("view3d.verse_show_avatars")


def init_properties():
    """
    Initialize properties used by this module
    """
    wm = bpy.types.WindowManager
    wm.verse_avatar_capture = bpy.props.BoolProperty(default=False)
    wm.verse_show_avatars = bpy.props.BoolProperty(default=False)


def reset_properties():
    """
    Reset properties used by this module
    """
    wm = bpy.types.WindowManager
    wm.verse_avatar_capture = False
    wm.verse_show_avatars = False


def register():
    """
    Register classes with panel and init properties
    """
    bpy.utils.register_class(VerseAvatarPanel)
    bpy.utils.register_class(VerseAvatarStatus)
    init_properties()


def umregister():
    """
    Unregister classes with panel and reset properties
    """
    bpy.utils.unregister_class(VerseAvatarPanel)
    bpy.utils.unregister_class(VerseAvatarStatus)
    reset_properties()

if __name__ == '__main__':
    register()

