from __future__ import unicode_literals

import frappe
from provider_fedex import get_fedex_packages_rate
from utils import get_state_code, get_country_code

VALID_PACKAGING_TYPES = (
	"FEDEX_10KG_BOX",
	"FEDEX_25KG_BOX",
	"FEDEX_BOX",
	"FEDEX_ENVELOPE",
	"FEDEX_PAK",
	"FEDEX_TUBE",
	"YOUR_PACKAGING"
)


def get_rates(from_address, to_address, packages, packaging_type="YOUR_PACKAGING"):
	"""Simple wrapper over fedex rating service.
	It takes the standard address field values for the from_ and to_ addresses
	to keep a consistent address api. Packaging is a list of objects with only
	one requirement "weight_value" though for the fexed api there are other fields
	to include"""

	# to try and keep some form of standardization we'll minimally  require
	# a weight_value. Any other values will be passed as is to the rates service.
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
	return sorted(rates, key=lambda rate: rate["fee"])


def test_rates_api():
	from_address = dict(
		state="FLORIDA",
		pincode="32803",
		country="United States"
	)

	to_address = dict(
		state="FLORIDA",
		pincode="32801",
		country="United States"
	)

	packages = [
		{"weight_value": 100,
		 "weight_units": "LB"},
		#"physical_packaging":"BOX"},
		#"group_package_count": 1,
		#"insured_amount":1000},
		{"weight_value": 2,
		"weight_units":"LB"}
		#"physical_packaging":"BOX"}
		#"group_package_count":2,
		#"insured_amount":100}
	]

	result = get_rates(from_address, to_address, packages)