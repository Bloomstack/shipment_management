
# -*- coding: utf-8 -*-


class DocTypeStatus(object):
	Open = 0
	Submitted = 1
	Cancelled = 2


class DeliveryNoteOperationalStatus(object):
	ToBill = "To Bill"
	Completed = "Completed"
	Cancelled = "Cancelled"
	Closed = "Closed"


class ShipmentNoteOperationalStatus(object):
	"""
	Our own Shipment Note statuses
	- In progress – the shipment and its parcels handed to a Delivery Service to pick up and do delivery
	- Completed – successfully delivered to a customer
	- Returned – the shipment returned to Sender by Customer
	- Cancelled – the delivery of the shipment cancelled by Customer
	- Failed – there is an error or physical failure delivering
	"""
	InProgress = "In progress"
	Completed = "Completed"
	Returned = "Returned"
	Cancelled = "Cancelled"
	Failed = "Failed"


class FedexStatusCode(object):
	def __init__(self, status_code, definition):
		self.status_code = status_code
		self.definition = definition


class FedexOperationalStatus(object):
	"""
	ALL STATUSES:
	AA - At Airport
	PL - Plane Landed
	AD - At Delivery
	PM - In Progress
	AF - At FedEx Facility
	PU - Picked Up
	AP - At Pickup
	PX - Picked up (see Details)
	AR - Arrived at
	RR - CDO Requested
	AX - At USPS facility
	RM - CDO Modified
	CA - Shipment Canceled
	RC - CDO Cancelled
	CH - Location Changed
	RS - Return to Shipper
	DD - Delivery Delay
	DE - Delivery Exception
	DL - Delivered
	DP - Departed FedEx Location
	SE - Shipment Exception
	DS - Vehicle dispatched
	SF - At Sort Facility
	DY - Delay
	SP - Split status - multiple statuses
	EA - Enroute to Airport delay
	TR - Transfer
	"""
	Completed = [FedexStatusCode("DL", "Delivered")]
	Canceled = [FedexStatusCode("CA", "Shipment Canceled"),
				FedexStatusCode("DE", "Delivery Exception"),
				FedexStatusCode("SE", "Shipment Exception"),
				FedexStatusCode("RS", "Return to Shipper")]


def get_related_shipment_note():
	shipment_note = None
	return shipment_note


def get_related_fedex_shipment():
	fedex_shipment = None
	return fedex_shipment


def get_related_shipment_package():
	shipment_package = None
	return shipment_package


def _close_delivery_note(shipment_note=None, fedex_shipment=None, shipment_package=None):
	if shipment_note:
		shipment_note.status = DocTypeStatus.Cancelled
		shipment_note.shipment_status = ShipmentNoteOperationalStatus.Cancelled

		shipment_note.save()

	if fedex_shipment:
		fedex_shipment.status = DocTypeStatus.Cancelled
		fedex_shipment.shipment_status = FedexOperationalStatus.Canceled

		fedex_shipment.save()

	if shipment_package:
		shipment_package.status = DocTypeStatus.Cancelled

		shipment_package.save()


def _close_shipment_note(fedex_shipment=None, shipment_package=None):

	if fedex_shipment:
		fedex_shipment.status = DocTypeStatus.Cancelled
		fedex_shipment.shipment_status = FedexOperationalStatus.Canceled

		fedex_shipment.save()

	if shipment_package:
		shipment_package.status = DocTypeStatus.Cancelled

		shipment_package.save()


def delivery_note_status_sync(target_doc=None, status=None):
	shipment_note = get_related_shipment_note()
	fedex_shipment = get_related_fedex_shipment()
	shipment_package = get_related_shipment_package()

	if status == DeliveryNoteOperationalStatus.Completed:
		_close_delivery_note(shipment_note=shipment_note,
							 fedex_shipment=fedex_shipment,
							 shipment_package = shipment_package)

	elif status == DeliveryNoteOperationalStatus.Cancelled:
		_close_delivery_note(shipment_note=shipment_note,
							 fedex_shipment=fedex_shipment,
							 shipment_package = shipment_package)

	elif status == DeliveryNoteOperationalStatus.Closed:
		_close_delivery_note(shipment_note=shipment_note,
							 fedex_shipment=fedex_shipment,
							 shipment_package = shipment_package)

	else:
		raise Exception("Can't mach Delivery Note status = %s (%s)", (target_doc, status))


def shipment_note_status_sync(target_doc, status):
	"""
	Our own Shipment Note statuses
	- In progress – the shipment and its parcels handed to a Delivery Service to pick up and do delivery
	- Completed – successfully delivered to a customer
	- Returned – the shipment returned to Sender by Customer
	- Cancelled – the delivery of the shipment cancelled by Customer
	- Failed – there is an error or physical failure delivering
	"""

	fedex_shipment = get_related_fedex_shipment()
	shipment_package = get_related_shipment_package()

	if status == ShipmentNoteOperationalStatus.Failed:
		_close_shipment_note(fedex_shipment=fedex_shipment,
							 shipment_package = shipment_package)

	elif status == ShipmentNoteOperationalStatus.Cancelled:
		_close_shipment_note(fedex_shipment=fedex_shipment,
							 shipment_package = shipment_package)

	elif status == ShipmentNoteOperationalStatus.Returned:
		_close_shipment_note(fedex_shipment=fedex_shipment,
							 shipment_package = shipment_package)

	elif status == DeliveryNoteOperationalStatus.Completed:
		if fedex_shipment:
			fedex_shipment.status = DocTypeStatus.Submitted
			fedex_shipment.shipment_status = FedexOperationalStatus.Canceled

			fedex_shipment.save()

		if shipment_package:
			shipment_package.status = DocTypeStatus.Cancelled

			shipment_package.save()


def fedex_shipment_status_sync(target_doc, status):
	shipment_note = get_related_shipment_note()
	shipment_package = get_related_shipment_package()

	if status in FedexOperationalStatus.Completed:
		if shipment_note:
			shipment_note.status = DocTypeStatus.Submitted
			shipment_note.shipment_status = ShipmentNoteOperationalStatus.Completed

		if shipment_package:
			shipment_note.status = DocTypeStatus.Submitted

	if status in FedexOperationalStatus.Canceled:
		if shipment_note:
			shipment_note.status = DocTypeStatus.Cancelled
			shipment_note.shipment_status = ShipmentNoteOperationalStatus.Cancelled

		if shipment_package:
			shipment_note.status = DocTypeStatus.Submitted


def send_email_status_update():
	print "email!!!!!"
	
if __name__ == "__main__":
	send_email_status_update()