# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import unittest

from wolframclient.serializers import export
from wolframclient.serializers.wxfencoder.serializer import WXFExprSerializer
from wolframclient.serializers.wxfencoder.wxfencoder import DefaultWXFEncoder
from wolframclient.serializers.wxfencoder.wxfexprprovider import (
    WXFExprProvider)
from wolframclient.serializers.wxfencoder.wxfnumpyencoder import (
    NumPyWXFEncoder)
from wolframclient.utils import six
from wolframclient.utils.api import numpy
from wolframclient.utils.tests import TestCase as BaseTestCase


@unittest.skipIf(six.JYTHON, "numpy is not supported in jython")
class TestCase(BaseTestCase):
    @classmethod
    def initDefault(cls):
        return cls.init(True, False)

    @classmethod
    def initBothArraySupport(cls):
        return cls.init(True, True)

    @classmethod
    def initOnlyRA(cls):
        return cls.init(False, True)

    def compare_serializer(self,
                           serializer,
                           array,
                           value,
                           test_round_trip=False):
        serializer.serialize(array)
        self.assertEqual(serializer._writer.getvalue(), value)

        if test_round_trip:
            self.assertEqual(export(array, target_format='wxf'), value)

    @staticmethod
    def init(pa, ra):
        expr_provider = WXFExprProvider()
        numpy_encoder = NumPyWXFEncoder(
            packed_array_support=pa, rawarray_support=ra)

        expr_provider.add_encoder(numpy_encoder)
        expr_provider.add_encoder(DefaultWXFEncoder())
        serializer = WXFExprSerializer(
            six.BytesIO(), expr_provider=expr_provider)
        return serializer

    def test_dimensions(self):
        provider = WXFExprProvider(NumPyWXFEncoder())
        arr = numpy.ndarray([2, 1, 3])
        wxfExpr = next(provider.provide_wxfexpr(arr))
        self.assertEqual(wxfExpr.dimensions, (2, 1, 3))

    def test_zero_dimension(self):
        provider = WXFExprProvider(NumPyWXFEncoder())
        arr = numpy.ndarray([2, 0, 3])
        with self.assertRaises(Exception) as err:
            next(provider.provide_wxfexpr(arr))

        self.assertEqual(
            str(err.exception), "Dimensions must be positive integers.")

    def test_int8_PA(self):

        self.compare_serializer(
            self.initDefault(),
            numpy.array([[-(1 << 7), -1], [1, (1 << 7) - 1]], numpy.int8),
            b'\x38\x3a\xc1\x00\x02\x02\x02\x80\xff\x01\x7f')

    def test_int8_Both(self):

        self.compare_serializer(
            self.initBothArraySupport(),
            numpy.array([[-(1 << 7), -1], [1, (1 << 7) - 1]], numpy.int8),
            b'\x38\x3a\xc1\x00\x02\x02\x02\x80\xff\x01\x7f')

    def test_int8_RA(self):

        self.compare_serializer(
            self.initOnlyRA(),
            numpy.array([[-(1 << 7), -1], [1, (1 << 7) - 1]], numpy.int8),
            b'\x38\x3a\xc2\x00\x02\x02\x02\x80\xff\x01\x7f',
            test_round_trip=True)

    def test_int16(self):
        s = self.initDefault()
        sRA = self.initOnlyRA()
        arr = arr = numpy.array([[-(1 << 15)], [(1 << 15) - 1]], numpy.int16)

        self.compare_serializer(s, arr,
                                b'8:\xc1\x01\x02\x02\x01\x00\x80\xff\x7f')
        self.compare_serializer(
            sRA,
            arr,
            b'8:\xc2\x01\x02\x02\x01\x00\x80\xff\x7f',
            test_round_trip=True)

    def test_int32(self):

        arr = numpy.array([[-(1 << 31)], [(1 << 31) - 1]], numpy.int32)

        self.compare_serializer(
            self.initDefault(), arr,
            b'8:\xc1\x02\x02\x02\x01\x00\x00\x00\x80\xff\xff\xff\x7f')
        self.compare_serializer(
            self.initOnlyRA(),
            arr,
            b'8:\xc2\x02\x02\x02\x01\x00\x00\x00\x80\xff\xff\xff\x7f',
            test_round_trip=True)

    def test_int64(self):

        arr = numpy.array([[-(1 << 62)], [(1 << 62)]], numpy.int64)
        self.compare_serializer(
            self.initDefault(), arr,
            b'8:\xc1\x03\x02\x02\x01\x00\x00\x00\x00\x00\x00\x00\xc0\x00\x00\x00\x00\x00\x00\x00@'
        )
        self.compare_serializer(
            self.initOnlyRA(), arr,
            b'8:\xc2\x03\x02\x02\x01\x00\x00\x00\x00\x00\x00\x00\xc0\x00\x00\x00\x00\x00\x00\x00@'
        )

    def test_uint8_PA(self):

        self.compare_serializer(
            self.initDefault(), numpy.array([[0, (1 << 7)]], numpy.uint8),
            b'\x38\x3a\xc1\x01\x02\x01\x02\x00\x00\x80\x00')

    def test_uint8_RA(self):

        self.compare_serializer(self.initBothArraySupport(),
                                numpy.array([0, (1 << 8) - 1], numpy.uint8),
                                b'8:\xc2\x10\x01\x02\x00\xff')

    def test_uint16_RA(self):

        self.compare_serializer(self.initBothArraySupport(),
                                numpy.array([0, (1 << 16) - 1], numpy.uint16),
                                b'8:\xc2\x11\x01\x02\x00\x00\xff\xff')

    def test_uint32_RA(self):

        self.compare_serializer(
            self.initBothArraySupport(),
            numpy.array([0, (1 << 32) - 1], numpy.uint32),
            b'8:\xc2\x12\x01\x02\x00\x00\x00\x00\xff\xff\xff\xff')

    def test_uint64_RA(self):

        self.compare_serializer(
            self.initBothArraySupport(),
            numpy.array([0, (1 << 64) - 1], numpy.uint64),
            b'8:\xc2\x13\x01\x02\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff'
        )

    def test_bad_options(self):
        with self.assertRaises(ValueError):
            NumPyWXFEncoder(packed_array_support=False, rawarray_support=False)
