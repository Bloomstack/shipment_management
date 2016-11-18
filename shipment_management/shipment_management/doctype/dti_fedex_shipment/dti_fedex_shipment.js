// Copyright (c) 2016, DigiThinkit Inc. and contributors
// For license information, please see license.txt
// cur_frm.cscript.shipment_note_link = function(doc, cdt, cd){}


frappe.ui.form.on('DTI Fedex Shipment', {

	refresh: function(frm) {
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

});
