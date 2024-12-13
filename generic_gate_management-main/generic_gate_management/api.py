import frappe
import traceback
import re

#Purchase Order List
@frappe.whitelist()
def purchase_order_list():
    if frappe.local.request.method=="GET":
        status, message, response = 200, "Success", {}
        purchase_order_list = frappe.get_all("Purchase Order",fields=["name as purchase_order"])
        frappe.local.response.update({"status":status,"message":message,"data":purchase_order_list})
#Sales Invoice List       
@frappe.whitelist()
def sales_invoice_list():
    if frappe.local.request.method=="GET":
        status, message, response = 200, "Success", {}
        purchase_order_list = frappe.get_all("Sales Invoice",fields=["name as sales_invoice"])
        frappe.local.response.update({"status":status,"message":message,"data":purchase_order_list})

#Invite Visitor List
@frappe.whitelist()
def invite_visitor_list():
    if frappe.local.request.method=="GET":
        status, message, response = 200, "Success", {}
        invite_visitor_list = frappe.get_all("Invite Visitor",fields=["name as invite_visitor"])
        frappe.local.response.update({"status":status,"message":message,"data":invite_visitor_list})
       
@frappe.whitelist()
def gate_entry():
    if frappe.local.request.method == 'POST':
        status, message,response = 200, "Gate Entry created successfully.",{}
        
        # Extract form data from `frappe.form_dict`
        po_number = frappe.form_dict.get("po_number")
        vehicle_no = frappe.form_dict.get("vehicle_no")
        vendor_invoice_no = frappe.form_dict.get("vendor_invoice_no")
        amended_from = frappe.form_dict.get("amended_from")
        vendor_invoice_date = frappe.form_dict.get("vendor_invoice_date")
        vendor_invoice_quantity = frappe.form_dict.get("vendor_invoice_quantity")
        invoice_amount = frappe.form_dict.get("invoice_amount")
        gate_entry_date = frappe.form_dict.get("gate_entry_date")
        created_time = frappe.form_dict.get("created_time")
        remarks = frappe.form_dict.get("remarks")
        is_purchase_receipt_created = frappe.form_dict.get("is_purchase_receipt_created")
        by_mobile_app = frappe.form_dict.get("by_mobile_app")                                    
        vendor_invoice_photo = frappe.request.files['vendor_invoice_photo']
        vehicle_photo = frappe.request.files['vehicle_photo']
        
        try:
            # Validate mandatory fields
            mandatory_fields = [po_number, vehicle_no, vendor_invoice_no, vehicle_photo, vendor_invoice_photo, vendor_invoice_date]
            missing_fields = [field for field, value in zip(["po_number", "vehicle_no", "vendor_invoice_no", "vehicle_photo", "vendor_invoice_photo", "vendor_invoice_date"], mandatory_fields) if not value]
                
            if missing_fields:
                status, message = 500, f"Missing mandatory fields: {', '.join(missing_fields)}"
                frappe.local.response.update({'status': status, 'message': message, 'data': response})
                return

            #creating a new record
            gate_entry_doc = frappe.get_doc({
                "doctype": "Gate Entry",
                "po_number":po_number,
                "vehicle_no": vehicle_no,
                "vendor_invoice_no":vendor_invoice_no,
                "amended_from":amended_from,
                "vendor_invoice_date":vendor_invoice_date,
                "vendor_invoice_quantity":vendor_invoice_quantity,
                "invoice_amount":invoice_amount,
                "gate_entry_date":gate_entry_date,
                "created_time":created_time, 
                "remarks":remarks, 
                "vehicle_photo": "",  
                "vendor_invoice_photo": "" , 
                "is_purchase_receipt_created": int(is_purchase_receipt_created),  # Convert to integer if checkbox
                "by_mobile_app": int(by_mobile_app) # Convert to integer if checkbox
            })
            #insert the document
            gate_entry_doc.insert()
            print("gate_entry_doc name:",gate_entry_doc.name)
            print("vendor_invoice_photo:",vendor_invoice_photo,"vehicle_photo:",vehicle_photo)
            
            # Attach vendor invoice photo
            if vendor_invoice_photo:
                vendor_invoice_attachment = frappe.get_doc({
                    "doctype": "File",
                    "file_name": vendor_invoice_photo.filename,
                    "content": vendor_invoice_photo.read(),
                    "attached_to_doctype": "Gate Entry",
                    "attached_to_name": gate_entry_doc.name,
                    "attached_to_field": 'vendor_invoice_photo',
                    "is_private": 0
                })
                vendor_invoice_attachment.insert()
                # Update the created record with the file URL
                gate_entry_doc.vendor_invoice_photo = vendor_invoice_attachment.file_url
                
            # Attach vehicle photo
            if vehicle_photo:
                vehicle_attachment = frappe.get_doc({
                    "doctype": "File",
                    "content": vehicle_photo.read(),
                    "file_name": vehicle_photo.filename,
                    "attached_to_doctype": "Gate Entry",
                    "attached_to_name": gate_entry_doc.name,
                    "attached_to_field": 'vehicle_photo',
                    "is_private": 0
                })
                vehicle_attachment.insert()
                # Update the created record with the file URL
                gate_entry_doc.vehicle_photo = vehicle_attachment.file_url
            
            # Save,Submit the document and commit
            gate_entry_doc.save()
            # gate_entry_doc.submit()     
            frappe.db.commit()
            frappe.local.response.update({'status':status,'message':message,'data':gate_entry_doc.name})
        except Exception as e:
            error_trace = traceback.format_exc()
            frappe.log_error(error_trace, "Gate Entry Creation Error")
            frappe.local.response.update({'status': 500, 'message': f"An error occurred: {str(e)}", 'data': {}})     

