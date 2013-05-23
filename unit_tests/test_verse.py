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
Module for testing verse module and verse model
"""

import unittest
import model
import verse as vrs
import time


class TestChangedTagCase(unittest.TestCase):
    """
    Test case of created VerseTag
    """

    node = None
    tg = None
    tag = None

    @classmethod
    def setUpClass(cls):
        """
        This method is called before any test is performed
        """
        __class__.node = model.session.test_node
        __class__.tg = model.session.test_node.test_tg
        __class__.tag = model.session.test_node.test_tg.test_tag

    def test_tag_value(self):
        """
        Test of state of created tag
        """      
        self.assertEqual(__class__.tag.value, (123,))

    @classmethod
    def tearDownClass(cls):
        """
        This method is called, when all method has been performed
        """
        model.session.send_connect_terminate()


class TestCreatedTagCase(unittest.TestCase):
    """
    Test case of created VerseTag
    """

    node = None
    tg = None
    tag = None

    @classmethod
    def setUpClass(cls):
        """
        This method is called before any test is performed
        """
        __class__.node = model.session.test_node
        __class__.tg = model.session.test_node.test_tg
        __class__.tag = model.session.test_node.test_tg.test_tag

    def test_tag_created(self):
        """
        Test of state of created tag
        """      
        self.assertEqual(__class__.tag.state, model.ENTITY_CREATED)


class TestNewTagCase(unittest.TestCase):
    """
    Test case of new VerseTag
    """

    node = None
    tg = None
    tag = None

    @classmethod
    def setUpClass(cls):
        """
        This method is called before any test is performed
        """
        __class__.node = model.session.test_node
        __class__.tg = model.session.test_node.test_tg
        __class__.tag = model.session.test_node.test_tg.test_tag

    def test_tag_not_created(self):
        """
        Test of state of created tag
        """      
        self.assertEqual(__class__.tag.state, model.ENTITY_CREATING)


class TestCreatedTagGroupCase(unittest.TestCase):
    """
    Test case of VerseTagGroup
    """

    node = None
    tg = None

    @classmethod
    def setUpClass(cls):
        """
        This method is called before any test is performed
        """
        __class__.node = model.session.test_node
        __class__.tg = model.session.test_node.test_tg

    def test_tg_created(self):
        """
        Test of state of created tag group
        """      
        self.assertEqual(__class__.tg.state, model.ENTITY_CREATED)

    def test_tg_id(self):
        """
        Test of tag group ID
        """      
        self.assertIsNotNone(__class__.tg.id)

    def test_tg_subscribed(self):
        """
        Test of subscription of created tag group
        """      
        self.assertEqual(__class__.tg.subscribed, True)


class TestNewTagGroupCase(unittest.TestCase):
    """
    Test case of VerseTagGroup
    """

    node = None
    tg = None

    @classmethod
    def setUpClass(cls):
        """
        This method is called before any test is performed
        """
        __class__.node = model.session.test_node
        __class__.tg = model.session.test_node.test_tg

    def test_tg_not_created(self):
        """
        Test of creating new tag group
        """      
        self.assertEqual(__class__.tg.state, model.ENTITY_CREATING)

    def test_tg_not_subscribed(self):
        """
        Test of subscription of new tag group
        """      
        self.assertEqual(__class__.tg.subscribed, False)


class TestLinkNodeCase(unittest.TestCase):
    """
    Test case of VerseNode with changed link to parent node
    """

    child_node = None
    parent_node = None

    @classmethod
    def setUpClass(cls):
        """
        This method is called before any test is performed
        """
        __class__.child_node = model.session.test_node
        __class__.parent_node = model.session.test_scene_node
        __class__.avatar_node = model.session.avatar_node

    def test_child_node_link(self):
        """
        Test of node with changed link to parent node
        """      
        self.assertEqual(__class__.child_node.parent, __class__.parent_node)

    def test_parent_node_link(self):
        """
        Test that new parent node include child node in
        dictionary of child nodes
        """
        self.assertEqual(__class__.parent_node.child_nodes[__class__.child_node.id], __class__.child_node)

    def test_avatar_child_nodes(self):
        """
        Test that original parent node (avatar node) does not include
        reference at node anymore
        """
        try:
            node = __class__.avatar_node.child_nodes[__class__.child_node.id]
        except KeyError:
            node = None
        self.assertIsNone(node)


class TestCreatedNodeCase(unittest.TestCase):
    """
    Test case of created VerseNode
    """

    node = None

    @classmethod
    def setUpClass(cls):
        """
        This method is called before any test is performed
        """
        __class__.node = model.session.test_node

    def test_node_created(self):
        """
        Test of creating new node
        """      
        self.assertEqual(__class__.node.state, model.ENTITY_CREATED)

    def test_node_id(self):
        """
        Test of node ID
        """      
        self.assertIsNotNone(__class__.node.id)

    def test_node_subscribed(self):
        """
        Test of node subscribtion
        """      
        self.assertEqual(__class__.node.subscribed, True)


class TestNewNodeCase(unittest.TestCase):
    """
    Test case of new VerseNode
    """

    node = None

    @classmethod
    def setUpClass(cls):
        """
        This method is called before any test is performed
        """
        __class__.node = model.session.test_node

    def test_node_not_created(self):
        """
        Test of creating new node
        """      
        self.assertEqual(__class__.node.state, model.ENTITY_CREATING)

    def test_node_not_subscribed(self):
        """
        Test of creating new node
        """      
        self.assertEqual(__class__.node.subscribed, False)


class MySession(vrs.Session):
    """
    Class with session used in this client
    """

    def _receive_user_authenticate(self, username, methods):
        """
        Callback method for user authenticate
        """
        print("MY user_authenticate(): ",
              "username: ", username,
              ", methods: ", methods)
        if username=="":
            if self.username is None:
                self.username = username = input('username: ')
            else:
                username = self.username
            self.send_user_authenticate(username, vrs.UA_METHOD_NONE, "")
        else:
            if methods.count(vrs.UA_METHOD_PASSWORD)>=1:
                if self.password is None:
                    self.password = password = input('password: ')
                else:
                    password = self.password
                self.send_user_authenticate(username, vrs.UA_METHOD_PASSWORD, password)
            else:
                print("Unsuported authenticate method")

    def _receive_connect_accept(self, user_id, avatar_id):
        """
        Custom callback method for connect accept
        """
        # Call parent method to print debug information
        super(MySession, self)._receive_connect_accept(self, user_id, avatar_id)
        # Save important informations
        self.user_id = user_id
        self.avatar_id = avatar_id
        self.test_node = None
        self.test_tg = None
        self.test_tag = None
        # Create root node
        self.root_node = model.VerseNode(node_id=0, parent=None, user_id=100, custom_type=0)
        self.state = 'CONNECTED'

    def _receive_node_create(self, node_id, parent_id, user_id, custom_type):
        """
        Custom callback method that is called, when client received
        command node_create
        """

        # Call parent method to print debug information
        super(MySession, self)._receive_node_create(node_id, parent_id, user_id, custom_type)
        # Call calback method of model
        node = model.VerseNode._receive_node_create(node_id, parent_id, user_id, custom_type)

        # Start unit testing of new node, tag group and tag, when avatar node is created
        if node_id == self.avatar_id:

            # Save reference at avatar node
            self.avatar_node = node

            # Try to find node representing parent node of scene nodes
            try:
                self.scene_node = model.VerseNode.nodes[3]
            except KeyError:
                self.scene_node = model.VerseNode(node_id=3, \
                    parent=self.root_node, \
                    user_id=100,
                    custom_type=0)

            # Create test scene node
            self.test_scene_node = model.VerseNode(node_id=None, \
                parent=self.scene_node, \
                user_id=None,
                custom_type=17)

            # Create new test node
            self.test_node = model.VerseNode(node_id=None, \
                parent=self.test_scene_node, \
                user_id=None, \
                custom_type=16)

            # Create new test tag group
            self.test_node.test_tg = model.VerseTagGroup(node=self.test_node, \
                tg_id=None, \
                custom_type=32)

            # Create new test tag
            self.test_node.test_tg.test_tag = model.VerseTag(tg=self.test_node.test_tg, \
                tag_id=None, \
                data_type=vrs.VALUE_TYPE_UINT8, \
                count=1, \
                custom_type=64)

            # Set value of tag
            self.test_node.test_tg.test_tag.value = (123,)

            # Test new Node
            suite = unittest.TestLoader().loadTestsFromTestCase(TestNewNodeCase)
            unittest.TextTestRunner(verbosity=1).run(suite)

            # Test new TagGroup
            suite = unittest.TestLoader().loadTestsFromTestCase(TestNewTagGroupCase)
            unittest.TextTestRunner(verbosity=1).run(suite)

            # Test new tag
            suite = unittest.TestLoader().loadTestsFromTestCase(TestNewTagCase)
            unittest.TextTestRunner(verbosity=1).run(suite)

        # Start unit testing of created node
        if node == self.test_node:
            suite = unittest.TestLoader().loadTestsFromTestCase(TestCreatedNodeCase)
            unittest.TextTestRunner(verbosity=1).run(suite)


    def _receive_node_link(self, parent_node_id, child_node_id):
        """
        Custom callback method that is called, when client receive command changing
        link between nodes
        """
        # Call parent method to print debug information
        super(MySession, self)._receive_node_link(parent_node_id, child_node_id)
        # Call calback method of model
        child_node = model.VerseNode._receive_node_link(parent_node_id, child_node_id)

        # Start unit testing of node with changed parent
        if child_node == self.test_node:
            suite = unittest.TestLoader().loadTestsFromTestCase(TestLinkNodeCase)
            unittest.TextTestRunner(verbosity=1).run(suite)


    def _receive_taggroup_create(self, node_id, taggroup_id, custom_type):
        """
        Custom callback method that is called, when client received command
        tag group create
        """

        # Call parent method to print debug information
        super(MySession, self)._receive_taggroup_create(node_id, taggroup_id, custom_type)
        # Call calback method of model
        tg = model.VerseTagGroup._receive_tg_create(node_id, taggroup_id, custom_type)

        # Start unit testing of created tag group
        if tg == self.test_node.test_tg:
            suite = unittest.TestLoader().loadTestsFromTestCase(TestCreatedTagGroupCase)
            unittest.TextTestRunner(verbosity=1).run(suite)


    def _receive_tag_create(self, node_id, taggroup_id, tag_id, data_type, count, custom_type):
        """
        Custom callback method that is called, when client receive command tag create
        """

        # Call parent method to print debug information
        super(MySession, self)._receive_tag_create(node_id, taggroup_id, tag_id, data_type, count, custom_type)
        # Call calback method of model
        tag = model.VerseTag._receive_tag_create(node_id, taggroup_id, tag_id, data_type, count, custom_type)

        # Start unit testing of created tag
        if tag == self.test_node.test_tg.test_tag:
            suite = unittest.TestLoader().loadTestsFromTestCase(TestCreatedTagCase)
            unittest.TextTestRunner(verbosity=1).run(suite)

    def _receive_tag_set_value(self, node_id, taggroup_id, tag_id, value):
        """
        Custom callback method that is called, when client reveive command tag set value
        """

        # Call method of parent class
        super(MySession, self)._receive_tag_set_value(node_id, taggroup_id, tag_id, value)
        # Call callback method of model
        tag = model.VerseTag._receive_tag_set_value(node_id, taggroup_id, tag_id, value)

        # Start unit testing of tag with changed value
        if tag == self.test_node.test_tg.test_tag:
            suite = unittest.TestLoader().loadTestsFromTestCase(TestChangedTagCase)
            unittest.TextTestRunner(verbosity=1).run(suite)


    def _receive_connect_terminate(self, error):
        """
        Custom callback method for fake connect terminate command
        """
        self.state = 'DISCONNECTED'

def main(hostname, username, password):
    """
    Function with main never ending verse loop
    """
    model.session = MySession(hostname, "12345", vrs.DGRAM_SEC_DTLS)
    model.session.username = username
    model.session.password = password
    model.session.state = 'CONNECTING'

    while(model.session.state != 'DISCONNECTED'):
        model.session.callback_update()
        time.sleep(0.05)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--hostname', nargs='?', default='localhost', help='Hostname of Verse server')
    parser.add_argument('--username', nargs='?', default=None, help='Username')
    parser.add_argument('--password', nargs='?', default=None, help='Password')
    args = parser.parse_args()
    main(args.hostname, args.username, args.password)