
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

         cur_frm.dashboard.add_doctype_badge("Shipment Note", doc.name);
    });

//
//    db = function(doc) {
//        cur_frm.dashboard.reset(doc);
//        if(doc.__islocal)
//            return;
//        if (in_list(user_roles, "Accounts User") || in_list(user_roles, "Accounts Manager"))
//            cur_frm.dashboard.set_headline('<span class="text-muted">'+ __('Loading...')+ '</span>')
//
//        cur_frm.dashboard.add_doctype_badge("Opportunity", "customer");
//        cur_frm.dashboard.add_doctype_badge("Quotation", "customer");
//        cur_frm.dashboard.add_doctype_badge("Sales Order", "customer");
//        cur_frm.dashboard.add_doctype_badge("Delivery Note", "customer");
//        cur_frm.dashboard.add_doctype_badge("Sales Invoice", "customer");
//        cur_frm.dashboard.add_doctype_badge("Project", "customer");
//
//        return frappe.call({
//            type: "GET",
//            method: "erpnext.selling.doctype.customer.customer.get_dashboard_info",
//            args: {
//                customer: cur_frm.doc.name
//            },
//            callback: function(r) {
//                if (in_list(user_roles, "Accounts User") || in_list(user_roles, "Accounts Manager")) {
//                    if(r.message["company_currency"].length == 1) {
//                        cur_frm.dashboard.set_headline(
//                            __("Total Billing This Year: ") + "<b>"
//                            + format_currency(r.message.billing_this_year, r.message["company_currency"][0])
//                            + '</b> / <span class="text-muted">' + __("Unpaid") + ": <b>"
//                            + format_currency(r.message.total_unpaid, r.message["company_currency"][0])
//                            + '</b></span>');
//                    } else {
//                        cur_frm.dashboard.set_headline("");
//                    }
//                }
//                cur_frm.dashboard.set_badge_count(r.message);
//            }
//        });
//    }
