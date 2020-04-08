#!/usr/bin/env python

# Copyright (c) 2011, Dorian Scholz, TU Darmstadt
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above
#     copyright notice, this list of conditions and the following
#     disclaimer in the documentation and/or other materials provided
#     with the distribution.
#   * Neither the name of the TU Darmstadt nor the names of its
#     contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import os
import time

from typing import Tuple, List, ClassVar

from ament_index_python.resources import get_resource
from python_qt_binding import loadUi
from python_qt_binding.QtCore import Qt, QTimer, qWarning, Slot
from python_qt_binding.QtGui import QIcon
from python_qt_binding.QtWidgets import QAction, QMenu, QWidget

from rqt_py_common.topic_completer import TopicCompleter
from rqt_py_common import message_helpers, message_field_type_helpers

from rqt_plot.rosplot import ROSData, RosPlotException, get_topic_type

class MsgSpecException(Exception):
    pass

def _parse_type(topic_type_str): # -> Tuple[str, bool, int]:
    """
    Parses a msg type string and returns a tuple with information the type

    :returns: a Tuple with the base type of the slot as a str, a bool indicating
        if the slot is an array and an integer if it has a static or bound size
        or if it is unbounded, then the third value is None

        Strips out any array information from the topic_type_str

        eg:
            sequence<int8, 3> -> int8, true, 3
            sequence<int8>    -> int8, true, None
            int8[3]           -> int8, true, 3

    :rtype: str, bool, int
    """
    if not topic_type_str:
        raise MsgSpecException("Invalid empty type")

    slot_type = topic_type_str
    is_array = False
    array_size = None

    topic_type_info = message_field_type_helpers.MessageFieldTypeInfo(topic_type_str)
    slot_type = topic_type_info.base_type_str
    is_array = topic_type_info.is_array

    if topic_type_info.is_static_array:
        array_size = topic_type_info.static_array_size

    elif topic_type_info.is_bounded_array:
        array_size = topic_type_info.bounded_array_size

    elif topic_type_info.is_unbounded_array:
        array_size = None

    return slot_type, is_array, array_size

def get_plot_fields(node, topic_name):
    topic_type, real_topic, _ = get_topic_type(node, topic_name)
    if topic_type is None:
        message = "topic %s does not exist" % (topic_name)
        return [], message
    field_name = topic_name[len(real_topic) + 1:]

    is_array = False
    array_size = None
    slot_type = topic_type

    field_class = message_helpers.get_message_class(slot_type)
    if field_class is None:
        message = "type of topic %s is unknown" % (topic_name)
        return [], message

    field_index = None
    # Go through the fields until you reach the last msg field
    fields = [f for f in field_name.split('/') if f]
    for field in fields:
        # parse the field name for an array index
        try:
            field, _, field_index = \
                message_field_type_helpers.separate_field_from_array_information(field)
        except MsgSpecException:
            message = "invalid field %s in topic %s" % (field, real_topic)
            return [], message

        if not hasattr(field_class, "get_fields_and_field_types"):
            msg = "Invalid field path %s in topic %s" % (field_name, real_topic)
            return [], msg

        fields_and_field_types = field_class.get_fields_and_field_types()
        if field not in fields_and_field_types.keys() :
            message = "no field %s in topic %s" % (field_name, real_topic)
            return [], message

        slot_type = fields_and_field_types[field]
        slot_type, slot_is_array, array_size = _parse_type(slot_type)
        is_array = slot_is_array

        field_class = message_field_type_helpers.get_type_class(slot_type)

    # TODO: add bytes to this as you could treat bytes as an array of uint
    if field_class in (int, float, bool):
        topic_kind = 'boolean' if field_class == bool else 'numeric'
        if is_array:
            if array_size is not None:
                msg = "topic %s is fixed-size %s array" % (topic_name, topic_kind)
                return ["%s[%d]" % (topic_name, i) for i in range(array_size)], msg
            else:
                if field_index is not None:
                    msg = "topic %s is variable-size %s array with ix %d" % (
                        topic_name, topic_kind, field_index
                    )
                    return [topic_name], msg
                else:
                    msg = "topic %s is variable-size %s array" % (topic_name, topic_kind)
                    return [], msg
        else:
            msg = "topic %s is %s" % (topic_name, topic_kind)
            return [topic_name], msg
    else:
        if not message_field_type_helpers.is_primitive_type(slot_type):
            numeric_fields = []
            fields_and_field_types = field_class.get_fields_and_field_types()
            for i, slot in enumerate(fields_and_field_types.keys()):
                slot_type = fields_and_field_types[slot]
                slot_type, is_array, array_size = _parse_type(slot_type)
                slot_class = message_field_type_helpers.get_type_class(slot_type)
                if slot_class in (int, float) and not is_array:
                    numeric_fields.append(slot)
            message = ""
            if len(numeric_fields) > 0:
                message = "%d plottable fields in %s" % (len(numeric_fields), topic_name)
            else:
                message = "No plottable fields in %s" % (topic_name)
            return ["%s/%s" % (topic_name, f) for f in numeric_fields], message
        else:
            message = "Topic %s is not numeric" % (topic_name)
            return [], message


