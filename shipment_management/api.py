from __future__ import unicode_literals

import frappe
from provider_fedex import get_fedex_packages_rate
from country_code_config import COUNTRY_STATE_CODES

VALID_PACKAGING_TYPES = (
	"FEDEX_10KG_BOX",
	"FEDEX_25KG_BOX",
	"FEDEX_BOX",
	"FEDEX_ENVELOPE",
	"FEDEX_PAK",
	"FEDEX_TUBE",
	"YOUR_PACKAGING"
)

SERVICE_TYPES = (
	"FEDEX_2_DAY",
	"FEDEX_EXPRESS_SAVER",
	"FEDEX_GROUND",
	"FIRST_OVERNIGHT",
	"PRIORITY_OVERNIGHT",
	"STANDARD_OVERNIGHT"
)

SERVICE_TYPES_INTERNATIONAL = (
	"INTERNATIONAL_ECONOMY",
	"INTERNATIONAL_FIRST",
	"INTERNATIONAL_PRIORITY"
)

def normalize_state(country, state):
	for name, abbr in COUNTRY_STATE_CODES[country].iteritems():
		if name.upper() == state.upper():
			return abbr.upper()

	return state

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

	from_country = frappe.get_value("Country", from_address.get("country"), "code")
	to_country = frappe.get_value("Country", to_address.get("country"), "code")

	args = dict(
		DropoffType='REGULAR_PICKUP',
		PackagingType=packaging_type,
		EdtRequestType='NONE',
		PaymentType='SENDER',
		ShipperStateOrProvinceCode=normalize_state(to_address.get("country"), to_address.get("state")),
		ShipperPostalCode=to_address.get("pincode"),
		ShipperCountryCode=to_country,
		RecipientStateOrProvinceCode=normalize_state(from_address.get("country"), from_address.get("state")),
		RecipientPostalCode=from_address.get("pincode"),
		RecipientCountryCode=from_country,
		package_list=packages
	)

	rates = {}
	services = list()
	services += SERVICE_TYPES

	if from_country != to_country:
		services += SERVICE_TYPES_INTERNATIONAL

	for serviceType in services:
		try:
			args["ServiceType"] = serviceType
			rate = get_fedex_packages_rate(**args)
			rates[serviceType] = rate
		except Exception as ex:
			print(ex)

	return rates


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
		"weight_units":"LB"},
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
	print(result)
