import frappe
from frappe.utils import today
import json
import base64
from frappe.utils.password import get_decrypted_password
from frappe.utils import getdate, today
 
# --------------------------
# Authentication Method
# --------------------------
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
    if not user:
        frappe.local.response["http_status_code"] = 401
        return None
 
    real_secret = get_decrypted_password("User", user.name, "api_secret")
    if real_secret != api_secret:
        frappe.local.response["http_status_code"] = 401
        return None
 
    return user

@frappe.whitelist(allow_guest=True)
def get_all_job_requisition():
    if frappe.request.method != "GET":
        frappe.local.response["http_status_code"] = 405
        return {"error": "Method Not Allowed. Use GET."}
 
    if not authenticate_user():
        return {"message": "Unauthorized", "success": False}
 
    claims = frappe.get_all("Job Requisition", fields=["*"])
    return claims


@frappe.whitelist(allow_guest=False)
def get_company_list():
    if frappe.request.method != "GET":
        frappe.local.response["http_status_code"] = 405
        return {"error": "Method Not Allowed. Use GET."}

    if not authenticate_user():
        return {"message": "Unauthorized", "success": False}
    filters = {}
    designations = frappe.get_all(
        "Company",
        fields=["*"],
        filters=filters,
        # order_by="designation asc",
    )
    return {
        "success": True,
        "data": designations,
    }

@frappe.whitelist(allow_guest=False)
def get_designation_options():
    if frappe.request.method != "GET":
        frappe.local.response["http_status_code"] = 405
        return {"error": "Method Not Allowed. Use GET."}

    if not authenticate_user():
        return {"message": "Unauthorized", "success": False}
    filters = {}
    designations = frappe.get_all(
        "Designation",
        fields=["*"],
        filters=filters,
        # order_by="designation asc",
    )
    return {
        "success": True,
        "data": designations,
    }


@frappe.whitelist(allow_guest=False)
def get_department_list():
    if frappe.request.method != "GET":
        frappe.local.response["http_status_code"] = 405
        return {"error": "Method Not Allowed. Use GET."}
    if not authenticate_user():
        return {"message": "Unauthorized", "success": False}
    filters = {}
    designations = frappe.get_all(
        "Department",
        fields=["*"],
        filters=filters,
    )
    return {
        "success": True,
        "data": designations,
    }


@frappe.whitelist(allow_guest=False)
def get_requestedBy_list():
    if frappe.request.method != "GET":
        frappe.local.response["http_status_code"] = 405
        return {"error": "Method Not Allowed. Use GET."}
    if not authenticate_user():
        return {"message": "Unauthorized", "success": False}
    filters = {}
    designations = frappe.get_all(
        "Employee",
        fields=["*"],
        filters=filters,

    )
    return {
        "success": True,
        "data": designations,
    }


@frappe.whitelist(allow_guest=False)
def create_job_requisition():
    if frappe.request.method != "POST":
        frappe.local.response["http_status_code"] = 405
        return {"error": "Method Not Allowed. Use POST."}
    if not authenticate_user():
        return {"message": "Unauthorized", "success": False}
    try:
        data = json.loads(frappe.request.data or "{}")
        doc = frappe.new_doc("Job Requisition")
        print("the data ", data)
        field_mapping = {
            "no_of_positions": "no_of_positions",
            "company": "company",
            "designation": "designation",
            "expected_compensation": "expected_compensation",
            "status": "status",
            "department": "department",
            "requested_by": "requested_by",
            "posting_date": "posting_date",
            "expected_by": "expected_by",
            "description":"description"
        }
        for frontend_key, doctype_field in field_mapping.items():
            if frontend_key in data:
                doc.set(doctype_field, data[frontend_key])
        doc.insert()
        frappe.db.commit()
        return {
            "success": True,
            "message": "Job Requisition created",
            "name": doc.name,
        }   
    except Exception as e:
        frappe.local.response["http_status_code"] = 500
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist(allow_guest=True)
def get_job_requisition(name):
    if frappe.request.method != "GET":
        frappe.local.response["http_status_code"] = 405
        return {"error": "Method Not Allowed. Use GET."}
    if not authenticate_user():
        frappe.local.response["http_status_code"] = 401
        return {"message": "Unauthorized", "success": False}
    if not frappe.db.exists("Job Requisition", name):
        frappe.local.response["http_status_code"] = 404
        return {"error": "Job Requisition not found"}
    doc = frappe.get_doc("Job Requisition", name)
    return {
        "success": True,
        "data": doc.as_dict(),
    }

@frappe.whitelist(allow_guest=False)
def update_job_requisition():
    if frappe.request.method != "POST":
        frappe.local.response["http_status_code"] = 405
        return {"error": "Method Not Allowed. Use POST."}
    if not authenticate_user():
        return {"message": "Unauthorized", "success": False}
    try:
        data = json.loads(frappe.request.data or "{}")
        name = data.get("name")
        if not name:
            frappe.local.response["http_status_code"] = 400
            return {"error": "Missing required field: name"}
        if not frappe.db.exists("Job Requisition", name):
            frappe.local.response["http_status_code"] = 404
            return {"error": "Job Requisition not found"}
        doc = frappe.get_doc("Job Requisition", name)
        data.pop("name", None)
        for key, value in data.items():
            if key in doc.as_dict():
                doc.set(key, value)
        doc.save()
        frappe.db.commit()
        return {
            "success": True,
            "message": "Job Requisition updated",
            "name": doc.name,
        }
    except Exception as e:
        frappe.local.response["http_status_code"] = 500
        return {
            "success": False,
            "error": str(e)
        }
    

