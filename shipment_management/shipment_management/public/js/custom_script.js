
frappe.ui.form.on("Delivery Note",
    {
    refresh:
        function(frm)
        {
		        if (cur_frm.doc.status!="Cancelled" && cur_frm.doc.status!="Closed")
            {
                cur_frm.add_custom_button(__('Shipment'),
                    function ()
                        {
                            frappe.model.open_mapped_doc(
                                {
                                method: "shipment_management.shipment.make_new_shipment_note_from_delivery_note",
                                frm: cur_frm
                                })
                        }, __("Make"));
                }

            }
    });
