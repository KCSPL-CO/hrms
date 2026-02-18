frappe.pages['attendance-toolkit'].on_page_load = function(wrapper) {
  var page = frappe.ui.make_app_page({
    parent: wrapper,
    title: 'My Attendance Toolkit',
    single_column: true
  });

  frappe.require('attendance_toolkit.bundle.js', function () {
    wrapper.doc_viewer = new octa.AttendanceToolkit.Controller(wrapper);
    // window.cur_doc_viewer = wrapper.doc_viewer;
  });
}