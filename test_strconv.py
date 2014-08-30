#!/usr/bin/env python
import unittest
from datetime import datetime, date, time

from dateutil.tz import tzoffset

import strconv


class StrconvTestCase(unittest.TestCase):
    def test_default(self):
        s = strconv.Strconv()
        self.assertEqual(len(s.converters), 0)
        self.assertRaises(KeyError, s.converters.__getitem__, 'int')
        self.assertEqual(s.convert('1'), '1')

    def test_strconv_with_int_converter(self):
        s = strconv.Strconv([('int', strconv.convert_int)])
        self.assertEqual(len(s.converters), 1)
        self.assertEqual(s.converters['int'], strconv.convert_int)
        self.assertEqual(s.convert('1'), 1)
        self.assertEqual(s.convert('-112'), -112)
        self.assertEqual(s.convert('-112', True), (-112, 'int'))
        self.assertEqual(s.convert('-1f12', True), ('-1f12', None))


class ConvertTestCase(unittest.TestCase):
    def test_convert(self):
        self.assertEqual(strconv.convert('-3'), -3)
        self.assertEqual(strconv.convert('+0.4'), 0.4)
        self.assertEqual(strconv.convert('true'), True)
        self.assertEqual(strconv.convert('3/20/2013'), datetime(2013, 3, 20))
        self.assertEqual(strconv.convert('5:40 PM'), time(17, 40))
        self.assertEqual(strconv.convert('March 4, 2013 5:40 PM'),
                         datetime(2013, 3, 4, 17, 40, 0))

    def test_convert_include_type(self):
        self.assertEqual(strconv.convert('-3', include_type=True), (-3, 'int'))

    def test_convert_series(self):
        self.assertEqual(list(strconv.convert_series(['+0.4'])), [0.4])

    def test_convert_matrix(self):
        self.assertEqual(list(strconv.convert_matrix([['+0.4']])), [(0.4,)])


class InferTestCase(unittest.TestCase):
    def test_infer(self):
        self.assertEqual(strconv.infer('-3'), 'int')
        self.assertEqual(strconv.infer(''), 'float')
        self.assertEqual(strconv.infer('+0.4'), 'float')
        self.assertEqual(strconv.infer('true'), 'bool')
        self.assertEqual(strconv.infer('3/20/2013'), 'datetime')
        self.assertEqual(strconv.infer('5:40 PM'), 'time')
        self.assertEqual(strconv.infer('March 4, 2013 5:40 PM'), 'datetime')

    def test_infer_converted(self):
        self.assertEqual(strconv.infer('-3', astype=True), int)
        self.assertEqual(strconv.infer('+0.4', astype=True), float)
        self.assertEqual(strconv.infer('true', astype=True), bool)
        self.assertEqual(strconv.infer('3/20/2013', astype=True), datetime)
        self.assertEqual(strconv.infer('5:40 PM', astype=True), time)
        self.assertEqual(strconv.infer('March 4, 2013 5:40 PM',
                         astype=True), datetime)

    def test_infer_series(self):
        c0 = strconv.infer_series(['+0.4', '1.0', '0.'])
        self.assertEqual(c0.most_common(), [('float', 3)])
        self.assertEqual(c0.types['float'].freq(), 1.0)
        self.assertEqual(c0.types['float'].count, 3)
        self.assertIsNone(c0.types['float'].size)  # default size

        self.assertEqual(strconv.infer_series([]), None)

    def test_infer_series_n(self):
        c0 = strconv.infer_series(['+0.4', '1.0', '0.'], n=1)
        self.assertEqual(c0.most_common(), [('float', 1)])
        self.assertEqual(c0.types['float'].count, 1)

    def test_infer_matrix(self):
        c0, c1, c2 = strconv.infer_matrix([['+0.4', 'true', '50']])
        self.assertEqual(c0.most_common(), [('float', 1)])
        self.assertEqual(c0.types['float'].freq(), 1.0)
        self.assertIsNone(c0.size)  # default size

        self.assertEqual(strconv.infer_matrix([]), [])

    def test_infer_matrix_n(self):
        c0, c1, c2 = strconv.infer_matrix([
            ['+0.4', 'true', '50'],
            ['+0.3', 'f', '0'],
        ], n=1)
        self.assertEqual(c0.most_common(), [('float', 1)])


class ConverterTestCase(unittest.TestCase):
    def test_convert_int(self):
        self.assertEqual(strconv.convert_int('0'), 0)
        self.assertEqual(strconv.convert_int('1'), 1)
        self.assertEqual(strconv.convert_int('+1'), 1)
        self.assertEqual(strconv.convert_int('-1'), -1)

    def test_convert_float(self):
        self.assertEqual(strconv.convert_float('0.'), 0.0)
        self.assertEqual(strconv.convert_float('+.0'), 0.0)
        self.assertEqual(strconv.convert_float('-.0'), 0.0)
        self.assertEqual(strconv.convert_float('1.'), 1.0)
        self.assertEqual(strconv.convert_float('+1.'), 1.0)
        self.assertEqual(strconv.convert_float('-1.'), -1.0)

    def test_convert_bool(self):
        self.assertEqual(strconv.convert_bool('t'), True)
        self.assertEqual(strconv.convert_bool('true'), True)
        self.assertEqual(strconv.convert_bool('yes'), True)
        self.assertEqual(strconv.convert_bool('f'), False)
        self.assertEqual(strconv.convert_bool('false'), False)
        self.assertEqual(strconv.convert_bool('no'), False)

    def test_convert_date(self):
        self.assertEqual(strconv.convert_date('2013-03-01'), date(2013, 3, 1))
        self.assertEqual(strconv.convert_date('2013-3-1'), date(2013, 3, 1))
        self.assertEqual(strconv.convert_date('3-1-2013'), date(2013, 3, 1))
        self.assertEqual(strconv.convert_date('3/1/2013'), date(2013, 3, 1))
        self.assertEqual(strconv.convert_date('3.1.2013'), date(2013, 3, 1))
        self.assertEqual(strconv.convert_date('Mar 1, 2013'), date(2013, 3, 1))

    def test_convert_time(self):
        self.assertEqual(strconv.convert_time('01:30'), time(1, 30, 0))
        self.assertEqual(strconv.convert_time('1:30'), time(1, 30, 0))
        self.assertEqual(strconv.convert_time('1:30:40'), time(1, 30, 40))
        self.assertEqual(strconv.convert_time('1:30:40 pm'), time(13, 30, 40))
        self.assertEqual(strconv.convert_time('15:30:40'), time(15, 30, 40))
        self.assertEqual(strconv.convert_time('5:30:40 AM'), time(5, 30, 40))

    def test_convert_datetime(self):
        tzoff = tzoffset(None, -18000)

        self.assertEqual(strconv.convert_datetime('Mar 1, 2013T5:30:40 AM'),
                         datetime(2013, 3, 1, 5, 30, 40))
        self.assertEqual(strconv.convert_datetime('Mar 1, 2013 5:30:40 AM'),
                         datetime(2013, 3, 1, 5, 30, 40))
        self.assertRaises(ValueError, strconv.convert_datetime, 'foo')

        # TZ
        self.assertEqual(strconv.convert_datetime('2013-03-01 5:30:40 -0500'),
                         datetime(2013, 3, 1, 5, 30, 40, tzinfo=tzoff))

if __name__ == '__main__':
    unittest.main()
