import base64

import frappe
from frappe.utils import cint
from frappe import _
from frappe.utils import getdate, nowdate
# import json


def authenticate_user():
	auth_header = frappe.get_request_header("Authorization")
	if not auth_header or not auth_header.startswith("Basic "):
		frappe.local.response["http_status_code"] = 401
		return None

	try:
		encoded_token = auth_header.split("Basic ")[1]
		decoded = base64.b64decode(encoded_token).decode("utf-8")
		api_key, api_secret = decoded.split(":")
	except Exception:
		frappe.local.response["http_status_code"] = 401
		return None

	user = frappe.db.get("User", {"api_key": api_key})
	if (
		not user
		or frappe.utils.password.get_decrypted_password("User", user.name, "api_secret") != api_secret
	):
		frappe.local.response["http_status_code"] = 401
		return None

	return user

@frappe.whitelist(allow_guest=True)
def listRecentLeaveApplications():
    if frappe.request.method != "GET":
        frappe.local.response["http_status_code"] = 405
        return {"error": "Only GET method allowed"}

    if not authenticate_user():
        frappe.local.response["http_status_code"] = 401
        return {"error": "Unauthorized"}

    try:
        # Pagination
        limit_start = int(frappe.form_dict.get("limit_start", 0))
        raw_limit = frappe.form_dict.get("limit_page_length", 10)

        total = frappe.db.count("Leave Application")
        if str(raw_limit).lower() in ("0", "all"):
            limit_page_length = total
        else:
            try:
                limit_page_length = int(raw_limit)
            except ValueError:
                limit_page_length = 10

        MAX_LIMIT = 1000
        if limit_page_length > MAX_LIMIT:
            limit_page_length = MAX_LIMIT

        leave_apps = frappe.get_all(
            "Leave Application",
            fields=[
                "name", "employee", "employee_name", "leave_type",
                "from_date", "to_date", "half_day", "half_day_date",
                "status", "total_leave_days", "creation"
            ],
            order_by="creation desc",
            limit_start=limit_start,
            limit_page_length=limit_page_length
        )

        return {
            "total": total,
            "limit_start": limit_start,
            "applied_limit": limit_page_length,
            "returned_count": len(leave_apps),
            "leave_applications": leave_apps
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "List Leave Applications API")
        frappe.local.response["http_status_code"] = 500
        return {"error": str(e)}

@frappe.whitelist(allow_guest=False)
def createLeaveApplication():
    if frappe.request.method != "POST":
        frappe.local.response["http_status_code"] = 405
        return {"error": "Only POST method allowed"}

    if not authenticate_user():
        frappe.local.response["http_status_code"] = 401
        return {"error": "Unauthorized"}

    try:
        data = frappe.request.get_json()

        # Required fields check
        required_fields = ["employee", "leave_type", "from_date", "to_date"]
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            return {"error": f"Missing required fields: {', '.join(missing)}"}

        doc = frappe.new_doc("Leave Application")
        doc.update(data)
        doc.insert(ignore_permissions=True)

        # Save only if status is "Open"
        if data.get("status") == "Open":
            # Only save, do not submit
            frappe.db.commit()
            return {
                "message": "Leave Application saved as Open",
                "name": doc.name,
                "status": doc.status,
                "total_leave_days": getattr(doc, "total_leave_days", None)
            }
        else:
            # Submit for all other statuses
            doc.submit()
            frappe.db.commit()
            return {
                "message": "Leave Application created and submitted successfully",
                "name": doc.name,
                "status": doc.status,
                "total_leave_days": doc.total_leave_days
            }

    except frappe.ValidationError as ve:
        frappe.db.rollback()
        return {"error": str(ve)}

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Create Leave Application API")
        frappe.local.response["http_status_code"] = 500
        return {"error": str(e)}


