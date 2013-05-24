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
This module implements object model of data shared at Verse server. it
provides classes for Node, TagGroup, Tag and Layer.
"""

import verse as vrs


session = None

ENTITY_RESERVED     = 0
ENTITY_CREATING     = 1
ENTITY_CREATED      = 2
ENTITY_ASSUMED      = 3
ENTITY_WANT_DESTROY = 4
ENTITY_DESTROYING   = 5
ENTITY_DESTROYED    = 6


class VerseStateError(Exception):
    """
    Exception for invalid state changes
    """

    def __init__(self, state, transition):
        """
        Constructor of exception
        """
        self.state = state
        self.transition = transition

    def __str__(self):
        """
        Method for printing content of exception
        """
        return str(self.state) + '!' + str(self.transition)


class VerseCustomTypeError(Exception):
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


class VerseEntity(object):
    """
    Parent class for VerseNode, Verse, VerseTagGroup and VerseLayer
    """

    def __init__(self, *args, **kwargs):
        """
        Constructor of VerseEntity
        """
        self.id = None
        self.version = 0
        self.crc32 = 0
        self.state = ENTITY_RESERVED
        self.subscribed = False

    def _send_create(self):
        """
        Dummy method
        """
        pass

    def _send_destroy(self):
        """
        Dummy method
        """
        pass

    def _send_subscribe(self):
        """
        Dummy method
        """
        pass

    def _send_unsubscribe(self):
        """
        Dummy method
        """
        pass

    def _create(self):
        """
        This method switch state, when client wants to create new entity
        """
        if self.state == ENTITY_RESERVED:
            if self.id is None:
                self._send_create()
                self.state = ENTITY_CREATING
            else:
                # Skip _send_create(), when ID is known and jump to assumed state
                self.state = ENTITY_ASSUMED
                self._send_subscribe()
        else:
            raise VerseStateError(self.state, "create")

    def _destroy(self):
        """
        This method switch entity state, when client wants to destroy entity
        """
        if self.state == ENTITY_CREATED or self.state == ENTITY_ASSUMED:
            self._send_destroy()
            self.state = ENTITY_DESTROYING
        elif self.state == ENTITY_CREATING:
            self.state = ENTITY_WANT_DESTROY
        else:
            raise VerseStateError(self.state, "destroy")

    def _receive_create(self, *args, **kwargs):
        """
        This method is called when client receive callback function about
        it creating on Verse server
        """
        if self.state == ENTITY_RESERVED or self.state == ENTITY_CREATING:
            self.state = ENTITY_CREATED
            self._send_subscribe()
        elif self.state == ENTITY_ASSUMED:
            self.state = ENTITY_CREATED
        elif self.state == ENTITY_WANT_DESTROY:
            self._send_destroy()
            self.state = ENTITY_DESTROYING
        else:
            raise VerseStateError(self.state, "rcv_create")

    def _receive_destroy(self, *args, **kwargs):
        """
        This method is called when client receive callback function about
        it destroying on Verse server
        """
        if self.state == ENTITY_CREATED:
            self.state = ENTITY_DESTROYED
        elif self.state == ENTITY_DESTROYING:
            self.state = ENTITY_DESTROYED
            self._clean()
        else:
            raise VerseStateError(self.state, "rcv_destroy")

    def _clean(self):
        """
        This method is called, when entity is switched to destroy state
        and it is required to clean all data in this entity
        """
        pass


class VerseLayer():
    """
    Class representing Verse layer
    """

    def __init__(self, node, parent_layer, layer_id, data_type, count, custom_type):
        """
        Constructor of VerseLayer
        """
        super(VerseLayer, self).__init__()
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
        Destructor of VerseLayer
        """
        # Clear bindings
        self.node.layers.pop(self.id)
        if self.parent_layer is not None:
            self.parent_layer.childs.pop(self.id)


