# -*- coding: utf-8 -*-
#
# Based on strconv by Byron Ruth
#
# Maintainer: Marius Cobzarenco <marius@reinfer.io>
#
# BSD License
from collections import Counter, OrderedDict
from datetime import datetime
import re

from dateutil.parser import parse as duparse

__version__ = '0.4.1'


class TypeInfo(object):
    "Sampling and frequency of a type for a sample of values."
    def __init__(self, name, size=None, total=None):
        self.name = name
        self.count = 0
        self.sample = []
        self.size = size
        self.total = total
        self.sample_set = set()

    def __repr__(self):
        return '<{0}: {1} n={2}>'.format(self.__class__.__name__,
                                         self.name, self.count)

    def incr(self, n=1):
        self.count += n

    def add(self, i, value):
        if self.size is None or len(self.sample) < self.size:
            # No dupes
            if value not in self.sample_set:
                self.sample_set.add(value)
                self.sample.append((i, value))

    def freq(self):
        if self.total:
            return self.count / float(self.total)
        return 0.


class Types(object):
    "Type information for a sample of values."
    def __init__(self, size=None, total=None):
        self.size = size
        self.total = None
        self.types = {}

    def __repr__(self):
        types = self.most_common()
        label = ', '.join(['{0}={1}'.format(t, i) for t, i in types])
        return '<{0}: {1}>'.format(self.__class__.__name__, label)

    def incr(self, t, n=1):
        if t is None:
            t = 'unknown'
        if t not in self.types:
            self.types[t] = TypeInfo(t, self.size, self.total)
        self.types[t].incr(n)

    def add(self, t, i, value):
        if t is None:
            t = 'unknown'
        if t not in self.types:
            self.types[t] = TypeInfo(t, self.size, self.total)
        self.types[t].add(i, value)

    def set_total(self, total):
        self.total = total
        for k in self.types:
            self.types[k].total = total

    def most_common(self, n=None):
        if n is None:
            n = len(self.types)
        c = Counter()
        for t in self.types:
            c[t] = self.types[t].count
        return c.most_common(n)


class Strconv(object):
    def __init__(self, converters=[]):
        self.converters = OrderedDict(converters)

    def convert(self, value_str, include_type=False):
        assert isinstance(value_str, basestring)
        for type_name, converter in self.converters.iteritems():
            try:
                value = converter(value_str)
                if include_type:
                    return value, type_name
                else:
                    return value
            except ValueError:
                pass
        if include_type:
            return value_str, None
        else:
            return value_str

    def convert_series(self, series, include_type=False):
        for value_str in series:
            yield self.convert(value_str, include_type=include_type)

    def convert_matrix(self, matrix, include_type=False):
        for row in matrix:
            yield tuple(
                self.convert(value_str, include_type=include_type)
                for value_str in row)

    def infer(self, value_str, astype=False):
        value, type_name = self.convert(value_str, include_type=True)
        if type_name and astype:
            return type(value)
        return type_name

    def infer_series(self, iterable, n=None, size=None):
        info = Types(size=size)
        i = -1

        for i, value in enumerate(iterable):
            if n and i >= n:
                break

            t = self.infer(value)
            info.incr(t)
            info.add(t, i, value)

        i += 1

        # No reason to return type info when no data exists
        if i == 0:
            return

        info.set_total(i)
        return info

    def infer_matrix(self, matrix, n=None, size=None):
        infos = []
        i = -1

        for i, iterable in enumerate(matrix):
            if n and i >= n:
                break

            for j, value in enumerate(iterable):
                if i == 0:
                    infos.append(Types(size=size))
                info = infos[j]

                t = self.infer(value)
                info.incr(t)
                info.add(t, i, value)

        i += 1

        for info in infos:
            info.set_total(i)

        return infos


# Built-in converters

NAN_STRINGS = ['', 'NAN', 'N/A', 'NA', 'NONE']

TIME_FORMATS = (
    '%H:%M:%S',
    '%H:%M',
    '%I:%M:%S %p',
    '%I:%M %p',
    '%I:%M',
)

DATE_TIME_SEPS = (' ', 'T')

true_re = re.compile(r'^(t(rue)?|yes)$', re.I)
false_re = re.compile(r'^(f(alse)?|no)$', re.I)


def convert_int(s):
    return int(s)


def convert_float(s):
    try:
        return float(s)
    except ValueError:
        if s.upper() in NAN_STRINGS:
            return float('nan')
        raise ValueError()


def convert_bool(s):
    if true_re.match(s):
        return True
    if false_re.match(s):
        return False
    raise ValueError


def convert_datetime(s):
    if s == '':
        raise ValueError
    try:
        return duparse(s)
    except TypeError:
        raise ValueError


def convert_date(s):
    return convert_datetime(s).date()


def convert_time(s, time_formats=TIME_FORMATS):
    for f in time_formats:
        try:
            return datetime.strptime(s, f).time()
        except ValueError:
            pass
    raise ValueError


# Initialize default instance and make accessible at the module level
default_strconv = Strconv(converters=[
    ('int', convert_int),
    ('float', convert_float),
    ('bool', convert_bool),
    ('time', convert_time),
    ('datetime', convert_datetime),
    ('date', convert_date),
])

convert = default_strconv.convert
convert_series = default_strconv.convert_series
convert_matrix = default_strconv.convert_matrix

infer = default_strconv.infer
infer_series = default_strconv.infer_series
infer_matrix = default_strconv.infer_matrix
