import base64
import frappe
from frappe import _
from frappe.utils import cint, nowdate
from frappe.utils.password import get_decrypted_password
import json
from hrms.hr.doctype.leave_allocation.leave_allocation import LeaveAllocation

# ------------------ AUTH ------------------
def authenticate_user():
    """Authenticate using Basic Auth (api_key:api_secret)"""
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
        or get_decrypted_password("User", user.name, "api_secret") != api_secret
    ):
        frappe.local.response["http_status_code"] = 401
        return None

    frappe.set_user(user.name)
    return user


# ------------------ GENERIC PAGINATION ------------------
def paginate_results(doctype, filters=None, fields=None):
    limit_start = cint(frappe.form_dict.get("limit_start", 0))
    raw_limit = frappe.form_dict.get("limit_page_length", 10)
    total = frappe.db.count(doctype, filters=filters)

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

    data = frappe.get_all(
        doctype,
        filters=filters,
        fields=fields or ["*"],
        order_by="creation desc",
        limit_start=limit_start,
        limit_page_length=limit_page_length,
    )

    return {
        "total": total,
        "limit_start": limit_start,
        "applied_limit": limit_page_length,
        "returned_count": len(data),
        "data": data,
    }


# ------------------ LIST LEAVE ALLOCATIONS ------------------
@frappe.whitelist(allow_guest=True)
def list_leave_allocations():
    """Return paginated list of Leave Allocations"""
    if frappe.request.method != "GET":
        frappe.local.response["http_status_code"] = 405
        return {"error": "Only GET method allowed"}

    if not authenticate_user():
        frappe.local.response["http_status_code"] = 401
        return {"error": "Unauthorized"}

    try:
        filters = {}

        employee = frappe.form_dict.get("employee")
        leave_type = frappe.form_dict.get("leave_type")

        if employee:
            filters["employee"] = employee
        if leave_type:
            filters["leave_type"] = leave_type

        result = paginate_results("Leave Allocation", filters=filters)
        frappe.local.response["http_status_code"] = 200
        return result

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Leave Allocation List API Error")
        frappe.local.response["http_status_code"] = 500
        return {"error": str(e)}


# ------------------ CREATE LEAVE ALLOCATION ------------------
@frappe.whitelist(allow_guest=True)
def create_leave_allocation():
    """Create a new Leave Allocation from JSON input"""
    
    if frappe.request.method != "POST":
        frappe.local.response["http_status_code"] = 405
        return {"error": "Only POST method allowed"}

    user = authenticate_user()
    if not user:
        frappe.local.response["http_status_code"] = 401
        return {"error": "Unauthorized"}

    try:
        # Load JSON body
        data = frappe.local.request.get_data(as_text=True)
        data = json.loads(data)

        mandatory_fields = ["employee", "leave_type", "from_date", "to_date"]
        for field in mandatory_fields:
            if not data.get(field):
                frappe.local.response["http_status_code"] = 400
                return {"error": f"Missing required field: {field}"}

        # Create new Leave Allocation
        doc = frappe.new_doc("Leave Allocation")
        doc.employee = data.get("employee")
        doc.leave_type = data.get("leave_type")
        doc.from_date = data.get("from_date")
        doc.to_date = data.get("to_date")
        doc.company = data.get("company") or frappe.defaults.get_user_default("Company")
        doc.carry_forward = cint(data.get("carry_forward", 0))
        doc.allocation_date = data.get("allocation_date") or nowdate()
        doc.notes = data.get("notes")
        doc.description = data.get("description")

        # Handle leave allocation properly
        total_leaves = data.get("total_leaves_allocated")
        new_leaves = data.get("new_leaves_allocated")

        if total_leaves:
            doc.total_leaves_allocated = total_leaves
            doc.new_leaves_allocated = total_leaves  # to satisfy Frappe validation
        elif new_leaves:
            doc.new_leaves_allocated = new_leaves
            doc.total_leaves_allocated = new_leaves
        else:
            frappe.local.response["http_status_code"] = 400
            return {"error": f"Either total_leaves_allocated or new_leaves_allocated must be provided."}

        # Insert and commit
        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        frappe.local.response["http_status_code"] = 201
        return {"message": "Leave Allocation created successfully", "name": doc.name}

    except frappe.ValidationError as ve:
        frappe.local.response["http_status_code"] = 400
        return {"error": str(ve)}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Leave Allocation Create API Error")
        frappe.local.response["http_status_code"] = 500
        return {"error": str(e)}

