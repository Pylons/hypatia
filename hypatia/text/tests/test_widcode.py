##############################################################################
#
# Copyright (c) 2009 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Text Index Tests
"""
import unittest

_marker = object()

class Test_widcode(unittest.TestCase):

    def test_encode_1_to_7_bits(self):
        from ..widcode import encode
        for wid in xrange(2**7):
            code = encode([wid])
            self.assertEqual(code, chr(wid + 128))

    def test_encode_8_to_14_bits(self):
        from ..widcode import encode
        for wid in xrange(2**7, 2**14):
            hi, lo = divmod(wid, 128)
            code = encode([wid])
            self.assertEqual(code, chr(hi + 128) + chr(lo))

    def test_encode_15_to_21_bits(self):
        from ..widcode import encode
        for wid in xrange(2**14, 2**21, 255):
            mid, lo = divmod(wid, 128)
            hi, mid = divmod(mid, 128)
            code = encode([wid])
            self.assertEqual(code, chr(hi + 128) + chr(mid) + chr(lo))

    def test_encode_22_to_28_bits(self):
        from ..widcode import encode
        STEP = (256 * 512) - 1
        for wid in xrange(2**21, 2**28, STEP):
            lmid, lo = divmod(wid, 128)
            hmid, lmid = divmod(lmid, 128)
            hi, hmid = divmod(hmid, 128)
            code = encode([wid])
            self.assertEqual(code,
                             chr(hi + 128) + chr(hmid) + chr(lmid) + chr(lo))

    def test_decode_zero(self):
        from ..widcode import decode
        self.assertEqual(decode('\x80'), [0])

    def test__decode_other_one_byte_asserts(self):
        from ..widcode import _decode
        for wid in range(1, 128):
            self.assertRaises(AssertionError, _decode, chr(128+wid))

    def test__decode_two_bytes_asserts(self):
        from ..widcode import _decode
        for wid in range(128, 2**14):
            hi, lo = divmod(wid, 128)
            code = chr(hi + 128) + chr(lo)
            self.assertRaises(AssertionError, _decode, code)
                
    def test__decode_three_bytes(self):
        from ..widcode import _decode
        for wid in range(2**14, 2**21, 247):
            mid, lo = divmod(wid, 128)
            hi, mid = divmod(mid, 128)
            code = chr(hi + 128) + chr(mid) + chr(lo)
            self.assertEqual(_decode(code), wid)

    def test__decode_four_bytes(self):
        from ..widcode import _decode
        STEP = (256 * 512) - 7
        for wid in range(2**21, 2**28, STEP):
            lmid, lo = divmod(wid, 128)
            hmid, lmid = divmod(lmid, 128)
            hi, hmid = divmod(hmid, 128)
            code = chr(hi + 128) + chr(hmid) + chr(lmid) + chr(lo)
            self.assertEqual(_decode(code), wid)

    def test_symmetric(self):
        from ..widcode import decode
        from ..widcode import encode
        for wid in xrange(2**14, 2**21, 247):
            wids = [wid]
            code = encode(wids)
            self.assertEqual(decode(code), wids)

