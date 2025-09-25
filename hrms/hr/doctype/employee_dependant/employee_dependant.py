import frappe
from frappe.model.document import Document

class EmployeeDependant(Document):
    def before_insert(self):
        self.set_gender_from_relation()

    def validate(self):
        self.set_gender_from_relation()

    def set_gender_from_relation(self):
        if self.relationship:
            gender = frappe.db.get_value("Relation", self.relationship, "gender")
            if gender:
                self.gender = gender
