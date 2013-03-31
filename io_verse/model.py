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


class MyLayer():
    """
    Class representing Verse layer
    """

    def __init__(self):
        """
        Constructor of MyLayer
        """
        pass

# VerseTag class
class MyTag():
    """
    Class representing Verse tag
    """
    
    def __init__(self, tg, tag_id, custom_type, data_type):
        """
        Constructor of MyTag
        """
        self.tg = tg
        self.id = tag_id
        self.custom_type = custom_type
        self.data_type = data_type
   
    def set_value(self, value):
        """
        Setter of tag value
        """
        self.value = value


# VerseTagGroup class
class MyTagGroup():
    """
    Class representing Verse tag group
    """

    def __init__(self, node, tg_id, custom_type):
        """
        Constructor of MyTagGroup
        """
        self.id = tg_id
        self.node = node
        self.custom_type = custom_type
        self.tags = {}


# VerseNode class
class MyNode():
    """
    Class representing Verse node
    """
    
    def __init__(self, node_id, parent, user_id, custom_type):
        """
        Constructor of MyNode
        """
        self.id = node_id
        self.parent = parent
        self.user_id = user_id
        self.custom_type = custom_type
        self.taggroups = {}
        self.layers = {}
