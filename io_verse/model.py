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


import verse as vrs


session = None


class MyCustomTypeError(Exception):
    """
    Exception for invalid custom types
    """
    def __init__(self, value):
        """
        Constructor of exception
        """
        self.value = value

    def __str__(self):
        """
        Method for printing content of exception
        """
        return repr(self.value)


class MyLayer():
    """
    Class representing Verse layer
    """

    def __init__(self, node, parent_layer, layer_id, data_type, count, custom_type):
        """
        Constructor of MyLayer
        """
        self.node = node
        self.id = layer_id
        self.data_type = data_type
        self.count = count
        self.custom_type = custom_type
        self.childs = {}
        self.values = {}
        # Set bindings
        if layer_id is not None:
            self.node.layers[layer_id] = self
        else:
            self.node.layer_queue[custom_type] = self
        if parent_layer is not None:
            self.parent_layer = parent_layer
            if layer_id is not None:
                self.parent_layer.childs[layer_id] = self

    def destroy(self):
        """
        Destructor of MyLayer
        """
        # Clear bindings
        self.node.layers.pop(self.id)
        if self.parent_layer is not None:
            self.parent_layer.childs.pop(self.id)


# VerseTag class
class MyTag():
    """
    Class representing Verse tag
    """
    
    def __init__(self, tg, tag_id, data_type, count, custom_type):
        """
        Constructor of MyTag
        """
        self.tg = tg
        self.id = tag_id
        self.custom_type = custom_type
        self.data_type = data_type
        self._value = None

        if tag_id is not None:
            self.tg.tags[tag_id] = self
            self.tg.tag_queue[custom_type] = self
        else:
            tag = None
            try:
                tag = self.tg.tag_queue[custom_type]
            except KeyError:
                self.tg.tag_queue[custom_type] = self
            if tag is not None:
                raise MyCustomTypeError(custom_type)
        if session is not None and tg.id is not None:
            session.send_tag_create(tg.node.prio, tg.node.id, tg.id, data_type, count, custom_type)

    def destroy(self):
        """
        Destructor of MyTag
        """
        if self.id is not None:
            self.tg.tags.pop(self.id)
        self.tg.tag_queue.pop(self.custom_type)
        # Send destroy command to Verse server
        if session is not None and self.id is not None:
            session.send_tag_destroy(self.tg.node.id, self.tg.id, self.id)

    @property
    def value(self):
        """
        The value is property of MyTag
        """
        return self._value

    @value.setter
    def value(self, val):
        """
        The setter of value
        """
        self._value = val
        # Send value to Verse server
        if session is not None and self.id is not None:
            session.send_tag_(self.tg.node.id, self.tg.id, self.id)

    @value.deleter
    def value(self):
        """
        The deleter of value
        """
        del self._value
        # Send destroy command to Verse server
        if session is not None and self.id is not None:
            session.send_tag_destroy(self.tg.node.id, self.tg.id, self.id)


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
        self.tag_queue = {}
        # Set bindings
        if tg_id is not None:
            self.node.taggroups[tg_id] = self
            self.node.tg_queue[custom_type] = self
        else:
            tg = None
            try:
                tg = self.node.tg_queue[custom_type]
            except KeyError:
                self.node.tg_queue[custom_type] = self
            if tg is not None:
                raise MyCustomTypeError(custom_type)
        # Send create command to Verse server
        if session is not None and node.id is not None:
            session.send_taggroup_create(node.id, custom_type)


    def __del__(self):
        """
        Destructor of MyTagGroup
        """
        pass


    def destroy(self):
        """
        Method for destroying tag group
        """
        if self.id is not None:
            self.node.taggroups.pop(self.id)
        self.node.tg_queue.pop(self.custom_type)
        # Send destroy command to Verse server
        if session is not None and self.id is not None:
            session.send_taggroup_destroy(node.prio, node.id, self.id)

    @staticmethod
    def tg_created(node_id, tg_id, custom_type):
        """
        Static method of class that add reference to the
        the dictionary of tag groups and send pending tag_create
        commands
        """
        node = None
        try:
            node = MyNode.nodes[node_id]
        except KeyError:
            return
        try:
            tg = node.tg_queue[custom_type]
        except KeyError:
            return
        node.taggroups[tg_id] = tg
        # Subscribe to tag group
        session.send_taggroup_subscribe(node.prio, node_id, tg_id, 0, 0)
        # Send tag_create commands for pending tags
        for custom_type, tag in tg.tag_queue.items():
            session.send_tag_create(node.prio, node.id, tg.id, tag.data_typ, tag.count, custom_type)


# VerseNode class
class MyNode():
    """
    Class representing Verse node
    """

    nodes = {}
    my_node_queues = {}
    
    def __init__(self, node_id, parent, user_id, custom_type):
        """
        Constructor of MyNode
        """
        self.id = node_id
        self.parent = parent
        self.user_id = user_id
        self.custom_type = custom_type
        self.child_nodes = {}
        self.taggroups = {}
        self.tg_queue = {}
        self.layers = {}
        self.layer_queue = {}
        self.prio = vrs.DEFAULT_PRIORITY

        # When node_id is not set, then:
        if node_id is None:
            # Send node_create command to the server
            if session is not None:
                session.send_node_create(self.prio, custom_type)
            # Try to find queue of custom_type of node or create new one
            try:
                node_queue = __class__.my_node_queues[custom_type]
            except KeyError:
                node_queue = []
                __class__.my_node_queues[custom_type] = node_queue
            # Add this object to the queue
            node_queue.insert(0, self)
        else:
            __class__.nodes[node_id] = self
            if self.parent is not None:
                self.parent.child_nodes[node_id] = self


    def __del__(self):
        """
        Destructor of MyNode
        """
        pass


    def destroy(self):
        """
        This method destroy node 
        """
        # Delete all child nodes
        for node in self.child_nodes.values():
            node.parent = None
            node.destroy()
        self.child_nodes.clear()
        if self.id is not None:
            # Send destroy command to verse server
            if session is not None:
                session.send_node_destroy(self.prio, self.id)
            # Remove this node from dict of child nodes
            __class__.nodes.pop(self.id)
            # Remove node from dictionar of nodes in class
            if self.parent is not None:
                self.parent.child_nodes.pop(self.id)


    @staticmethod
    def node_created(node_id, custom_type):
        """
        Static method of class that move object from queue to
        the dictionary of nodes and send pending commands
        """
        node_queue = None
        try:
            node_queue = __class__.my_node_queues[custom_type]
        except KeyError:
            return
        node = node_queue.popitem()
        __class__.nodes[node_id] = node
        session.send_node_subscribe()
        # Send tag group create for pending tag groups
        for custom_type in node.tg_queue.keys():
            session.send_taggroup_create(node.prio, node.id, custom_type)
        # TODO: send node_prioroty, node_link, node_subscribe, layer_create
