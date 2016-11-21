# -*- coding: utf-8 -*-

import frappe
from hooks import app_email
from shipment import check_permission
from config.app_config import EMAIL_SIGNATURE
from frappe.email.smtp import get_outgoing_email_account

TEMPLATE_PickedUP = frappe.render_template("templates/email/picked_up.html", {"customer_name": "DEBUGGGGGGGG"})


@check_permission()
@frappe.whitelist()
def send_email_status_update(target_doc, message):
	# message += EMAIL_SIGNATURE
	# source = unicode(TEMPLATE_PickedUP, 'utf-8')
	#yourstring = TEMPLATE_PickedUP.encode('ascii', 'ignore').decode('ascii')
	##print "TEMPLATE_PickedUP = ", yourstring

	frappe.sendmail(recipients="romanchuk.katerina@gmail.com",
		sender=app_email,
		subject="Test",
		message="Test",
		delayed=False)
