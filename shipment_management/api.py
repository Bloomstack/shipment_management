from __future__ import unicode_literals

import frappe
from provider_fedex import get_fedex_packages_rate
from utils import get_state_code, get_country_code
from shipment_management.doctype.shipping_package_rule.shipping_package_rule import find_packages

VALID_PACKAGING_TYPES = (
	"FEDEX_10KG_BOX",
	"FEDEX_25KG_BOX",
	"FEDEX_BOX",
	"FEDEX_ENVELOPE",
	"FEDEX_PAK",
	"FEDEX_TUBE",
	"YOUR_PACKAGING"
)

def get_rates(from_address, to_address, items, packaging_type="YOUR_PACKAGING"):
	"""Simple wrapper over fedex rating service.
	It takes the standard address field values for the from_ and to_ addresses
	to keep a consistent address api. Packaging is a list of items with only
	two foe;d requirements "item_code" and "qty". """

	packages = find_packages(items)

	# to try and keep some form of standardization we'll minimally  require
	# a weight_value. Any other values will be passed as is to the rates service.
	surcharge = 0
	for package in packages:
		if package.get("weight_value", None) is None or \
		   package.get("weight_units", None) is None:
			raise frappe.exceptions.ValidationError("Missing weight_value data")

		if not package.get("group_package_count"):
			package["group_package_count"] = 1

		if not package.get("insured_amount"):
			package["insured_amount"] = 0

		if not package.get("physical_packaging"):
			package["physical_packaging"] = "BOX"

		surcharge = surcharge + package.get("surcharge", 0)

	args = dict(
		DropoffType='REGULAR_PICKUP',
		PackagingType=packaging_type,
		EdtRequestType='NONE',
		PaymentType='SENDER',
		ShipperStateOrProvinceCode=get_state_code(from_address),
		ShipperPostalCode=from_address.get("pincode"),
		ShipperCountryCode=get_country_code(from_address.get("country")),
		RecipientStateOrProvinceCode=get_state_code(to_address),
		RecipientPostalCode=to_address.get("pincode"),
		RecipientCountryCode=get_country_code(to_address.get("country")),
		package_list=packages,
		ignoreErrors=True
	)

	rates = get_fedex_packages_rate(**args)
	sorted_rates = []
	for rate in sorted(rates, key=lambda rate: rate["fee"]):
		rate["fee"] = rate["fee"] + surcharge
		sorted_rates.append(rate)

	return sorted_rates
