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

class MySession(vrs.Session):
    def _receive_user_authenticate(self, username, methods):
        """Callback function for user authenticate"""
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
        """Custom callback function for connect accept"""
        # Subscribe to node that is root of node tree
        self.send_node_subscribe(prio=vrs.DEFAULT_PRIORITY, node_id=0, version=0)

    def _receive_node_create(self, node_id, parent_id, user_id, type):
        """Custom callback function that is called, when client received"""
        """command node_create"""
        self.send_node_subscribe(vrs.DEFAULT_PRIORITY, node_id, 0)

def main(hostname, username, password):
    """
    Function with main never ending verse loop
    """
    session = MySession(hostname, "12345", vrs.DGRAM_SEC_DTLS)
    session.username = username
    session.password = password

    while(True):
        session.callback_update()
        time.sleep(1)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--hostname', nargs='?', default='localhost', help='Hostname of Verse server')
    parser.add_argument('--username', nargs='?', default=None, help='Username')
    parser.add_argument('--password', nargs='?', default=None, help='Password')
    args = parser.parse_args()
    main(args.hostname, args.username, args.password)