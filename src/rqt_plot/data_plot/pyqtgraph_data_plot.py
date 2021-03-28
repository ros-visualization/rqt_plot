#!/usr/bin/env python

# Copyright (c) 2011, Dorian Scholz
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

from python_qt_binding.QtCore import Slot, Qt, qVersion, qWarning, Signal
from python_qt_binding.QtGui import QColor
from python_qt_binding.QtWidgets import QAction, QSpinBox, QVBoxLayout, QWidget

if qVersion().startswith('5.'):
    try:
        from pkg_resources import parse_version
    except:
        import re

        def parse_version(s):
            return [int(x) for x in re.sub(r'(\.0+)*$', '', s).split('.')]

    try:
        from pyqtgraph import __version__ as pyqtgraph_version
    except RuntimeError:
        # pyqtgraph < 1.0 using Qt4 failing on 16.04 because kinetic uses Qt5.
        # This raises RuntimeError('the PyQt4.QtCore and PyQt5.QtCore modules both
        # wrap the QObject class')
        import pkg_resources
        pyqtgraph_version = pkg_resources.get_distribution("pyqtgraph").version

    if parse_version(pyqtgraph_version) < parse_version('0.10.0'):
        raise ImportError('A newer PyQtGraph version is required (at least 0.10 for Qt 5)')

from pyqtgraph import PlotWidget, mkPen, mkBrush
import numpy


class PyQtGraphDataPlot(QWidget):

    limits_changed = Signal()

    def __init__(self, parent=None):
        super(PyQtGraphDataPlot, self).__init__(parent)
        self._plot_widget = PlotWidget()
        self._plot_widget.getPlotItem().addLegend()
        self._plot_widget.setBackground((255, 255, 255))
        self._plot_widget.setXRange(0, 10, padding=0)
        self._line_width = 1
        self._add_line_width_menu_option()
        vbox = QVBoxLayout()
        vbox.addWidget(self._plot_widget)
        self.setLayout(vbox)
        self._plot_widget.getPlotItem().sigRangeChanged.connect(self.limits_changed)

        self._curves = {}
        self._current_vline = None

    def add_curve(self, curve_id, curve_name, curve_color=QColor(Qt.blue), markers_on=False):
        pen = mkPen(curve_color, width=self._line_width)
        symbol = "o"
        symbolPen = mkPen(QColor(Qt.black))
        symbolBrush = mkBrush(curve_color)
        # this adds the item to the plot and legend
        if markers_on:
            plot = self._plot_widget.plot(name=curve_name, pen=pen, symbol=symbol,
                                          symbolPen=symbolPen, symbolBrush=symbolBrush, symbolSize=4)
        else:
            plot = self._plot_widget.plot(name=curve_name, pen=pen)
        self._curves[curve_id] = plot

    def remove_curve(self, curve_id):
        curve_id = str(curve_id)
        if curve_id in self._curves:
            self._plot_widget.removeItem(self._curves[curve_id])
            del self._curves[curve_id]
            self._update_legend()

    def _update_legend(self):
        # clear and rebuild legend (there is no remove item method for the legend...)
        self._plot_widget.clear()
        self._plot_widget.getPlotItem().legend.items = []
        for curve in self._curves.values():
            self._plot_widget.addItem(curve)
        if self._current_vline:
            self._plot_widget.addItem(self._current_vline)

    def _add_line_width_menu_option(self):
        menu = self._plot_widget.getMenu().addMenu('Line Width')
        menu.setLayout(QVBoxLayout())
        self._line_width_spinbox = QSpinBox()
        self._line_width_spinbox.setRange(1, 30)
        self._line_width_spinbox.valueChanged.connect(self._line_width_spinbox_valueChanged)
        menu.layout().addWidget(self._line_width_spinbox)

    @Slot(int)
    def _line_width_spinbox_valueChanged(self, val):
        self._line_width = val
        for curve in self._curves.values():
            color = curve.opts['pen'].color()
            curve.setPen(mkPen(color, width=self._line_width))

    def redraw(self):
        pass

    def set_values(self, curve_id, data_x, data_y):
        curve = self._curves[curve_id]
        curve.setData(data_x, data_y)

    def vline(self, x, color):
        if self._current_vline:
            self._plot_widget.removeItem(self._current_vline)
        self._current_vline = self._plot_widget.addLine(x=x, pen=color)

    def set_xlim(self, limits):
        # TODO: this doesn't seem to handle fast updates well
        self._plot_widget.setXRange(limits[0], limits[1], padding=0)

    def set_ylim(self, limits):
        self._plot_widget.setYRange(limits[0], limits[1], padding=0)

    def get_xlim(self):
        x_range, _ = self._plot_widget.viewRange()
        return x_range

    def get_ylim(self):
        _, y_range = self._plot_widget.viewRange()
        return y_range

    def save_settings(self, plugin_settings, instance_settings):
        instance_settings.set_value('plot_widget_state', self._plot_widget.saveState())
        instance_settings.set_value('qt_line_width', self._line_width)

    def restore_settings(self, plugin_settings, instance_settings):
        plot_widget_state = instance_settings.value('plot_widget_state')
        if plot_widget_state is not None:
            self._plot_widget.restoreState(plot_widget_state)

        qt_line_width = instance_settings.value('qt_line_width')
        if qt_line_width is not None:
            self._line_width = int(qt_line_width)
            self._line_width_spinbox.setValue(self._line_width)
