// Copyright (c) 2016, DigiThinkit Inc. and contributors
// For license information, please see license.txt
// cur_frm.cscript.shipment_note_link = function(doc, cdt, cd){}


frappe.ui.form.on('DTI Fedex Shipment', {

	refresh: function(frm) {

		// frappe.model.set_value(frm.doc.doctype, frm.docname, "shipment_note_link", "test")
		// shipment_note = 'SHIP-00070'
		//shipment_note_doc = create_fedex_shipment()
		//cur_frm.set_value("shipment_note_link", shipment_note_doc.name);
		//cur_frm.refresh_fields("shipment_note_link")
		console.log("Debug:", cur_frm.doc)

		        {
		        if (cur_frm.doc.label_1)
                    {
                    cur_frm.add_custom_button(__('Print label'),
                    function ()
                        {
                           var url = '/labels?name=' + cur_frm.doc.name
                           window.location.assign(url)
                        });
                }
            }
	}

});