@frappe.whitelist()
def gate_exit():
    if frappe.local.request.method == 'POST':
        status, message, response = 200, "Gate Exit created successfully.", {}

        # Extract form data
        sales_invoice_scanner = frappe.form_dict.get("sales_invoice_scanner")
        sales_invoice = frappe.form_dict.get("sales_invoice")
        vehicle_no = frappe.form_dict.get("vehicle_no")
        vehicle_photo = frappe.request.files.get('vehicle_photo')
        amended_from = frappe.form_dict.get("amended_from")
        gate_exit_date = frappe.form_dict.get("gate_exit_date")
        remarks = frappe.form_dict.get("remarks")
        by_mobile_app = frappe.form_dict.get("by_mobile_app")

        try:
            # Validate mandatory fields
            mandatory_fields = [sales_invoice, vehicle_no, vehicle_photo, gate_exit_date]
            missing_fields = [field for field, value in zip(
                ["sales_invoice", "vehicle_no", "vehicle_photo", "gate_exit_date"],
                mandatory_fields) if not value]
            if missing_fields:
                status, message = 400, f"Missing mandatory fields: {', '.join(missing_fields)}"
                frappe.local.response.update({'status': status, 'message': message, 'data': response})
                return

            # Create the Gate Exit document
            gate_exit_doc = frappe.get_doc({
                "doctype": "Gate Exit",
                "sales_invoice_scanner": sales_invoice_scanner,
                "sales_invoice": sales_invoice,
                "vehicle_no": vehicle_no,
                "amended_from": amended_from,
                "gate_exit_date": gate_exit_date,
                "remarks": remarks,
                "by_mobile_app": int(by_mobile_app) if by_mobile_app else 0,
            })

            #insert the document
            gate_exit_doc.insert()
            print("gate_exit_doc:",gate_exit_doc)
            if vehicle_photo:
                vehicle_attachment = frappe.get_doc({
                    "doctype": "File",
                    "content": vehicle_photo.read(),
                    "file_name": vehicle_photo.filename,
                    "attached_to_doctype": "Gate Exit",
                    "attached_to_name": gate_exit_doc.name,
                    "attached_to_field": 'vehicle_photo',
                    "is_private": 0
                })
                vehicle_attachment.insert()
                # Update the created record with the file URL
                gate_exit_doc.vehicle_photo = vehicle_attachment.file_url

            
            # Save,Submit the document and commit
            gate_exit_doc.save()
            # gate_entry_doc.submit()     
            frappe.db.commit()


            response = {
                "gate_exit_name": gate_exit_doc.name,
                "vehicle_photo_file": gate_exit_doc.vehicle_photo
            }

            frappe.local.response.update({'status': status, 'message': message, 'data': response})

        except Exception as e:
            # Log the error and send a response
            error_trace = traceback.format_exc()
            frappe.log_error(error_trace, "Gate Exit Creation Error")
            status, message = 500, f"An error occurred: {str(e)}"
            frappe.local.response.update({'status': status, 'message': message, 'data': {}})