# Get BY ID
@frappe.whitelist(allow_guest=False)
def getLeaveApplicationById():
    if frappe.request.method != "POST":  # using POST since you want ID in body
        frappe.local.response["http_status_code"] = 405
        return {"error": "Only POST method allowed"}

    if not authenticate_user():
        frappe.local.response["http_status_code"] = 401
        return {"error": "Unauthorized"}

    try:
        data = frappe.request.get_json()
        leave_id = data.get("leave_id")

        if not leave_id:
            return {"error": "leave_id is required in request body"}

        if not frappe.db.exists("Leave Application", leave_id):
            frappe.local.response["http_status_code"] = 404
            return {"error": f"Leave Application {leave_id} not found"}

        doc = frappe.get_doc("Leave Application", leave_id)
        return {"leave_application": doc.as_dict()}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Leave Application API")
        frappe.local.response["http_status_code"] = 500
        return {"error": str(e)}

# UPDATE
@frappe.whitelist(allow_guest=False)
def updateLeaveApplication():
    if frappe.request.method != "POST":
        frappe.local.response["http_status_code"] = 405
        return {"error": "Only POST method allowed"}

    if not authenticate_user():
        frappe.local.response["http_status_code"] = 401
        return {"error": "Unauthorized"}

    try:
        data = frappe.request.get_json()
        leave_id = data.get("leave_id")

        if not leave_id:
            return {"error": "leave_id is required in request body"}

        if not frappe.db.exists("Leave Application", leave_id):
            frappe.local.response["http_status_code"] = 404
            return {"error": f"Leave Application {leave_id} not found"}

        doc = frappe.get_doc("Leave Application", leave_id)

        # Update only fields passed in body (ignore leave_id itself)
        for key, value in data.items():
            if key != "leave_id" and hasattr(doc, key):
                setattr(doc, key, value)

        doc.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "message": f"Leave Application {leave_id} updated successfully",
            "leave_application": doc.as_dict()
        }

    except frappe.ValidationError as ve:
        frappe.db.rollback()
        return {"error": str(ve)}

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Update Leave Application API")
        frappe.local.response["http_status_code"] = 500
        return {"error": str(e)}

# Cancel Leave Application API
@frappe.whitelist(allow_guest=False)
def cancelLeaveApplication():
    if frappe.request.method != "POST":
        frappe.local.response["http_status_code"] = 405
        return {"error": "Only POST method allowed"}

    if not authenticate_user():
        frappe.local.response["http_status_code"] = 401
        return {"error": "Unauthorized"}

    try:
        data = frappe.request.get_json()
        leave_id = data.get("leave_id")

        if not leave_id:
            return {"error": "leave_id is required in request body"}

        if not frappe.db.exists("Leave Application", leave_id):
            frappe.local.response["http_status_code"] = 404
            return {"error": f"Leave Application {leave_id} not found"}

        doc = frappe.get_doc("Leave Application", leave_id)

        if doc.docstatus == 2:
            return {"message": f"Leave Application {leave_id} is already cancelled"}

        # cancel leave
        doc.cancel()
        frappe.db.commit()

        return {"message": f"Leave Application {leave_id} cancelled successfully"}

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Cancel Leave Application API")
        frappe.local.response["http_status_code"] = 500
        return {"error": str(e)}

# Update Leave Application Status API
@frappe.whitelist(allow_guest=False)
def updateLeaveApplicationStatus():
    if frappe.request.method != "POST":
        frappe.local.response["http_status_code"] = 405
        return {"error": "Only POST method allowed"}

    if not authenticate_user():
        frappe.local.response["http_status_code"] = 401
        return {"error": "Unauthorized"}

    try:
        data = frappe.request.get_json()
        leave_id = data.get("leave_id")
        new_status = data.get("status")

        if not leave_id or not new_status:
            return {"error": "Both leave_id and status are required"}

        if not frappe.db.exists("Leave Application", leave_id):
            frappe.local.response["http_status_code"] = 404
            return {"error": f"Leave Application {leave_id} not found"}

        doc = frappe.get_doc("Leave Application", leave_id)

        # check valid statuses
        allowed_status = ["Open", "Approved", "Rejected", "Cancelled"]
        if new_status not in allowed_status:
            return {"error": f"Invalid status. Allowed: {allowed_status}"}

        # update status
        doc.status = new_status

        # if not already submitted, submit the document
        if doc.docstatus == 0:
            doc.submit()
        else:
            doc.save(ignore_permissions=True)

        frappe.db.commit()

        return {
            "message": f"Leave Application {leave_id} updated to {new_status} and submitted",
            "leave_application": doc.as_dict()
        }

    except frappe.ValidationError as ve:
        frappe.db.rollback()
        return {"error": str(ve)}

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Update Leave Application Status API")
        frappe.local.response["http_status_code"] = 500
        return {"error": str(e)}




