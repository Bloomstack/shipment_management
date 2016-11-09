// Copyright (c) 2016, DigiThinkit Inc. and contributors
// For license information, please see license.txt

frappe.ui.form.on('DTI Fedex Shipment', {
	refresh: function(frm) {
		console.log(frm);
		        {
		        if (cur_frm.doc.label_1)
                    {
                    cur_frm.add_custom_button(__('Print label'),
                    function ()
                        {
                          window.href='/labels';
                        });
                }

            }
	}
});
