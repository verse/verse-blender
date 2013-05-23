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

import unittest
import model
import verse as vrs

class TestTag(unittest.TestCase):
    """
    Test case of tag
    """

    def seUp(self):
        """
        Execute before each test (clear dictionary of nodes)
        """
        model.VerseNode.nodes = {}
        model.VerseNode.my_node_queues = {}


    def test_create_new_tag(self):
        """
        Test of creating new tag
        """
        node = model.VerseNode(node_id=65536, parent=None, user_id=None, custom_type=16)
        tg = model.VerseTagGroup(node=node, tg_id=None, custom_type=32)
        tag = model.VerseTag(tg=tg, tag_id=None, data_type=vrs.VALUE_TYPE_UINT8, count=1, custom_type=5)
        self.assertEqual(tag, tg.tag_queue[5])
 

    def test_exception_tag(self):
        """
        Test of raising exception, when client wants to create two tags
        with the same custom type inside the same tag group
        """
        node = model.VerseNode(node_id=65536, parent=None, user_id=None, custom_type=16)
        tg = model.VerseTagGroup(node=node, tg_id=None, custom_type=32)
        tag = model.VerseTag(tg=tg, tag_id=None, data_type=vrs.VALUE_TYPE_UINT8, count=1, custom_type=5)
        self.assertRaises(model.VerseCustomTypeError, model.VerseTag, tg, None, vrs.VALUE_TYPE_UINT8, 1, 5)


    def test_destroy_tag(self):
        """
        Test of destroying of tag
        """
        node = model.VerseNode(node_id=65536, parent=None, user_id=None, custom_type=16)
        tg = model.VerseTagGroup(node=node, tg_id=None, custom_type=32)
        tag = model.VerseTag(tg=tg, tag_id=None, data_type=vrs.VALUE_TYPE_UINT8, count=1, custom_type=5)
        tag.destroy()
        self.assertEqual(len(tg.tags), 0)
        self.assertEqual(len(tg.tag_queue), 0)


    def test_setter_getter_tag(self):
        """
        Test of creating new tag
        """
        node = model.VerseNode(node_id=65536, parent=None, user_id=None, custom_type=16)
        tg = model.VerseTagGroup(node=node, tg_id=None, custom_type=32)
        tag = model.VerseTag(tg=tg, tag_id=None, data_type=vrs.VALUE_TYPE_UINT8, count=1, custom_type=5)
        tag.value = 5
        self.assertEqual(tag.value, 5)


class TestTagGroup(unittest.TestCase):
    """
    Test case of tag group
    """

    def setUp(self):
        """
        Execute before each test (clear dictionary of nodes)
        """
        model.VerseNode.nodes = {}
        model.VerseNode.my_node_queues = {}


    def test_create_new_taggroup(self):
        """
        Test of creating new tag group
        """
        node = model.VerseNode(node_id=65536, parent=None, user_id=None, custom_type=16)
        tg = model.VerseTagGroup(node=node, tg_id=None, custom_type=32)
        self.assertEqual(tg, node.tg_queue[32])


    def test_exception_taggroup(self):
        """
        Test of raising exception, when client wants to create two
        tag groups with the same custom type
        """
        node = model.VerseNode(node_id=65536, parent=None, user_id=None, custom_type=16)
        tg = model.VerseTagGroup(node=node, tg_id=None, custom_type=32)
        self.assertRaises(model.VerseCustomTypeError, model.VerseTagGroup, node, None, 32)


    def test_create_taggroup(self):
        """
        Test of creating tag group that was received from verse server (tg ID is known)
        """
        node = model.VerseNode(node_id=65536, parent=None, user_id=None, custom_type=16)
        tg = model.VerseTagGroup(node=node, tg_id=3, custom_type=32)
        self.assertEqual(tg, node.taggroups[3])


    def test_destroy_taggroup(self):
        """
        Test of creating tag group that was received from verse server (tg ID is known)
        """
        node = model.VerseNode(node_id=65536, parent=None, user_id=None, custom_type=16)
        tg = model.VerseTagGroup(node=node, tg_id=3, custom_type=32)
        tg.destroy()
        self.assertEqual(len(node.taggroups), 0)
        self.assertEqual(len(node.tg_queue), 0)


class TestNode(unittest.TestCase):
    """
    Test case of TestNode
    """

    
    def setUp(self):
        """
        Execute before each test (clear dictionary of all nodes)
        """
        model.VerseNode.nodes = {}
        model.VerseNode.my_node_queues = {}


    def test_create_node(self):
        """
        Test of creating new node
        """
        node = model.VerseNode(node_id=None, parent=None, user_id=None, custom_type=16)
        self.assertEqual(node, model.VerseNode.my_node_queues[16][0])


    def test_create_root_node(self):
        """
        Test of creating new root node
        """
        node = model.VerseNode(node_id=0, parent=None, user_id=0, custom_type=0)
        self.assertEqual(node, model.VerseNode.nodes[0])


    def test_create_scene_node(self):
        """
        Test of creating new scene node that is child node of root node
        """
        root_node = model.VerseNode(node_id=0, parent=None, user_id=0, custom_type=0)
        scene_node = model.VerseNode(node_id=1, parent=root_node, user_id=0, custom_type=0)
        self.assertEqual(scene_node, root_node.child_nodes[1])


    def test_destroy_node(self):
        """
        Test of destroying node
        """
        node = model.VerseNode(node_id=None, parent=None, user_id=None, custom_type=16)
        node.destroy()
        self.assertEqual(len(model.VerseNode.nodes), 0)


    def test_destroy_child_node(self):
        """
        Test of destroying child node
        """
        root_node = model.VerseNode(node_id=0, parent=None, user_id=None, custom_type=0)
        scene_node = model.VerseNode(node_id=1, parent=root_node, user_id=0, custom_type=0)
        scene_node.destroy()
        self.assertEqual(len(model.VerseNode.nodes), 1)


    def test_destroy_parent_node(self):
        """
        Test of destroying parent node
        """
        root_node = model.VerseNode(node_id=0, parent=None, user_id=None, custom_type=0)
        scene_node = model.VerseNode(node_id=1, parent=root_node, user_id=0, custom_type=0)
        root_node.destroy()
        self.assertEqual(len(model.VerseNode.nodes), 0)

if __name__ == '__main__':
    unittest.main()