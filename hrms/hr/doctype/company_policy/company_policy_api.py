import base64
import frappe
import json
from frappe import _
from frappe.utils import cint, now_datetime, nowdate
from frappe.utils.password import get_decrypted_password
from hrms.hr.doctype.policy_acknowledgement.policy_acknowledgement import save_acknowledgement

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


# ------------------ PAGINATION ------------------
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


# ------------------ LIST POLICIES ------------------
@frappe.whitelist(allow_guest=True)
def list_policies():
    """Return paginated list of Company Policies"""
    if frappe.request.method != "GET":
        frappe.local.response["http_status_code"] = 405
        return {"error": "Only GET method allowed"}

    if not authenticate_user():
        frappe.local.response["http_status_code"] = 401
        return {"error": "Unauthorized"}

    try:
        filters = {}
        result = paginate_results(
            "Company Policy",
            fields=[
                "name",
                "effective_date",
                "purpose",
                "eligibility",
                "policy_details",
                "revision_authority",
                "explanation_authority"
            ],
            filters=filters
        )
        frappe.local.response["http_status_code"] = 200
        return result

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Company Policy List API Error")
        frappe.local.response["http_status_code"] = 500
        return {"error": str(e)}


# ------------------ CREATE POLICY ------------------
@frappe.whitelist(allow_guest=True)
def create_policy():
    """Create a new Company Policy from JSON body"""
    if frappe.request.method != "POST":
        frappe.local.response["http_status_code"] = 405
        return {"error": "Only POST method allowed"}

    if not authenticate_user():
        frappe.local.response["http_status_code"] = 401
        return {"error": "Unauthorized"}

    try:
        data = frappe.local.request.get_data(as_text=True)
        data = json.loads(data)

        mandatory_fields = ["effective_date", "purpose", "eligibility", "policy_details"]
        for field in mandatory_fields:
            if not data.get(field):
                frappe.local.response["http_status_code"] = 400
                return {"error": f"Missing required field: {field}"}

        doc = frappe.new_doc("Company Policy")
        doc.effective_date = data.get("effective_date")
        doc.purpose = data.get("purpose")
        doc.eligibility = data.get("eligibility")
        doc.policy_details = data.get("policy_details")
        doc.revision_authority = data.get("revision_authority")
        doc.explanation_authority = data.get("explanation_authority")

        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        frappe.local.response["http_status_code"] = 201
        return {"message": "Policy created successfully", "name": doc.name}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Company Policy Create API Error")
        frappe.local.response["http_status_code"] = 500
        return {"error": str(e)}


# ------------------ POLICY DETAILS ------------------
@frappe.whitelist(allow_guest=True)
def get_policy_details():
    """Fetch details of a single Company Policy by ID (name)"""
    if frappe.request.method != "POST":
        frappe.local.response["http_status_code"] = 405
        return {"error": "Only POST method allowed"}

    if not authenticate_user():
        frappe.local.response["http_status_code"] = 401
        return {"error": "Unauthorized"}

    try:
        data = frappe.local.request.get_data(as_text=True)
        data = json.loads(data)
        policy_name = data.get("name") or data.get("id")

        if not policy_name:
            frappe.local.response["http_status_code"] = 400
            return {"error": "Missing required field: name or id"}

        doc = frappe.get_doc("Company Policy", policy_name)
        frappe.local.response["http_status_code"] = 200
        return {"data": doc.as_dict()}

    except frappe.DoesNotExistError:
        frappe.local.response["http_status_code"] = 404
        return {"error": f"Company Policy not found for ID: {policy_name}"}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Company Policy Details API Error")
        frappe.local.response["http_status_code"] = 500
        return {"error": str(e)}


# ------------------ UPDATE POLICY ------------------
@frappe.whitelist(allow_guest=True)
def update_policy():
    """Update an existing Company Policy via JSON body"""
    if frappe.request.method != "PUT":
        frappe.local.response["http_status_code"] = 405
        return {"error": "Only PUT method allowed"}

    if not authenticate_user():
        frappe.local.response["http_status_code"] = 401
        return {"error": "Unauthorized"}

    try:
        data = frappe.local.request.get_data(as_text=True)
        data = json.loads(data)

        policy_name = data.get("name")
        if not policy_name:
            frappe.local.response["http_status_code"] = 400
            return {"error": "Missing Company Policy name"}

        doc = frappe.get_doc("Company Policy", policy_name)

        allowed_fields = [
            "effective_date",
            "purpose",
            "eligibility",
            "policy_details",
            "revision_authority",
            "explanation_authority"
        ]
        for key in allowed_fields:
            if key in data:
                setattr(doc, key, data.get(key))

        doc.save(ignore_permissions=True)
        frappe.db.commit()

        frappe.local.response["http_status_code"] = 200
        return {"message": f"Company Policy {policy_name} updated successfully"}

    except frappe.DoesNotExistError:
        frappe.local.response["http_status_code"] = 404
        return {"error": f"Company Policy not found: {policy_name}"}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Company Policy Update API Error")
        frappe.local.response["http_status_code"] = 500
        return {"error": str(e)}


# ------------------ SUBMIT POLICY ------------------
@frappe.whitelist(allow_guest=True)
def submit_policy():
    """Submit a Company Policy and create acknowledgement"""
    if frappe.request.method != "POST":
        frappe.local.response["http_status_code"] = 405
        return {"error": "Only POST method allowed"}

    if not authenticate_user():
        frappe.local.response["http_status_code"] = 401
        return {"error": "Unauthorized"}

    try:
        data = frappe.local.request.get_data(as_text=True)
        data = json.loads(data)

        policy_name = data.get("name")
        employee = data.get("employee")
        if not policy_name or not employee:
            frappe.local.response["http_status_code"] = 400
            return {"error": "Missing required field: name or employee"}

        doc = frappe.get_doc("Company Policy", policy_name)
        # Optional: mark as submitted
        if hasattr(doc, "status"):
            doc.status = "Submitted"
            doc.save(ignore_permissions=True)
            frappe.db.commit()

        # Call Policy Acknowledgement API
        save_acknowledgement(policy_name, employee)

        frappe.local.response["http_status_code"] = 200
        return {"message": "Policy submitted and acknowledgement created"}

    except frappe.DoesNotExistError:
        frappe.local.response["http_status_code"] = 404
        return {"error": f"Company Policy not found: {policy_name}"}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Company Policy Submit API Error")
        frappe.local.response["http_status_code"] = 500
        return {"error": str(e)}