def is_plottable(node, topic_name):
    fields, message = get_plot_fields(node, topic_name)
    return len(fields) > 0, message


class PlotWidget(QWidget):
    _redraw_interval = 40

    def __init__(self, node, initial_topics=None, start_paused=False):
        super(PlotWidget, self).__init__()
        self.setObjectName('PlotWidget')

        self._node = node
        self._initial_topics = initial_topics

        _, package_path = get_resource('packages', 'rqt_plot')
        ui_file = os.path.join(package_path, 'share', 'rqt_plot', 'resource', 'plot.ui')
        loadUi(ui_file, self)
        self.subscribe_topic_button.setIcon(QIcon.fromTheme('list-add'))
        self.remove_topic_button.setIcon(QIcon.fromTheme('list-remove'))
        self.pause_button.setIcon(QIcon.fromTheme('media-playback-pause'))
        self.clear_button.setIcon(QIcon.fromTheme('edit-clear'))
        self.data_plot = None

        self.subscribe_topic_button.setEnabled(False)
        if start_paused:
            self.pause_button.setChecked(True)

        self._topic_completer = TopicCompleter(self.topic_edit)
        self._topic_completer.update_topics(node)
        self.topic_edit.setCompleter(self._topic_completer)

        self._start_time = time.time()
        self._rosdata = {}
        self._remove_topic_menu = QMenu()

        # init and start update timer for plot
        self._update_plot_timer = QTimer(self)
        self._update_plot_timer.timeout.connect(self.update_plot)

    def switch_data_plot_widget(self, data_plot):
        self.enable_timer(enabled=False)

        self.data_plot_layout.removeWidget(self.data_plot)
        if self.data_plot is not None:
            self.data_plot.close()

        self.data_plot = data_plot
        self.data_plot_layout.addWidget(self.data_plot)
        self.data_plot.autoscroll(self.autoscroll_checkbox.isChecked())

        # setup drag 'n drop
        self.data_plot.dropEvent = self.dropEvent
        self.data_plot.dragEnterEvent = self.dragEnterEvent

        if self._initial_topics:
            for topic_name in self._initial_topics:
                self.add_topic(topic_name)
            self._initial_topics = None
        else:
            for topic_name, rosdata in self._rosdata.items():
                data_x, data_y = rosdata.next()
                self.data_plot.add_curve(topic_name, topic_name, data_x, data_y)

        self._subscribed_topics_changed()

    @Slot('QDragEnterEvent*')
    def dragEnterEvent(self, event):
        # get topic name
        if not event.mimeData().hasText():
            if not hasattr(event.source(), 'selectedItems') or \
                    len(event.source().selectedItems()) == 0:
                qWarning(
                    'Plot.dragEnterEvent(): not hasattr(event.source(), selectedItems) or '
                    'len(event.source().selectedItems()) == 0')
                return
            item = event.source().selectedItems()[0]
            topic_name = item.data(0, Qt.UserRole)
            if topic_name == None:
                qWarning('Plot.dragEnterEvent(): not hasattr(item, ros_topic_name_)')
                return
        else:
            topic_name = str(event.mimeData().text())

        # check for plottable field type
        plottable, message = is_plottable(self._node, topic_name)
        if plottable:
            event.acceptProposedAction()
        else:
            qWarning('Plot.dragEnterEvent(): rejecting: "%s"' % (message))

    @Slot('QDropEvent*')
    def dropEvent(self, event):
        if event.mimeData().hasText():
            topic_name = str(event.mimeData().text())
        else:
            droped_item = event.source().selectedItems()[0]
            topic_name = str(droped_item.data(0, Qt.UserRole))
        self.add_topic(topic_name)

    @Slot(str)
    def on_topic_edit_textChanged(self, topic_name):
        # on empty topic name, update topics
        if topic_name in ('', '/'):
            self._topic_completer.update_topics(self._node)

        plottable, message = is_plottable(self._node, topic_name)
        self.subscribe_topic_button.setEnabled(plottable)
        self.subscribe_topic_button.setToolTip(message)

    @Slot()
    def on_topic_edit_returnPressed(self):
        if self.subscribe_topic_button.isEnabled():
            self.add_topic(str(self.topic_edit.text()))

    @Slot()
    def on_subscribe_topic_button_clicked(self):
        self.add_topic(str(self.topic_edit.text()))

    @Slot(bool)
    def on_pause_button_clicked(self, checked):
        self.enable_timer(not checked)

    @Slot(bool)
    def on_autoscroll_checkbox_clicked(self, checked):
        self.data_plot.autoscroll(checked)
        if checked:
            self.data_plot.redraw()

    @Slot()
    def on_clear_button_clicked(self):
        self.clear_plot()

    def update_plot(self):
        if self.data_plot is not None:
            needs_redraw = False
            for topic_name, rosdata in self._rosdata.items():
                try:
                    data_x, data_y = rosdata.next()
                    if data_x or data_y:
                        self.data_plot.update_values(topic_name, data_x, data_y)
                        needs_redraw = True
                except RosPlotException as e:
                    qWarning('PlotWidget.update_plot(): error in rosplot: %s' % e)
            if needs_redraw:
                self.data_plot.redraw()

    def _subscribed_topics_changed(self):
        self._update_remove_topic_menu()
        if not self.pause_button.isChecked():
            # if pause button is not pressed, enable timer based on subscribed topics
            self.enable_timer(self._rosdata)
        self.data_plot.redraw()

    def _update_remove_topic_menu(self):
        def make_remove_topic_function(x):
            return lambda: self.remove_topic(x)

        self._remove_topic_menu.clear()
        for topic_name in sorted(self._rosdata.keys()):
            action = QAction(topic_name, self._remove_topic_menu)
            action.triggered.connect(make_remove_topic_function(topic_name))
            self._remove_topic_menu.addAction(action)

        if len(self._rosdata) > 1:
            all_action = QAction('All', self._remove_topic_menu)
            all_action.triggered.connect(self.clean_up_subscribers)
            self._remove_topic_menu.addAction(all_action)

        self.remove_topic_button.setMenu(self._remove_topic_menu)

    def add_topic(self, topic_name):
        topics_changed = False
        topics, msg = get_plot_fields(self._node, topic_name)
        if len(topics) == 0:
            qWarning("get_plot_fields failed with msg: %s" % msg)
            return

        for topic_name in topics:
            if topic_name in self._rosdata:
                qWarning('PlotWidget.add_topic(): topic already subscribed: %s' % topic_name)
                continue
            self._rosdata[topic_name] = ROSData(self._node, topic_name, self._start_time)
            if self._rosdata[topic_name].error is not None:
                qWarning(str(self._rosdata[topic_name].error))
                del self._rosdata[topic_name]
            else:
                data_x, data_y = self._rosdata[topic_name].next()
                self.data_plot.add_curve(topic_name, topic_name, data_x, data_y)
                topics_changed = True

        if topics_changed:
            self._subscribed_topics_changed()

    def remove_topic(self, topic_name):
        self._rosdata[topic_name].close()
        del self._rosdata[topic_name]
        self.data_plot.remove_curve(topic_name)

        self._subscribed_topics_changed()

    def clear_plot(self):
        for topic_name, _ in self._rosdata.items():
            self.data_plot.clear_values(topic_name)
        self.data_plot.redraw()

    def clean_up_subscribers(self):
        for topic_name, rosdata in self._rosdata.items():
            rosdata.close()
            self.data_plot.remove_curve(topic_name)
        self._rosdata = {}

        self._subscribed_topics_changed()

    def enable_timer(self, enabled=True):
        if enabled:
            self._update_plot_timer.start(self._redraw_interval)
        else:
            self._update_plot_timer.stop()
