// Copyright (c) 2016, DigiThinkit Inc. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Shipment Rate Settings', {
	refresh: (frm) => {

	}
});

frappe.ui.form.on('Shipment Rate Item Settings', {
	items_add: (frm, cdt, cdn) => {
		// copy the preferred packaging from the first row
		frm.script_manager.copy_from_first_row('items', frm.selected_doc, 'packaging');
	}
});