#Employee List
@frappe.whitelist(allow_guest=False)
def get_employee_list():
    # Only allow GET
    if frappe.request.method != "GET":
        frappe.local.response["http_status_code"] = 405
        return {"error": _("Only GET method allowed")}

    # Optional: use your auth function if required
    if not authenticate_user():
        frappe.local.response["http_status_code"] = 401
        return {"error": _("Unauthorized")}

    try:
        employees = frappe.get_all(
            "Employee",
            filters={"status": "Active"},   # only active employees
            fields=["name", "employee_name", "employee_number", "department", "designation"],
            order_by="employee_name asc"
        )

        return {
            "total": len(employees),
            "employees": employees
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Employee List API")
        frappe.local.response["http_status_code"] = 500
        return {"error": str(e)}






#Employee list  with leave allocation
@frappe.whitelist(allow_guest=False)
def get_leave_allocations_by_employee(employee_id: str):
    # Only allow GET
    if frappe.request.method != "GET":
        frappe.local.response["http_status_code"] = 405
        return {"error": _("Only GET method allowed")}

    # Optional: use your auth function if required
    if not authenticate_user():
        frappe.local.response["http_status_code"] = 401
        return {"error": _("Unauthorized")}

    try:
        if not employee_id:
            return {"error": _("Employee ID is required")}

        today = getdate(nowdate()) # ensure a proper date object

        # Fetch leave allocations
        allocations = frappe.get_all(
            "Leave Allocation",
            filters={"employee": employee_id},
            fields=[
                "name",
                "leave_type",
                "from_date",
                "to_date",
                "new_leaves_allocated",
                "total_leaves_allocated",
                "total_leaves_encashed",
                "leave_period",
                "company"
            ],
            order_by="from_date desc"
        )

        for alloc in allocations:
            # Used Leaves (Approved Applications)
            used = frappe.db.sql("""
                SELECT SUM(total_leave_days) 
                FROM `tabLeave Application` 
                WHERE employee=%s 
                  AND leave_type=%s 
                  AND status='Approved'
            """, (employee_id, alloc["leave_type"]))
            used_leaves = used[0][0] if used and used[0][0] else 0

            # Pending Leaves (Applied / Open Applications)
            pending = frappe.db.sql("""
                SELECT SUM(total_leave_days) 
                FROM `tabLeave Application` 
                WHERE employee=%s 
                  AND leave_type=%s 
                  AND status IN ('Applied','Open')
            """, (employee_id, alloc["leave_type"]))
            pending_leaves = pending[0][0] if pending and pending[0][0] else 0

            # Expired Leaves (if allocation end date passed)
            expired_leaves = 0
            if alloc.get("to_date") and getdate(alloc["to_date"]) < today:
                expired_leaves = (alloc.get("total_leaves_allocated") or 0) - used_leaves

            # Balance = Allocated - Used
            balance = (alloc.get("total_leaves_allocated") or 0) - used_leaves

            # Update dict with new calculated fields
            alloc.update({
                "used_leaves": used_leaves,
                "pending_for_approval": pending_leaves,
                "expired_leaves": expired_leaves,
                "leave_balance": balance
            })

        return {
            "employee": employee_id,
            "leave_allocations": allocations
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Leave Allocations By Employee API")
        frappe.local.response["http_status_code"] = 500
        return {"error": str(e)}