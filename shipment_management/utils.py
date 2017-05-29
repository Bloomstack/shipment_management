import frappe
import requests
from frappe import _

def get_state_code(address):
	URL = "https://maps.googleapis.com/maps/api/geocode/json"
	params = { "address" : " ".join((address.get("pincode", ""),
		address.get("city",
			address.get("state", "")),
				address.get("country", "")))
					}

	r = requests.get(URL, params)
	if r.status_code != 200:
		frappe.throw(_("Error connecting to Google Maps API"))
	
	address_data = r.json().get("results")
	if address_data:
		address_data = address_data[0].get("address_components")
	for address_component in address_data:
		if address_component.get("long_name").lower() == address.get("state").lower():
			# To make sure that state code is either 2 or 3 letters only. 
			# Google API sometimes sends bad data
			if address_component.get("short_name"):
				if len(address_component.get("short_name")) <= 3:
					return address_component.get("short_name")

def get_country_code(country):
	return frappe.get_value("Country", country, "code")
