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
import time

class TestNode(unittest.TestCase):
    """
    Test case of TestNode
    """

    def test_create_node(self):
        """
        Test of creating new node
        """
        node = model.MyNode(node_id=None, parent=None, user_id=None, custom_type=16)
        time.sleep(0.2)
        self.assertEqual(node.created, True)

    def tearDown(self):
        model.session.send_connect_terminate()

class MySession(vrs.Session):
    """
    Class with session used in this client
    """

    def _receive_user_authenticate(self, username, methods):
        """
        Callback function for user authenticate
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
        Custom callback function for connect accept
        """
        self.user_id = user_id
        self.avatar_id = avatar_id
        # Subscribe to node of avatar
        self.send_node_subscribe(prio=vrs.DEFAULT_PRIORITY, node_id=0, version=0)
        # Create root node
        model.MyNode(0, None, 100, 0)
        self.state = "CONNECTED"

    def _receive_node_create(self, node_id, parent_id, user_id, type):
        """Custom callback function that is called, when client received"""
        """command node_create"""
        model.MyNode.node_created(node_id, parent_id, user_id, type)
        if node_id == self.avatar_id:
            # Start unitesting, when avatar node is created
            #unittest.main()
            print("avatar_id: ", self.avatar_id)
            test_node = TestNode()
            test_node.run()

    def _recive_connect_terminate(self, error):
        """
        """
        self.state = "DISCONNECTED"

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