@frappe.whitelist()
def invite_visitor():
    if frappe.local.request.method == 'POST':
        status, message, response = 200, "Visitor invited successfully.", {}

        try:
            # Extract form data
            form_data = frappe.form_dict
            scheduled_date = form_data.get("scheduled_date")
            duration = form_data.get("duration")
            scheduled_time = form_data.get("scheduled_time")
            invite_to_visitor_mobile = form_data.get("invite_to_visitor_mobile")
            invite_to_visitor_email = form_data.get("invite_to_visitor_email")
            multi_visit = form_data.get("multi_visit", 0)
            pass_type = form_data.get("pass_type")
            visitee_mobile = form_data.get("visitee_mobile")
            whom_to_meet = form_data.get("whom_to_meet")
            visitee_email = form_data.get("visitee_email")
            amended_from = form_data.get("amended_from")
            visitor_name = form_data.get("visitor_name")
            visitor_email = form_data.get("visitor_email")
            visitor_mobile = form_data.get("visitor_mobile")
            visitor_company_name = form_data.get("visitor_company_name")
            department = form_data.get("department")

            # Validate mandatory fields
            mandatory_fields = [
                scheduled_date, duration, scheduled_time, pass_type, visitee_mobile, 
                visitor_name, visitor_email, visitor_mobile, whom_to_meet, visitee_email, 
                visitor_company_name, department
            ]
            missing_fields = [field for field, value in zip(
                [
                    "scheduled_date", "duration", "scheduled_time", "pass_type", "visitee_mobile",
                    "visitor_name", "visitor_email", "visitor_mobile", "whom_to_meet", 
                    "visitee_email", "visitor_company_name", "department"
                ],
                mandatory_fields
            ) if not value]
            
            if missing_fields:
                status, message = 400, f"Missing mandatory fields: {', '.join(missing_fields)}"
                frappe.local.response.update({'status': status, 'message': message, 'data': response})
                return
            
            # Convert human-readable duration to seconds
            if 'h' in duration or 'm' in duration:
                duration_seconds = 0
                parts = duration.split()
                for part in parts:
                    if part.endswith('h'):
                        duration_seconds += int(part[:-1]) * 3600
                    elif part.endswith('m'):
                        duration_seconds += int(part[:-1]) * 60
            else:
                duration_seconds = float(duration)
            
            # Validate visitor email
            if not is_valid_email(visitor_email):
                status, message = 400, "Invalid email format for Visitor Email."
                frappe.local.response.update({'status': status, 'message': message, 'data': response})
                return

            # Validate visitee email
            if not is_valid_email(visitee_email):
                status, message = 400, "Invalid email format for Visitee Email."
                frappe.local.response.update({'status': status, 'message': message, 'data': response})
                return

            # Create the Invitation document
            visitor_invite_doc = frappe.get_doc({
                "doctype": "Invite Visitor",
                "scheduled_date": scheduled_date,
                "duration": duration_seconds,
                "scheduled_time": scheduled_time,
                "invite_to_visitor_mobile": int(invite_to_visitor_mobile),
                "invite_to_visitor_email": int(invite_to_visitor_email),
                "multi_visit": int(multi_visit),
                "pass_type": pass_type,
                "visitee_mobile": visitee_mobile,
                "whom_to_meet": whom_to_meet,
                "visitee_email": visitee_email,
                "amended_from": amended_from,
                "visitor_name": visitor_name,
                "visitor_email": visitor_email,
                "visitor_mobile": visitor_mobile,
                "visitor_company_name": visitor_company_name,
                "department": department
            })

            # Insert and commit the document
            visitor_invite_doc.insert()
            frappe.db.commit()

            response = {
                "visitor_invitation_name": visitor_invite_doc.name
            }

            frappe.local.response.update({'status': status, 'message': message, 'data': response})

        except Exception as e:
            # Log the error and send a response
            error_trace = traceback.format_exc()
            frappe.log_error(error_trace, "Visitor Invitation Creation Error")
            status, message = 500, f"An error occurred: {str(e)}"
            frappe.local.response.update({'status': status, 'message': message, 'data': {}})
            
#validate Email
def is_valid_email(email):
    """Validate email format."""
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None


@frappe.whitelist()
def visitor_in_out_register():
    if frappe.local.request.method == 'POST':
        status, message, response = 200, "Visitor in/out register entry created successfully.", {}

        try:
            # Extract form data
            form_data = frappe.form_dict
            qr_scanner = form_data.get("qr_scanner")
            invite_visitor = form_data.get("invite_visitor")
            visit_type = form_data.get("visit_type")
            visitor_name = form_data.get("visitor_name")
            visitor_mobile = form_data.get("visitor_mobile")
            visitor_email = form_data.get("visitor_email")
            amended_from = form_data.get("amended_from")
            
            # Validate visitor_email separately
            if visitor_email and not is_valid_email(visitor_email):
                status, message = 400, "Invalid email format for Visitor Email."
                frappe.local.response.update({'status': status, 'message': message, 'data': response})
                return
            
            # Create the Visitor In/Out Register document
            visitor_in_out_doc = frappe.get_doc({
                "doctype": "Visitor In Out Register",
                "qr_scanner": qr_scanner,
                "invite_visitor": invite_visitor,
                "type": visit_type,
                "visitor_name": visitor_name,
                "visitor_mobile": visitor_mobile,
                "visitor_email": visitor_email,
                "amended_from": amended_from,
            })

            # Insert and commit the document
            visitor_in_out_doc.insert()
            frappe.db.commit()

            response = {
                "visitor_in_out_register_name": visitor_in_out_doc.name
            }

            frappe.local.response.update({'status': status, 'message': message, 'data': response})

        except Exception as e:
            # Log the error and send a response
            error_trace = frappe.get_traceback()
            frappe.log_error(error_trace, "Visitor In/Out Register Error")
            status, message = 500, f"An error occurred: {str(e)}"
            frappe.local.response.update({'status': status, 'message': message, 'data': {}})
  