# VerseTag class
class VerseTag(VerseEntity):
    """
    Class representing Verse tag
    """
    
    def __init__(self, tg, tag_id, data_type, count, custom_type):
        """
        Constructor of VerseTag
        """
        super(VerseTag, self).__init__()
        self.tg = tg
        self.id = tag_id
        self.data_type = data_type
        self.count = count
        self.custom_type = custom_type
        self._value = None

        self._create()

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
                raise VerseCustomTypeError(custom_type)


    def destroy(self):
        """
        Send destroy command of VerseTag
        """
        # Change state and send destroy command to Verse server
        self._destroy()

    @property
    def value(self):
        """
        The value is property of VerseTag
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
            session.send_tag_set_value(self.tg.node.prio, \
                self.tg.node.id, \
                self.tg.id, \
                self.id, \
                self.data_type, \
                self._value)

    @value.deleter
    def value(self):
        """
        The deleter of value
        """
        # Send destroy command to Verse server
        self._send_destroy()

    def _send_create(self):
        """
        Send tag create command to Verse server
        """
        if session is not None and self.tg.id is not None:
            session.send_tag_create(self.tg.node.prio, \
                self.tg.node.id, \
                self.tg.id, \
                self.data_type, \
                self.count, \
                self.custom_type)

    def _send_destroy(self):
        """
        Send tag group destroy command to Verse server
        """
        if session is not None and self.id is not None:
            session.send_taggroup_destroy(self.node.prio, \
                self.node.id, \
                self.id)

    def _clean(self):
        """
        This method try to clean content (value) of this tag
        """
        # Remove references on this tag from tag group
        if self.id is not None:
            self.tg.tags.pop(self.id)
        self.tg.tag_queue.pop(self.custom_type)
        # Remove value
        del self._value

    @staticmethod
    def _receive_tag_create(node_id, tg_id, tag_id, data_type, count, custom_type):
        """
        Static method of class that should be called when
        coresponding callback function is called
        """
        # Try to find node
        try:
            node = VerseNode.nodes[node_id]
        except KeyError:
            return
        # Try to find tag group
        try:
            tg = node.taggroups[tg_id]
        except KeyError:
            return
        # Was this tag created by this client?
        try:
            tag = tg.tag_queue[custom_type]
            # Add reference to dictionary of tags to tag group
            tg.tags[tag_id] = tag
            tag.id = tag_id
        except KeyError:
            tag = VerseTag(node, tg, tag_id, data_type, count, custom_type)
        # Update state
        tag._receive_create()
        # Send tag value
        tag.value = tag._value
        # Return reference at tag object
        return tag

    @staticmethod
    def _receive_tag_set_value(node_id, tg_id, tag_id, value):
        """
        Static method of class that should be called when
        coresponding callback function is called
        """
        # Try to find node
        try:
            node = VerseNode.nodes[node_id]
        except KeyError:
            return
        # Try to find tag group
        try:
            tg = node.taggroups[tg_id]
        except KeyError:
            return
        # Try to find tag
        try:
            tag = tg.tags[tag_id]
        except KeyError:
            return
        # Set value, but don't send set_value command
        tag._value = value
        # Return reference at this tag
        return tag

    @staticmethod
    def _receive_tag_destroy(node_id, tg_id, tag_id):
        """
        Static method of class that should be called when
        destroy callback session method is called
        """
        # Try to find node
        try:
            node = VerseNode.nodes[node_id]
        except KeyError:
            return
        # Try to find tag group
        try:
            tg = node.taggroups[tg_id]
        except KeyError:
            return
        # Try to find tag
        try:
            tag = tg.tag_queue[custom_type]
        except KeyError:
            return
        # Change state and call clen method
        tag._receive_destroy()
        # Return reference at this destroyed tag
        return tag


# VerseTagGroup class
class VerseTagGroup(VerseEntity):
    """
    Class representing Verse tag group
    """

    def __init__(self, node, tg_id, custom_type):
        """
        Constructor of VerseTagGroup
        """
        super(VerseTagGroup, self).__init__()
        self.id = tg_id
        self.node = node
        self.custom_type = custom_type
        self.tags = {}
        self.tag_queue = {}

        self._create()

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
                raise VerseCustomTypeError(custom_type)

    def _send_create(self):
        """
        Send tag group create command to Verse server
        """
        if session is not None and self.node.id is not None:
            session.send_taggroup_create(self.node.id, custom_type)

    def _send_destroy(self):
        """
        Send tag group destroy command to Verse server
        """
        if session is not None and self.id is not None:
            session.send_taggroup_destroy(self.node.prio, self.node.id, self.id)

    def _send_subscribe(self):
        """
        Send tag group subscribe command
        """
        if session is not None and self.id is not None and self.subscribed == False:
            session.send_taggroup_subscribe(self.node.prio, self.node.id, self.id, self.version, self.crc32)
            self.subscribed = True

    def _clean(self):
        """
        This method clean all data from this tag group
        """
        # Remove references at all this taggroup
        if self.id is not None:
            self.node.taggroups.pop(self.id)
        self.node.tg_queue.pop(self.custom_type)
        # Clean all tags and queue of tags
        self.tags.clear()
        self.tag_queue.clear()

    def destroy(self):
        """
        Method for destroying tag group
        """
        # Change state and send destroy command to Verse server
        self._destroy()

    @staticmethod
    def _receive_tg_create(node_id, tg_id, custom_type):
        """
        Static method of class that add reference to the
        the dictionary of tag groups and send pending tag_create
        commands
        """
        node = None
        try:
            node = VerseNode.nodes[node_id]
        except KeyError:
            return
        # Is it tag group created by this client?
        try:
            tg = node.tg_queue[custom_type]
            tg.id = tg_id
        except KeyError:
            tg = VerseTagGroup(node, tg_id, custom_type)
        node.taggroups[tg_id] = tg
        # Update state and subscribe command
        tg._receive_create()
        # Send tag_create commands for pending tags
        for custom_type, tag in tg.tag_queue.items():
            session.send_tag_create(node.prio, node.id, tg.id, tag.data_type, tag.count, custom_type)
        # Return reference at tag group object
        return tg

    @staticmethod
    def _receive_tg_destroy(node_id, tg_id):
        """
        Static method of class that should be called when
        destroy callback session method is called
        """
        # Try to find node
        try:
            node = VerseNode.nodes[node_id]
        except KeyError:
            return
        # Try to find tag group
        try:
            tg = node.taggroups[tg_id]
        except KeyError:
            return
        # Destroy tag group
        tg._receive_destroy()
        # Return reference at this object
        return tg

# VerseNode class
class VerseNode(VerseEntity):
    """
    Class representing Verse node
    """

    nodes = {}
    my_node_queues = {}
    
    def __init__(self, node_id, parent, user_id, custom_type):
        """
        Constructor of VerseNode
        """
        super(VerseNode, self).__init__()
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

        # Change state and send commands
        self._create()

        # When node_id is not set, then:
        if node_id is None:
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


    def destroy(self, send_destroy_cmd=True):
        """
        This method try to send destroy command
        """
        # Change state and send commands
        self._destroy()


    def _clean(self):
        """
        This method try to destroy all data in this object
        """
        # Delete all child nodes, but do not send destroy command
        # for these nodes
        for child_node in self.child_nodes.values():
            child_node.parent = None
            child_node._clean()
        self.child_nodes.clear()
        # Remove reference on this node
        if self.id is not None:
            # Remove this node from dictionary of nodes
            __class__.nodes.pop(self.id)
            # Remove this node from dictionar of child nodes
            if self.parent is not None:
                try:
                    self.parent.child_nodes.pop(self.id)
                except KeyError:
                    pass
                self.parent = None
        # Clear tag groups
        self.taggroups.clear()
        self.tg_queue.clear()
        # Clear layers
        self.layers.clear()
        self.layer_queue.clear()


    def _send_create(self):
        """
        This method send node create command to Verse server
        """
        if session is not None and self.id is None:
            session.send_node_create(self.prio, self.custom_type)


    def _send_destroy(self):
        """
        This method send destroy command to Verse server
        """
        if session is not None and self.id is not None:
            session.send_node_destroy(self.prio, self.id)


    def _send_subscribe(self):
        """
        This method send subscribe command to Verse server
        """
        if session is not None and self.id is not None:
            session.send_node_subscribe(self.prio, self.id, self.version, self.crc32)
            self.subscribed = True


    @staticmethod
    def _receive_node_create(node_id, parent_id, user_id, custom_type):
        """
        Static method of class that should be called, when coresponding callback
        method of class is called. This method moves node from queue to
        the dictionary of nodes and send pending commands
        """

        # Try to find parent node
        try:
            parent_node = __class__.nodes[parent_id]
        except KeyError:
            parent_node = None

        # Is it node created by this client?
        if parent_id == session.avatar_id:
            node_queue = __class__.my_node_queues[custom_type]
            # If this is node created by this client, then add it to
            # dictionary of nodes
            node = node_queue.pop()
            node.id = node_id
            __class__.nodes[node_id] = node
            if node.parent is None:
                node.parent = parent_node
        else:
            node = VerseNode(node_id, parent_node, user_id, custom_type)

        # Chnage state of node
        node._receive_create()

        # Send tag group create for pending tag groups
        for custom_type in node.tg_queue.keys():
            session.send_taggroup_create(node.prio, node.id, custom_type)

        # When node priority is different from default node priority
        if node.prio != vrs.DEFAULT_PRIORITY:
            session.send_node_prio(node.prio, node.id, node.prio)

        # When parent node is different then current parent, then send node_link
        # command to Verse server
        if node.parent is not None and parent_id != node.parent.id:
            session.send_node_link(node.prio, node.parent.id, node.id)
            # Add reference to list of child nodes to parent node now,
            # because it is possible to do now (node id is known)
            node.parent.child_nodes[node.id] = node

        # TODO: send layer_create

        # Return reference at node
        return node

    @staticmethod
    def _receive_node_destroy(node_id):
        """
        Static method of class that should be called, when destroy_node
        callback method of Session class is called. This method removes
        node from dictionary and node will be destroyed.
        """
        # Try to find node
        try:
            node = __class__.nodes[node_id]
        except KeyError:
            return
        # Set entity state and clean data in this node
        node._receive_destroy()
        # Return reference at this node
        return node

    @staticmethod
    def _receive_node_link(parent_node_id, child_node_id):
        """
        """
        # Try to find parent node
        try:
            parent_node = __class__.nodes[parent_node_id]
        except KeyError:
            return
        # Try to find child node
        try:
            child_node = __class__.nodes[child_node_id]
        except KeyError:
            return
        # When current link between nodes is different, then
        # set new link between nodes
        if child_node.parent.id != parent_node.id:
            # First remove child node from list of child nodes
            # of current parent node
            child.parent.child_nodes.pop(child_node_id)
            # Set new parent of child node
            child.parent = parent_node
            # Add child node to the list of child node of new
            # parent node
            parent_node.child_nodes[child_node_id] = child_node

        # Return reference at child node
        return child_node

