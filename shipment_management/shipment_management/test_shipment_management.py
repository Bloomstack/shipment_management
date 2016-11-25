
from __future__ import unicode_literals


import unittest

from shipment_management.shipment import *


class TestCaseAddress(unittest.TestCase):

	def test_recipient(self):
		get_recipient(delivery_note_name='DN-00048')
		get_shipper(delivery_note_name='DN-00048')


if __name__ == '__main__':
	unittest.main()
