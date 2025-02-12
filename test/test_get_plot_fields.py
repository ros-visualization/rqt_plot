# Copyright (c) 2025, Apex.AI, Inc.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#    * Neither the name of the copyright holder nor the names of its
#      contributors may be used to endorse or promote products derived from
#      this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import unittest

import rclpy
from rclpy.node import Node
from rqt_plot.plot_widget import get_plot_fields


class TestGetPlotFields(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.maxDiff = None
        rclpy.init()
        cls.node = Node('test_node')

    @classmethod
    def tearDownClass(cls) -> None:
        cls.node.destroy_node()
        rclpy.shutdown()

    def test_simple_validation(self) -> None:
        # Invalid/nonexistent topic
        self.assertEqual(([], "topic '' does not exist"), get_plot_fields(self.node, ''))
        self.assertEqual(([], "topic '/' does not exist"), get_plot_fields(self.node, '/'))
        self.assertEqual(
            ([], "topic 'notopic' does not exist"),
            get_plot_fields(self.node, 'notopic'))
        self.assertEqual(
            ([], "topic '/notopic' does not exist"),
            get_plot_fields(self.node, '/notopic'))
        self.assertEqual(
            ([], "topic '/sub/notopic' does not exist"),
            get_plot_fields(self.node, '/sub/notopic'))

        from std_msgs.msg import String as MsgType
        pub = self.node.create_publisher(MsgType, 'test_topic', 10)

        # Will not match without a leading '/'
        self.assertEqual(
            ([], "topic 'test_topic' does not exist"),
            get_plot_fields(self.node, 'test_topic'))
        # Will not match with an invalid namespace
        self.assertEqual(
            ([], "topic '/sub/test_topic' does not exist"),
            get_plot_fields(self.node, '/sub/test_topic'))
        # Missing/invalid field name
        self.assertEqual(
            ([], "no field specified in topic name '/test_topic'"),
            get_plot_fields(self.node, '/test_topic'))
        # This message type has no plottable fields, so topic + trailing slash cannot be plotted
        self.assertEqual(
            ([], '/test_topic/ cannot be plotted'),
            get_plot_fields(self.node, '/test_topic/'))
        # Invalid/nonexistent field
        self.assertEqual(
            ([], "trying to parse field 'notfield' of topic '/test_topic': 'notfield' is not a field of 'std_msgs/msg/String'"),  # noqa: E501
            get_plot_fields(self.node, '/test_topic/notfield'))

        self.node.destroy_publisher(pub)

    def test_string(self) -> None:
        from test_msgs.msg import Strings as MsgType
        pub = self.node.create_publisher(MsgType, 'topic_strings', 10)

        self.assertEqual(
            ([], "'/topic_strings/string_value' is a string, which cannot be plotted"),
            get_plot_fields(self.node, '/topic_strings/string_value'))
        self.assertEqual(
            ([], "'/topic_strings/bounded_string_value' is a string, which cannot be plotted"),
            get_plot_fields(self.node, '/topic_strings/bounded_string_value'))

        self.node.destroy_publisher(pub)

    def test_wstring(self) -> None:
        try:
            from test_msgs.msg import WStrings as MsgType
        except ImportError:
            self.skipTest('no test_msgs.msg.WStrings')
        pub = self.node.create_publisher(MsgType, 'topic_wstrings', 10)

        self.assertEqual(
            ([], "'/topic_wstrings/wstring_value' is a string, which cannot be plotted"),
            get_plot_fields(self.node, '/topic_wstrings/wstring_value'))

        self.node.destroy_publisher(pub)

    def test_primitives(self) -> None:
        from test_msgs.msg import BasicTypes as MsgType
        pub = self.node.create_publisher(MsgType, 'topic_basic_types', 10)

        self.assertEqual(
            (['/topic_basic_types/bool_value'], "topic '/topic_basic_types/bool_value' is boolean"),  # noqa: E501
            get_plot_fields(self.node, '/topic_basic_types/bool_value'))
        self.assertEqual(
            (['/topic_basic_types/byte_value'], "topic '/topic_basic_types/byte_value' is numeric"),  # noqa: E501
            get_plot_fields(self.node, '/topic_basic_types/byte_value'))
        self.assertEqual(
            (['/topic_basic_types/char_value'], "topic '/topic_basic_types/char_value' is numeric"),  # noqa: E501
            get_plot_fields(self.node, '/topic_basic_types/char_value'))
        self.assertEqual(
            (['/topic_basic_types/float32_value'], "topic '/topic_basic_types/float32_value' is numeric"),  # noqa: E501
            get_plot_fields(self.node, '/topic_basic_types/float32_value'))
        self.assertEqual(
            (['/topic_basic_types/float64_value'], "topic '/topic_basic_types/float64_value' is numeric"),  # noqa: E501
            get_plot_fields(self.node, '/topic_basic_types/float64_value'))
        self.assertEqual(
            (['/topic_basic_types/int8_value'], "topic '/topic_basic_types/int8_value' is numeric"),  # noqa: E501
            get_plot_fields(self.node, '/topic_basic_types/int8_value'))
        self.assertEqual(
            (['/topic_basic_types/uint8_value'], "topic '/topic_basic_types/uint8_value' is numeric"),  # noqa: E501
            get_plot_fields(self.node, '/topic_basic_types/uint8_value'))
        self.assertEqual(
            (['/topic_basic_types/int16_value'], "topic '/topic_basic_types/int16_value' is numeric"),  # noqa: E501
            get_plot_fields(self.node, '/topic_basic_types/int16_value'))
        self.assertEqual(
            (['/topic_basic_types/uint16_value'], "topic '/topic_basic_types/uint16_value' is numeric"),  # noqa: E501
            get_plot_fields(self.node, '/topic_basic_types/uint16_value'))
        self.assertEqual(
            (['/topic_basic_types/int32_value'], "topic '/topic_basic_types/int32_value' is numeric"),  # noqa: E501
            get_plot_fields(self.node, '/topic_basic_types/int32_value'))
        self.assertEqual(
            (['/topic_basic_types/uint32_value'], "topic '/topic_basic_types/uint32_value' is numeric"),  # noqa: E501
            get_plot_fields(self.node, '/topic_basic_types/uint32_value'))
        self.assertEqual(
            (['/topic_basic_types/int64_value'], "topic '/topic_basic_types/int64_value' is numeric"),  # noqa: E501
            get_plot_fields(self.node, '/topic_basic_types/int64_value'))
        self.assertEqual(
            (['/topic_basic_types/uint64_value'], "topic '/topic_basic_types/uint64_value' is numeric"),  # noqa: E501
            get_plot_fields(self.node, '/topic_basic_types/uint64_value'))
        # This message type has plottable fields, so topic + trailing slash can be plotted
        self.assertEqual(
            (
                [
                    '/topic_basic_types/bool_value',
                    '/topic_basic_types/byte_value',
                    '/topic_basic_types/char_value',
                    '/topic_basic_types/float32_value',
                    '/topic_basic_types/float64_value',
                    '/topic_basic_types/int8_value',
                    '/topic_basic_types/uint8_value',
                    '/topic_basic_types/int16_value',
                    '/topic_basic_types/uint16_value',
                    '/topic_basic_types/int32_value',
                    '/topic_basic_types/uint32_value',
                    '/topic_basic_types/int64_value',
                    '/topic_basic_types/uint64_value',
                ],
                "13 plottable fields in '/topic_basic_types/'"),
            get_plot_fields(self.node, '/topic_basic_types/'))

        self.node.destroy_publisher(pub)

    def test_arrays(self) -> None:
        from test_msgs.msg import Arrays as MsgType
        pub = self.node.create_publisher(MsgType, 'topic_arrays', 10)

        self.assertEqual(
            ([], "trying to parse field 'int8_values' of topic '/topic_arrays': 'int8_values' is a nested type but no index provided"),  # noqa: E501
            get_plot_fields(self.node, '/topic_arrays/int8_values'))
        self.assertEqual(
            ([], "trying to parse field 'int8_values[' of topic '/topic_arrays': 'int8_values[' is not a field of 'test_msgs/msg/Arrays'"),  # noqa: E501
            get_plot_fields(self.node, '/topic_arrays/int8_values['))
        self.assertEqual(
            ([], "trying to parse field 'int8_values[]' of topic '/topic_arrays': 'int8_values[]' is not a field of 'test_msgs/msg/Arrays'"),  # noqa: E501
            get_plot_fields(self.node, '/topic_arrays/int8_values[]'))
        self.assertEqual(
            ([], "trying to parse field 'int8_values[3]' of topic '/topic_arrays': index '3' out of bounds, maximum size is 3"),  # noqa: E501
            get_plot_fields(self.node, '/topic_arrays/int8_values[3]'))
        self.assertEqual(
            ([], "trying to parse field 'int8_values[4]' of topic '/topic_arrays': index '4' out of bounds, maximum size is 3"),  # noqa: E501
            get_plot_fields(self.node, '/topic_arrays/int8_values[4]'))
        self.assertEqual(
            ([], "trying to parse field 'int8_values[42]' of topic '/topic_arrays': index '42' out of bounds, maximum size is 3"),  # noqa: E501
            get_plot_fields(self.node, '/topic_arrays/int8_values[42]'))
        self.assertEqual(
            ([], "trying to parse field 'alignment_check[42]' of topic '/topic_arrays': 'alignment_check' is not an array or sequence"),  # noqa: E501
            get_plot_fields(self.node, '/topic_arrays/alignment_check[42]'))
        self.assertEqual(
            ([], "'/topic_arrays/string_values_default[0]' is a string, which cannot be plotted"),
            get_plot_fields(self.node, '/topic_arrays/string_values_default[0]'))

        self.assertEqual(
            (['/topic_arrays/int8_values[0]'], "topic '/topic_arrays/int8_values[0]' is numeric"),
            get_plot_fields(self.node, '/topic_arrays/int8_values[0]'))
        self.assertEqual(
            (['/topic_arrays/int8_values[1]'], "topic '/topic_arrays/int8_values[1]' is numeric"),
            get_plot_fields(self.node, '/topic_arrays/int8_values[1]'))
        self.assertEqual(
            (['/topic_arrays/int8_values[2]'], "topic '/topic_arrays/int8_values[2]' is numeric"),
            get_plot_fields(self.node, '/topic_arrays/int8_values[2]'))
        self.assertEqual(
            (['/topic_arrays/bool_values[0]'], "topic '/topic_arrays/bool_values[0]' is boolean"),
            get_plot_fields(self.node, '/topic_arrays/bool_values[0]'))

        self.node.destroy_publisher(pub)

    def test_bounded_sequences(self) -> None:
        from test_msgs.msg import BoundedSequences as MsgType
        pub = self.node.create_publisher(MsgType, 'topic_bounded_seq', 10)

        self.assertEqual(
            ([], "trying to parse field 'int8_values' of topic '/topic_bounded_seq': 'int8_values' is a nested type but no index provided"),  # noqa: E501
            get_plot_fields(self.node, '/topic_bounded_seq/int8_values'))
        self.assertEqual(
            ([], "trying to parse field 'int8_values[3]' of topic '/topic_bounded_seq': index '3' out of bounds, maximum size is 3"),  # noqa: E501
            get_plot_fields(self.node, '/topic_bounded_seq/int8_values[3]'))
        self.assertEqual(
            ([], "trying to parse field 'int8_values[4]' of topic '/topic_bounded_seq': index '4' out of bounds, maximum size is 3"),  # noqa: E501
            get_plot_fields(self.node, '/topic_bounded_seq/int8_values[4]'))
        self.assertEqual(
            ([], "trying to parse field 'int8_values[42]' of topic '/topic_bounded_seq': index '42' out of bounds, maximum size is 3"),  # noqa: E501
            get_plot_fields(self.node, '/topic_bounded_seq/int8_values[42]'))
        self.assertEqual(
            ([], "trying to parse field 'alignment_check[42]' of topic '/topic_bounded_seq': 'alignment_check' is not an array or sequence"),  # noqa: E501
            get_plot_fields(self.node, '/topic_bounded_seq/alignment_check[42]'))

        self.assertEqual(
            (['/topic_bounded_seq/int8_values[0]'], "topic '/topic_bounded_seq/int8_values[0]' is numeric"),  # noqa: E501
            get_plot_fields(self.node, '/topic_bounded_seq/int8_values[0]'))
        self.assertEqual(
            (['/topic_bounded_seq/int8_values[1]'], "topic '/topic_bounded_seq/int8_values[1]' is numeric"),  # noqa: E501
            get_plot_fields(self.node, '/topic_bounded_seq/int8_values[1]'))
        self.assertEqual(
            (['/topic_bounded_seq/int8_values[2]'], "topic '/topic_bounded_seq/int8_values[2]' is numeric"),  # noqa: E501
            get_plot_fields(self.node, '/topic_bounded_seq/int8_values[2]'))
        self.assertEqual(
            (['/topic_bounded_seq/bool_values[0]'], "topic '/topic_bounded_seq/bool_values[0]' is boolean"),  # noqa: E501
            get_plot_fields(self.node, '/topic_bounded_seq/bool_values[0]'))

        self.node.destroy_publisher(pub)

    def test_unbounded_sequences(self) -> None:
        from test_msgs.msg import UnboundedSequences as MsgType
        pub = self.node.create_publisher(MsgType, 'topic_unbounded_seq', 10)

        self.assertEqual(
            ([], "trying to parse field 'int8_values' of topic '/topic_unbounded_seq': 'int8_values' is a nested type but no index provided"),  # noqa: E501
            get_plot_fields(self.node, '/topic_unbounded_seq/int8_values'))
        self.assertEqual(
            ([], "trying to parse field 'alignment_check[42]' of topic '/topic_unbounded_seq': 'alignment_check' is not an array or sequence"),  # noqa: E501
            get_plot_fields(self.node, '/topic_unbounded_seq/alignment_check[42]'))

        self.assertEqual(
            (['/topic_unbounded_seq/int8_values[0]'], "topic '/topic_unbounded_seq/int8_values[0]' is numeric"),  # noqa: E501
            get_plot_fields(self.node, '/topic_unbounded_seq/int8_values[0]'))
        self.assertEqual(
            (['/topic_unbounded_seq/int8_values[999999]'], "topic '/topic_unbounded_seq/int8_values[999999]' is numeric"),  # noqa: E501
            get_plot_fields(self.node, '/topic_unbounded_seq/int8_values[999999]'))
        self.assertEqual(
            (['/topic_unbounded_seq/bool_values[0]'], "topic '/topic_unbounded_seq/bool_values[0]' is boolean"),  # noqa: E501
            get_plot_fields(self.node, '/topic_unbounded_seq/bool_values[0]'))

        self.node.destroy_publisher(pub)

    def test_nested(self) -> None:
        from test_msgs.msg import Nested as MsgType
        pub = self.node.create_publisher(MsgType, 'topic_nested', 10)

        self.assertEqual(
            (
                [
                    '/topic_nested/basic_types_value/bool_value',
                    '/topic_nested/basic_types_value/byte_value',
                    '/topic_nested/basic_types_value/char_value',
                    '/topic_nested/basic_types_value/float32_value',
                    '/topic_nested/basic_types_value/float64_value',
                    '/topic_nested/basic_types_value/int8_value',
                    '/topic_nested/basic_types_value/uint8_value',
                    '/topic_nested/basic_types_value/int16_value',
                    '/topic_nested/basic_types_value/uint16_value',
                    '/topic_nested/basic_types_value/int32_value',
                    '/topic_nested/basic_types_value/uint32_value',
                    '/topic_nested/basic_types_value/int64_value',
                    '/topic_nested/basic_types_value/uint64_value',
                ],
                "13 plottable fields in '/topic_nested/basic_types_value'",
            ),
            get_plot_fields(self.node, '/topic_nested/basic_types_value'))
        self.assertEqual(
            (
                [
                    '/topic_nested/basic_types_value/bool_value',
                    '/topic_nested/basic_types_value/byte_value',
                    '/topic_nested/basic_types_value/char_value',
                    '/topic_nested/basic_types_value/float32_value',
                    '/topic_nested/basic_types_value/float64_value',
                    '/topic_nested/basic_types_value/int8_value',
                    '/topic_nested/basic_types_value/uint8_value',
                    '/topic_nested/basic_types_value/int16_value',
                    '/topic_nested/basic_types_value/uint16_value',
                    '/topic_nested/basic_types_value/int32_value',
                    '/topic_nested/basic_types_value/uint32_value',
                    '/topic_nested/basic_types_value/int64_value',
                    '/topic_nested/basic_types_value/uint64_value',
                ],
                "13 plottable fields in '/topic_nested/basic_types_value/'",
            ),
            get_plot_fields(self.node, '/topic_nested/basic_types_value/'))

        self.node.destroy_publisher(pub)

    def test_multinested(self) -> None:
        from test_msgs.msg import MultiNested as MsgType1
        from std_msgs.msg import Int64MultiArray as MsgType2
        pub1 = self.node.create_publisher(MsgType1, 'topic_multinested1', 10)
        pub2 = self.node.create_publisher(MsgType2, 'topic_multinested2', 10)

        # We only count fields of basic types as "plottable fields"
        self.assertEqual(
            (
                ['/topic_multinested1/array_of_arrays[0]/alignment_check'],
                "1 plottable fields in '/topic_multinested1/array_of_arrays[0]'",
            ),
            get_plot_fields(self.node, '/topic_multinested1/array_of_arrays[0]'))
        self.assertEqual(
            (
                ['/topic_multinested1/array_of_arrays[0]/alignment_check'],
                "1 plottable fields in '/topic_multinested1/array_of_arrays[0]/'",
            ),
            get_plot_fields(self.node, '/topic_multinested1/array_of_arrays[0]/'))
        self.assertEqual(
            ([], "trying to parse field 'array_of_arrays[0].int8_values' of topic '/topic_multinested1': 'int8_values' is a nested type but no index provided"),  # noqa: E501
            get_plot_fields(self.node, '/topic_multinested1/array_of_arrays[0]/int8_values'))
        self.assertEqual(
            (
                ['/topic_multinested1/array_of_arrays[0]/int8_values[0]'],
                "topic '/topic_multinested1/array_of_arrays[0]/int8_values[0]' is numeric",
            ),
            get_plot_fields(self.node, '/topic_multinested1/array_of_arrays[0]/int8_values[0]'))
        self.assertEqual(
            (
                [
                    '/topic_multinested2/layout/dim[0]/size',
                    '/topic_multinested2/layout/dim[0]/stride',
                ],
                "2 plottable fields in '/topic_multinested2/layout/dim[0]'",
            ),
            get_plot_fields(self.node, '/topic_multinested2/layout/dim[0]'))
        self.assertEqual(
            (
                [
                    '/topic_multinested2/layout/dim[0]/size',
                    '/topic_multinested2/layout/dim[0]/stride',
                ],
                "2 plottable fields in '/topic_multinested2/layout/dim[0]/'",
            ),
            get_plot_fields(self.node, '/topic_multinested2/layout/dim[0]/'))

        self.node.destroy_publisher(pub1)
        self.node.destroy_publisher(pub2)
