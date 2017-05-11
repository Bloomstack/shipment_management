from __future__ import unicode_literals

import frappe
import requests
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
	("FEDEX_2_DAY", "FedEx 2 Day"),
	("FEDEX_EXPRESS_SAVER", "FedEx Express Saver"),
	("FEDEX_GROUND", "FedEx Ground"),
	("FIRST_OVERNIGHT", "FedEx First Class Overnight"),
	("PRIORITY_OVERNIGHT", "FedEx Priority Overnight"),
	("STANDARD_OVERNIGHT", "FedEx Standard Overnight")
)

SERVICE_TYPES_INTERNATIONAL = (
	("INTERNATIONAL_ECONOMY", "FedEx Int. Economy"),
	("INTERNATIONAL_FIRST", "FedEx Int. First Class"),
	("INTERNATIONAL_PRIORITY", "FedEx Int. Priority")
)

def normalize_state(country, state):
	if COUNTRY_STATE_CODES.get('country'):
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
		ShipperStateOrProvinceCode=from_address.get("state"),
		ShipperPostalCode=from_address.get("pincode"),
		ShipperCountryCode=from_country,
		RecipientStateOrProvinceCode=get_state_code(to_address),
		RecipientPostalCode=to_address.get("pincode"),
		RecipientCountryCode=to_country,
		package_list=packages,
		ignoreErrors=True
	)

	rates = get_fedex_packages_rate(**args)
	return sorted(rates, key=lambda rate: rate["fee"])

def get_state_code(address):
	URL = "https://maps.googleapis.com/maps/api/geocode/json?address=" \
	+ " ".join((address.get("city"), address.get("pincode"), address.get("country")))
	r = requests.get(URL)
	data = r.json()
	if data: 
		data = data.get("results")[0].get("address_components")
	for address_component in data:
		if address_component.get("long_name") == address.get("state"):
			return address_component.get("short_name")


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
	print(result)


