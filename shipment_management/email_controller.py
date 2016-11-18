import frappe
from frappe import _
from shipment import check_permission
from hooks import app_email


@check_permission()
@frappe.whitelist()
def send_email_status_update(target_doc):

	message = """Good day!
	Shipment status was changed from {} to {}!
	Thank you!""".format(target_doc.name, target_doc)

	frappe.sendmail(recipients="romanchuk.katerina@gmail.com",
		sender=app_email,
		subject="Status update for shipment [{}]on {}".format(target_doc.name, frappe.local.site),
		message=message,
		delayed=False)