import unittest
from shipment_management.fedex_status_controller import *


class TestDeliveryNote(unittest.TestCase):
    def test_status_completed(self):
        delivery_note_status_sync(target_doc="", status = DeliveryNoteOperationalStatus.Completed)

        note = get_related_shipment_note()
        package = get_related_shipment_package()
        fedex_shipment = get_related_fedex_shipment()

        self.assertEqual(note.status, DocTypeStatus.Submitted)
        self.assertEqual(note.shipment_status, ShipmentNoteOperationalStatus.Completed)

        self.assertEqual(package.status, DocTypeStatus.Submitted)
        self.assertEqual(package.shipment_status, ShipmentNoteOperationalStatus.Completed)

        self.assertEqual(fedex_shipment.status, DocTypeStatus.Submitted)
        self.assertEqual(fedex_shipment.shipment_status, ShipmentNoteOperationalStatus.Completed)

    def test_status_canceled(self):
        pass

    def test_status_closed(self):
        pass


class TestShipmentNote(unittest.TestCase):
    def test_status_completed(self):
        pass

    def test_status_canceled(self):
        pass

    def test_status_failed(self):
        pass

    def test_status_returned(self):
        pass


class TestFedexShipment(unittest.TestCase):
    def test_status_completed(self):
        pass

    def test_status_canceled(self):
        fedex_shipment_status_sync


if __name__ == '__main__':
      unittest.main()
