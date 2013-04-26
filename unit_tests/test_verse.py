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

class TestNewNodeCase(unittest.TestCase):
    """
    Test case of TestNode
    """

    node = None

    @classmethod
    def setUpClass(cls):
        """
        This method is called before any test is performed
        """
        __class__.node = model.MyNode(node_id=None, parent=None, user_id=None, custom_type=16)

    def test_node_not_created(self):
        """
        Test of creating new node
        """      
        self.assertEqual(__class__.node.created, False)

    def test_node_not_subscribed(self):
        """
        Test of creating new node
        """      
        self.assertEqual(__class__.node.subscribed, False)

    @classmethod
    def tearDownClass(cls):
        """
        This method is called, when all method has been performed
        """
        model.session.send_connect_terminate()

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
        self.user_id = user_id
        self.avatar_id = avatar_id
        # Subscribe to node of avatar
        self.send_node_subscribe(prio=vrs.DEFAULT_PRIORITY, node_id=0, version=0)
        # Create root node
        model.MyNode(0, None, 100, 0)
        self.state = 'CONNECTED'

    def _receive_node_create(self, node_id, parent_id, user_id, custom_type):
        """Custom callback method that is called, when client received"""
        """command node_create"""
        super(MySession, self)._receive_node_create(node_id, parent_id, user_id, custom_type)
        model.MyNode._receive_node_create(node_id, parent_id, user_id, type)
        if node_id == self.avatar_id:
            # Start unitesting, when avatar node is created
            print("avatar_id: ", self.avatar_id)
            suite = unittest.TestLoader().loadTestsFromTestCase(TestNewNodeCase)
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
        print('.')
        time.sleep(0.05)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--hostname', nargs='?', default='localhost', help='Hostname of Verse server')
    parser.add_argument('--username', nargs='?', default=None, help='Username')
    parser.add_argument('--password', nargs='?', default=None, help='Password')
    args = parser.parse_args()
    main(args.hostname, args.username, args.password)
