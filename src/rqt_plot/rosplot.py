#!/usr/bin/env python
#
# Software License Agreement (BSD License)
#
# Copyright (c) 2009, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Willow Garage, Inc. nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
import sys

import threading
import time

from operator import itemgetter

from rclpy.qos import QoSProfile
from rqt_py_common.message_helpers import get_message_class
from std_msgs.msg import Bool
from python_qt_binding.QtCore import qWarning


class RosPlotException(Exception):
    pass

def _get_nested_attribute(msg, nested_attributes):
    value = msg
    for attr in nested_attributes.split('/'):
        value = getattr(value, attr)
    return value

def _get_topic_type(topic_names_and_types, path_to_field):
    """
    subroutine for getting the topic type, topic name and path to field
    (nearly identical to rostopic._get_topic_type, except it returns rest of name instead of fn)

    :returns: topic type, real topic name, and path_to_field
      if the topic points to a field within a topic, e.g. /rosout/msg, ``str, str, str``
    """
    # See if we can find a full match
    matches = []
    for (t_name, t_types) in topic_names_and_types:
        if t_name == path_to_field:
            for t_type in t_types:
                matches.append((t_name, t_type))

    if not matches:
        for (t_name, t_types) in topic_names_and_types:
            if path_to_field.startswith(t_name + '/'):
                for t_type in t_types:
                    matches.append((t_name, t_type))

        # choose longest match first
        matches.sort(key=itemgetter(0), reverse=True)

        # try to ignore messages which don't have the field specified as part of the topic name
        while matches:
            t_name, t_type = matches[0]
            msg_class = get_message_class(t_type)
            if not msg_class:
                # if any class is not fetchable skip ignoring any message types
                break

            msg = msg_class()
            nested_attributes = path_to_field[len(t_name) + 1:].rstrip('/')
            nested_attributes = nested_attributes.split('[')[0]
            if nested_attributes == '':
                break
            try:
                _get_nested_attribute(msg, nested_attributes)
            except AttributeError:
                # ignore this type since it does not have the requested field
                matches.pop(0)
                continue
            # Select this match
            matches = [(t_name, t_type)]
            break
    if matches:
        t_name, t_type = matches[0]
        # This is a relic from ros1 where rosgraph.names.ANYTYPE = '*'.
        # TODO(remove)
        if t_type == '*':
            return None, None, None
        return t_type, t_name, path_to_field[len(t_name):]

    return None, None, None

def get_topic_type(node, path_to_field):
    """
    Get the topic type (nearly identical to rostopic.get_topic_type, except it doesn't return a fn)

    :returns: topic type, real topic name and rest of name referenced
      if the topic points to a field within a topic, e.g. /rosout/msg, ``str, str, str``
    """
    topic_names_and_types = node.get_topic_names_and_types()
    topic_type, real_topic, rest = _get_topic_type(topic_names_and_types, path_to_field)
    if topic_type:
        return topic_type, real_topic, rest
    else:
        return None, None, None

class ROSData(object):

    """
    Subscriber to ROS topic that buffers incoming data
    """

    def __init__(self, node, topic, start_time):
        self.name = topic
        self.start_time = start_time
        self.error = None
        self.node = node

        self.lock = threading.Lock()
        self.buff_x = []
        self.buff_y = []

        topic_type, real_topic, fields = get_topic_type(node, topic)
        if topic_type is not None:
            self.field_evals = generate_field_evals(fields)
            data_class = get_message_class(topic_type)
            self.sub = node.create_subscription(
                data_class, real_topic, self._ros_cb, qos_profile=QoSProfile(depth=10))
        else:
            self.error = RosPlotException("Can not resolve topic type of %s" % topic)

    def close(self):
        self.node.destroy_subscription(self.sub)

    def _ros_cb(self, msg):
        """
        ROS subscriber callback
        :param msg: ROS message data
        """
        try:
            self.lock.acquire()
            try:
                self.buff_y.append(self._get_data(msg))
                # 944: use message header time if present
                if hasattr(msg, 'header'):
                    stamped_time = msg.header.stamp.sec + msg.header.stamp.nanosec * 10**-9
                    self.buff_x.append(stamped_time - self.start_time)
                else:
                    self.buff_x.append(time.time() - self.start_time)
                # self.axes[index].plot(datax, buff_y)
            except AttributeError as e:
                self.error = RosPlotException("Invalid topic spec [%s]: %s" % (self.name, str(e)))
        finally:
            self.lock.release()

    def next(self):
        """
        Get the next data in the series

        :returns: [xdata], [ydata]
        """
        if self.error:
            raise self.error
        try:
            self.lock.acquire()
            buff_x = self.buff_x
            buff_y = self.buff_y
            self.buff_x = []
            self.buff_y = []
        finally:
            self.lock.release()
        return buff_x, buff_y

    def _get_data(self, msg):
        val = msg
        try:
            if not self.field_evals:
                if isinstance(val, Bool):
                    # extract boolean field from bool messages
                    val = val.data
                return float(val)
            for f in self.field_evals:
                val = f(val)
            return float(val)
        except IndexError:
            self.error = RosPlotException(
                "[%s] index error for: %s" % (self.name, str(val).replace('\n', ', ')))
        except TypeError:
            self.error = RosPlotException("[%s] value was not numeric: %s" % (self.name, val))


def _array_eval(field_name, slot_num):
    """
    :param field_name: name of field to index into, ``str``
    :param slot_num: index of slot to return, ``str``
    :returns: fn(msg_field)->msg_field[slot_num]
    """
    def fn(f):
        return getattr(f, field_name).__getitem__(slot_num)
    return fn


def _field_eval(field_name):
    """
    :param field_name: name of field to return, ``str``
    :returns: fn(msg_field)->msg_field.field_name
    """
    def fn(f):
        return getattr(f, field_name)
    return fn


def generate_field_evals(fields):
    try:
        evals = []
        fields = [f for f in fields.split('/') if f]
        for f in fields:
            if '[' in f:
                field_name, rest = f.split('[', maxsplit=1)
                slot_num = int(rest[:rest.find(']')])
                evals.append(_array_eval(field_name, slot_num))
            else:
                evals.append(_field_eval(f))
        return evals
    except Exception as e:
        raise RosPlotException("cannot parse field reference [%s]: %s" % (fields, str(e)))
