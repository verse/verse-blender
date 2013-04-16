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


class TestTagGroup(unittest.TestCase):
    """
    Test case of tag group
    """

    def test_create_taggroup(self):
        """
        Test of creating new tag group
        """
        node = model.MyNode(node_id=65536, parent=None, user_id=None, custom_type=16)
        tg = model.MyTagGroup(node=node, tg_id=None, custom_type=32)
        self.assertEqual(tg, node.tg_queue[32])

    def test_exception_taggroup(self):
        """
        Test of raising exception, when client wants to create two
        tag groups with the same custom type
        """
        node = model.MyNode(node_id=65536, parent=None, user_id=None, custom_type=16)
        tg = model.MyTagGroup(node=node, tg_id=None, custom_type=32)
        self.assertRaises(model.MyCustomTypeError, model.MyTagGroup, node, None, 32)



class TestNode(unittest.TestCase):
    """
    Test case of TestNode
    """

    
    def setUp(self):
        """
        Execute before each test
        """
        model.MyNode.nodes = {}
        model.MyNode.my_node_queues = {}

    def test_create_node(self):
        """
        Test of creating new node
        """
        node = model.MyNode(node_id=None, parent=None, user_id=None, custom_type=16)
        self.assertEqual(node, model.MyNode.my_node_queues[16][0])


    def test_create_root_node(self):
        """
        Test of creating new root node
        """
        node = model.MyNode(node_id=0, parent=None, user_id=0, custom_type=0)
        self.assertEqual(node, model.MyNode.nodes[0])


    def test_create_scene_node(self):
        """
        Test of creating new scene node that is child node of root node
        """
        root_node = model.MyNode(node_id=0, parent=None, user_id=0, custom_type=0)
        scene_node = model.MyNode(node_id=1, parent=root_node, user_id=0, custom_type=0)
        self.assertEqual(scene_node, root_node.child_nodes[1])


    def test_destroy_node(self):
        """
        Test of destroying node
        """
        node = model.MyNode(node_id=65535, parent=None, user_id=None, custom_type=16)
        node.destroy()
        self.assertEqual(len(model.MyNode.nodes), 0)


    def test_destroy_child_node(self):
        """
        Test of destroying child node
        """
        root_node = model.MyNode(node_id=0, parent=None, user_id=None, custom_type=0)
        scene_node = model.MyNode(node_id=1, parent=root_node, user_id=0, custom_type=0)
        scene_node.destroy()
        self.assertEqual(len(model.MyNode.nodes), 1)


    def test_destroy_parent_node(self):
        """
        Test of destroying parent node
        """
        root_node = model.MyNode(node_id=0, parent=None, user_id=None, custom_type=0)
        scene_node = model.MyNode(node_id=1, parent=root_node, user_id=0, custom_type=0)
        root_node.destroy()
        self.assertEqual(len(model.MyNode.nodes), 0)

if __name__ == '__main__':
    unittest.main()