# ------------------ UPDATE LEAVE ALLOCATION ------------------
@frappe.whitelist(allow_guest=True)
def update_leave_allocation():
    """Update an existing Leave Allocation via JSON body"""
    if frappe.request.method != "PUT":
        frappe.local.response["http_status_code"] = 405
        return {"error": "Only PUT method allowed"}

    user = authenticate_user()
    if not user:
        frappe.local.response["http_status_code"] = 401
        return {"error": "Unauthorized"}

    try:
        # Parse JSON body
        data = frappe.local.request.get_data(as_text=True)
        data = json.loads(data)

        name = data.get("name")
        if not name:
            frappe.local.response["http_status_code"] = 400
            return {"error": "Missing Leave Allocation name"}

        doc = frappe.get_doc("Leave Allocation", name)

        # Update allowed fields
        allowed_fields = [
            "employee", "leave_type", "from_date", "to_date",
            "new_leaves_allocated", "carry_forward", "notes", "description"
        ]

        for key in allowed_fields:
            if key in data:
                setattr(doc, key, data.get(key))

        # Recalculate total leaves allocated
        doc.set_total_leaves_allocated()

        doc.save(ignore_permissions=True)
        frappe.db.commit()

        frappe.local.response["http_status_code"] = 200
        return {"message": f"Leave Allocation {name} updated successfully"}

    except frappe.DoesNotExistError:
        frappe.local.response["http_status_code"] = 404
        return {"error": f"Leave Allocation not found: {name}"}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Leave Allocation Update API Error")
        frappe.local.response["http_status_code"] = 500
        return {"error": str(e)}
# ------------------ GET LEAVE ALLOCATION DETAILS ------------------
@frappe.whitelist(allow_guest=True)
def get_leave_allocation_details():
    """Fetch details of a single Leave Allocation by ID (passed in JSON body)"""
    if frappe.request.method != "POST":
        frappe.local.response["http_status_code"] = 405
        return {"error": "Only POST method allowed"}

    user = authenticate_user()
    if not user:
        frappe.local.response["http_status_code"] = 401
        return {"error": "Unauthorized"}

    try:
        # Parse JSON body
        data = frappe.local.request.get_data(as_text=True)
        data = json.loads(data)

        name = data.get("name") or data.get("id")
        if not name:
            frappe.local.response["http_status_code"] = 400
            return {"error": "Missing required field: name or id"}

        doc = frappe.get_doc("Leave Allocation", name)
        frappe.local.response["http_status_code"] = 200
        return {"data": doc.as_dict()}

    except frappe.DoesNotExistError:
        frappe.local.response["http_status_code"] = 404
        return {"error": f"Leave Allocation not found for ID: {name}"}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Leave Allocation Details API Error")
        frappe.local.response["http_status_code"] = 500
        return {"error": str(e)}
# Submit API
@frappe.whitelist(allow_guest=True)
def submit_leave_allocation():
    """Submit an existing Leave Allocation"""
    
    if frappe.request.method != "POST":
        frappe.local.response["http_status_code"] = 405
        return {"error": "Only POST method allowed"}

    user = authenticate_user()
    if not user:
        frappe.local.response["http_status_code"] = 401
        return {"error": "Unauthorized"}

    try:
        data = frappe.local.request.get_data(as_text=True)
        data = json.loads(data)

        leave_allocation_name = data.get("name")
        if not leave_allocation_name:
            frappe.local.response["http_status_code"] = 400
            return {"error": "Missing required field: name"}

        doc = frappe.get_doc("Leave Allocation", leave_allocation_name)
        doc.submit()
        frappe.db.commit()

        frappe.local.response["http_status_code"] = 200
        return {"message": "Leave Allocation submitted successfully", "name": doc.name}

    except frappe.ValidationError as ve:
        frappe.local.response["http_status_code"] = 400
        return {"error": str(ve)}

    except frappe.PermissionError as pe:
        frappe.local.response["http_status_code"] = 403
        return {"error": str(pe)}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Leave Allocation Submit API Error")
        frappe.local.response["http_status_code"] = 500
        return {"error": str(e)}
    
# ------------------ Generic List API ------------------
def get_list_api(doctype):
    """Generic list API with pagination and auth"""
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

        total = frappe.db.count(doctype)
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

        data = frappe.get_all(
            doctype,
            fields=["*"],
            order_by="creation desc",
            limit_start=limit_start,
            limit_page_length=limit_page_length,
        )

        return {
            "total": total,
            "limit_start": limit_start,
            "applied_limit": limit_page_length,
            "returned_count": len(data),
            "data": data,
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"List API for {doctype}")
        frappe.local.response["http_status_code"] = 500
        return {"error": str(e)}


@frappe.whitelist(allow_guest=True)
def listLeaveType():
    return listLeaveType("Leave Type")
