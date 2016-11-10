// Copyright (c) 2016, DigiThinkit Inc. and contributors
// For license information, please see license.txt
// cur_frm.cscript.shipment_note_link = function(doc, cdt, cd){}

frappe.ui.form.on('DTI Fedex Shipment', {

	refresh: function(frm) {

	    // $("[data-fieldname='shipment_status']", frm.body).css({"font-size": "18px", "color":"orange"})

		//console.log("Before:", frm.doc);
		frappe.model.set_value(frm.doc.doctype, frm.docname, "shipment_note_link", "!!!!!")
		//console.log("After:", frm.doc);
		        {
		        if (cur_frm.doc.label_1)
                    {
                    cur_frm.add_custom_button(__('Print label'),
                    function ()
                        {
//                          window.href='/labels';
//                            window.location.assign('/labels?name=FedexShip-00084')
                            var url = '/labels?name=' + cur_frm.doc.name
                           window.location.assign(url)
                        });
                }

            }
	}
});
