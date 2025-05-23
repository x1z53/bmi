# window.py
#
# Copyright 2024 philipp
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# SPDX-License-Identifier: GPL-2.0-or-later

# Imports
from gi.repository import Adw, Gtk, Gdk, Gio
import math

# Shorthand vars
app_id = "io.github.philippkosarev.bmi"
# Alignment
start = Gtk.Align.START
end = Gtk.Align.END
center = Gtk.Align.CENTER
fill = Gtk.Align.FILL
# Orientations
horizontal = Gtk.Orientation.HORIZONTAL
vertical = Gtk.Orientation.VERTICAL

class BmiWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'BmiWindow'
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Loading GSettings and connecting action after closing the app window
        self.settings = Gio.Settings.new_with_path(app_id, "/io/github/philippkosarev/bmi/")
        self.connect("close-request", self.on_close_window)

        # Basic window properties
        self.set_title("BMI")
        self.set_default_size(0, 230)
        self.set_resizable(False)

        # Start of the widget structure
        self.content = Adw.ToolbarView()
        self.set_content(self.content)

        # Headerbar
        self.header = Adw.HeaderBar()
        self.content.add_top_bar(self.header)
        # About button
        self.about_button = Gtk.Button(icon_name="help-about-symbolic")
        self.about_button.set_tooltip_text(_("Show About"))
        self.about_button.connect('clicked', self.show_about)
        self.header.pack_end(self.about_button)
        # Mode dropdown
        self.mode_dropdown = Gtk.DropDown()
        modes_list = Gtk.StringList()
        modes = ["BMI (Basic)", "BMI (Advanced)"]
        for mode in modes:
            modes_list.append(mode)
        self.mode_dropdown.set_model(modes_list)
        self.mode_dropdown.set_selected(self.settings["mode"])
        self.mode_dropdown.connect('notify::selected-item', self.on_dropdown_value_changed)
        self.mode_dropdown.get_first_child().set_css_classes(["flat"])
        self.header.set_title_widget(self.mode_dropdown)
        # Metric/Imperial button
        self.units_button = Gtk.ToggleButton(icon_name="ruler-angled-symbolic")
        self.units_button.set_active(self.settings["imperial"])
        self.units_button.connect('toggled', self.on_units_button)
        self.units_button.set_tooltip_text(_("Switch to imperial units"))
        self.header.pack_start(self.units_button)
        # Forget button
        self.forget_button = Gtk.ToggleButton(icon_name="user-trash-full-symbolic")
        self.forget_button.set_active(self.settings["forget"])
        self.forget_button.set_tooltip_text(_("Forget input values after closing"))
        self.header.pack_start(self.forget_button)

        # WindowHandle to make the whole window draggable
        self.drag = Gtk.WindowHandle()
        self.content.set_content(self.drag)
        # Toast overlay layer
        self.toast_overlay = Adw.ToastOverlay()
        self.drag.set_child(self.toast_overlay)
        # Main box
        self.main_box = Gtk.Box(valign=center)
        self.main_box.set_margin_start(16)
        self.main_box.set_margin_end(16)
        self.main_box.set_margin_bottom(16)
        self.toast_overlay.set_child(self.main_box)

        # Basic inputs root page
        self.inputs_page = Adw.PreferencesPage(halign=center)
        self.inputs_page.set_hexpand(True)
        self.inputs_page.set_vexpand(True)
        self.inputs_page.set_size_request(300, 170)
        self.main_box.append(self.inputs_page)
        # Basic inputs group
        self.inputs_group = Adw.PreferencesGroup(title=_("Inputs"))
        self.inputs_page.add(self.inputs_group)
        # Height input row
        self.height_adjustment = Gtk.Adjustment(lower=50, upper=267, step_increment=1, page_increment=10)
        self.create_input_row("height_input_row", _("Height"), self.height_adjustment, 1, "Affects BMI and BRI", False)
        # Weight input row
        self.weight_adjustment = Gtk.Adjustment(lower=10, upper=650, step_increment=1, page_increment=10)
        self.create_input_row("weight_input_row", _("Weight"), self.weight_adjustment, 1, "Affects BMI", False)

        # Advanced inputs root page
        self.advanced_inputs_page = Adw.PreferencesPage(halign=center)
        self.advanced_inputs_page.set_hexpand(True)
        self.advanced_inputs_page.set_vexpand(True)
        self.advanced_inputs_page.set_size_request(300, 330)
        self.main_box.append(self.advanced_inputs_page)
        # Advanced input group
        self.advanced_inputs_group = Adw.PreferencesGroup(title=_("Advanced inputs"))
        self.advanced_inputs_page.add(self.advanced_inputs_group)
        # Gender input row
        self.gender_adjustment = Adw.ComboRow(title=_("Gender"))
        self.gender_adjustment.set_tooltip_text(_("Affects healthy/unhealthy thresholds for Waist to Hip ratio"))
        gender_list = Gtk.StringList()
        self.gender_adjustment.set_model(gender_list)
        genders = [_("Average"), _("Female"), _("Male")]
        for gender in genders:
            gender_list.append(gender)
        self.gender_adjustment.set_selected(self.settings["gender"])
        self.gender_adjustment.connect('notify::selected-item', self.on_dropdown_value_changed)
        self.advanced_inputs_group.add(self.gender_adjustment)
        # Age input row
        self.age_adjustment = Gtk.Adjustment(lower=18, upper=123, step_increment=1, page_increment=10)
        self.create_input_row("age_input_row", _("Age"), self.age_adjustment, 0, _("Affects healthy/unhealthy thresholds for Waist to Height ratio"), True)
        self.age_input_row.set_subtitle("Years")
        # Waist circumference input row
        self.waist_adjustment = Gtk.Adjustment(lower= 25, upper=650, step_increment=1, page_increment=10)
        self.create_input_row("waist_input_row", _("Waist"), self.waist_adjustment, 1, _("Affects Waist to Height ratio, Waist to Hip ratio and BRI"), True)
        # Hip circumference input row
        self.hip_adjustment = Gtk.Adjustment(lower= 25, upper=650, step_increment=1, page_increment=10)
        self.create_input_row("hip_input_row", _("Hip"), self.hip_adjustment, 1, _("Affects Waist to Hip ratio"), True)

        # Arrow icon
        self.icon = Gtk.Image(icon_name="go-next-symbolic", pixel_size=32)
        self.icon.set_margin_start(24)
        self.main_box.append(self.icon)

        # Simple results root box
        self.right_box = Gtk.Box(orientation=vertical, valign=center, spacing=6)
        self.right_box.set_size_request(190, 0)
        self.right_box.set_margin_start(8)
        self.right_box.set_margin_end(8)
        self.main_box.append(self.right_box)
        # 'BMI:' label
        self.result_label = Gtk.Label(label=_("BMI:"))
        self.result_label.add_css_class("title-2")
        self.right_box.append(self.result_label)
        # The button which shows the BMI number
        self.bmi_button = Gtk.Button(halign=center)
        self.bmi_button.set_tooltip_text(_("Copy BMI"))
        self.bmi_button.set_css_classes(["pill", "title-1"])
        self.bmi_button.connect('clicked', self.clipboard_copy)
        self.bmi_button.set_size_request(110, 0)
        self.right_box.append(self.bmi_button)
        # The label which shows feedback (Underweight/Overweight)
        self.result_feedback_label = Gtk.Label()
        self.result_feedback_label.add_css_class("title-2")
        self.right_box.append(self.result_feedback_label)

        # Advanced results root page
        self.right_page = Adw.PreferencesPage(halign=center)
        self.right_page.set_size_request(300, 330)
        self.right_page.set_margin_start(24)
        self.main_box.append(self.right_page)
        # Advanced results group
        self.right_group = Adw.PreferencesGroup(title=_("Results"))
        self.right_page.add(self.right_group)
        # Result rows
        self.create_result_row("result_bmi_row", "BMI", _("Body Mass Index"))
        self.create_result_row("result_waist_to_height_row", _("Waist / Height"), _("Waist to height ratio"))
        self.create_result_row("result_waist_to_hip_row", _("Waist / Hip"), _("Waist to hip ratio"))
        self.create_result_row("result_bri_row", _("BRI"), _("Body Roundness Index"))

        # Setting values for input rows
        self.height_input_row.set_value(self.settings["height"])
        self.weight_input_row.set_value(self.settings["mass"])
        self.waist_input_row.set_value(self.settings["waist"])
        self.hip_input_row.set_value(self.settings["hip"])
        self.age_input_row.set_value(self.settings["age"])

        # Connecting input rows
        self.distance_rows = [self.height_input_row, self.waist_input_row, self.hip_input_row]
        self.mass_rows = [self.weight_input_row]
        self.metrics_rows = self.distance_rows + self.mass_rows
        for row in self.metrics_rows:
            row.connect('changed', self.on_input_changed)
        # Updating all
        self.update_all()
        # Switching to imperial if needed
        if self.imperial:
            self.on_units_button(self)

    def update_all(self):
        self.update_inputs()
        self.update_results()
        self.update_result_labels()
        self.update_mode()
        self.update_units_labels()

    def update_inputs(self):
        # Getting relevant values
        self.imperial = self.units_button.get_active()
        self.height = self.height_input_row.get_value()
        self.mass = self.weight_input_row.get_value()
        self.waist = self.waist_input_row.get_value()
        self.hip = self.hip_input_row.get_value()
        self.gender = self.gender_adjustment.get_selected_item().get_string()
        self.age = self.age_input_row.get_value()
        # Converting imperial to metric
        if self.imperial:
            self.height = self.in_to_cm(self.height)
            self.mass = self.lb_to_kg(self.mass)
            self.waist = self.in_to_cm(self.waist)
            self.hip = self.in_to_cm(self.hip)

        self.height_input_row.set_title(_("Height"))
        self.weight_input_row.set_title(_("Weight"))
        if self.height == 267:
            self.height_input_row.set_title("Robert Wadlow")
        if self.mass == 650:
            self.weight_input_row.set_title("Jon Brower Minnoch")

    def update_results(self):
        # Calculating BMI
        self.bmi = self.mass / ((self.height / 100) ** 2)
        # Calculating Waist to Height ratio
        self.waist_to_height = self.waist / self.height
        # Calculating Waist to Hip ratio
        self.waist_to_hip = self.waist / self.hip
        # Calculating BRI
        try:
            self.bri = 364.2 - (365.5 * math.sqrt((1 - (self.waist / (math.pi * self.height)) ** 2)))
        except:
            self.bri = 0
        # Sometimes '1 - (self.waist / (math.pi * self.height)' < 0 so sqrt() errors out

    # Hides or shows simple and advanced input and output widgets depending on the selected mode
    def update_mode(self):
        if self.mode_dropdown.get_selected() == 0:
            self.advanced_inputs_page.set_visible(False)
            self.right_page.set_visible(False)
            self.right_box.set_visible(True)
            self.inputs_group.set_title("")
        else:
            self.advanced_inputs_page.set_visible(True)
            self.right_page.set_visible(True)
            self.right_box.set_visible(False)
            self.inputs_group.set_title(_("Inputs"))

    # Action, called after value of self.height_input_row or other inputs changes
    def on_input_changed(self, _scroll):
        self.update_inputs()
        self.update_results()
        self.update_result_labels()

    # Action, called after value of self.mode_dropdown changes
    def on_dropdown_value_changed(self, dropdown, _pspec):
        self.update_mode()
        self.update_results()

    # Called by self.units_button
    def on_units_button(self, _button):
        self.update_inputs()
        self.convert_inputs()
        self.update_units_labels()
        self.update_results()
        self.update_result_labels()

    # Changes input rows' subtitles to cm/kg or in/ft
    def update_units_labels(self):
        # Setting vars
        if self.imperial is False:
            distance = _("Centimetres")
            mass = _("Kilograms")
        else:
            distance = _("Inches")
            mass = _("Pounds")
        # Setting subtitles
        for row in self.distance_rows:
            row.set_subtitle(distance)
        for row in self.mass_rows:
            row.set_subtitle(mass)

    # Converting row adjustment limits and values
    def convert_inputs(self):
        # Helper functions
        def row_get_limits(row):
            return [row.get_adjustment().get_lower(), row.get_adjustment().get_upper()]
        def row_set_limits(row, limits):
            row.get_adjustment().set_lower(limits[0])
            row.get_adjustment().set_upper(limits[1])
        # Defining conversions
        if self.imperial is False:
            convert_distance = self.in_to_cm
            convert_mass = self.lb_to_kg
        else:
            convert_distance = self.cm_to_in
            convert_mass = self.kg_to_lb
        # Setting limits and values
        for row in self.distance_rows:
            limits = row_get_limits(row)
            for i in range(len(limits)): limits[i] = round(convert_distance(limits[i]), 1)
            row_set_limits(row, limits)
            row.set_value(convert_distance(round(row.get_value(), 1)))
        for row in self.mass_rows:
            limits = row_get_limits(row)
            for i in range(len(limits)): limits[i] = round(convert_mass(limits[i]), 1)
            row_set_limits(row, limits)
            row.set_value(convert_mass(round(row.get_value(), 1)))

    def get_results(self):
        # Getting dynamic values
        def get_whtr_unhealthy():
            if self.age > 40:   return ((self.age-40)/100)+0.5
            elif self.age > 50: return 0.6
            else:               return 0.5
        def get_whr_overweight():
            if self.gender == "Female": return 0.8
            elif self.gender == "Male": return 0.9
            else:                       return 0.85
        def get_whr_obese():
          if self.gender == "Female": return 0.85
          elif self.gender == "Male": return 1
          else:                       return 0.925
        # Returning results
        return {
          'basic_bmi': {
            'widget': self.result_feedback_label,
            'label':  self.bmi_button,
            'value':  int(round(self.bmi, 0)),
            'thresholds': [
              {'text': _('Underweight'),     'value': 0,    'style': 'light-blue'},
              {'text': _('Healthy'),         'value': 18.5, 'style': 'success'},
              {'text': _('Overweight'),      'value': 25,   'style': 'warning'},
              {'text': _('Obese'),           'value': 30,   'style': 'error'},
              {'text': _('Extremely obese'), 'value': 40,   'style': 'error'},
            ]
          },
          'bmi': {
            'widget': self.result_bmi_row,
            'label': self.result_bmi_row_label,
            'value':  round(self.bmi, 1),
            'thresholds': [
              {'text': _('Underweight [Severe]'),   'value': 0,    'style': 'light-blue'},
              {'text': _('Underweight [Moderate]'), 'value': 16,   'style': 'light-blue'},
              {'text': _('Underweight [Mild]'),     'value': 17,   'style': 'light-blue'},
              {'text': _('Healthy'),                'value': 18.5, 'style': 'success'},
              {'text': _('Overweight'),             'value': 25,   'style': 'warning'},
              {'text': _('Obese [Class 1]'),        'value': 30,   'style': 'error'},
              {'text': _('Obese [Class 2]'),        'value': 35,   'style': 'error'},
              {'text': _('Obese [Class 3]'),        'value': 40,   'style': 'error'},
            ]
          },
          'whtr': {
            'widget': self.result_waist_to_height_row,
            'label': self.result_waist_to_height_row_label,
            'value':  round(self.waist_to_height, 2),
            'thresholds': [
              {'text': _('Healthy'),   'value': 0,                    'style': 'success'},
              {'text': _('Unhealthy'), 'value': get_whtr_unhealthy(), 'style': 'warning'},
            ]
          },
          'whr': {
            'widget': self.result_waist_to_hip_row,
            'label': self.result_waist_to_hip_row_label,
            'value':  round(self.waist_to_hip, 2),
            'thresholds': [
              {'text': _('Healthy'),    'value': 0,                    'style': 'success'},
              {'text': _('Overweight'), 'value': get_whr_overweight(), 'style': 'warning'},
              {'text': _('Obese'),      'value': get_whr_obese(),      'style': 'error'},
            ]
          },
          'bri': {
            'widget': self.result_bri_row,
            'label': self.result_bri_row_label,
            'value':  round(self.bri, 2),
            'thresholds': [
              {'text': _('Very lean'),     'value': 0,    'style': 'light-blue'},
              {'text': _('Lean'),          'value': 3.41, 'style': 'success'},
              {'text': _('Average'),       'value': 4.45, 'style': 'success'},
              {'text': _('Above average'), 'value': 5.46, 'style': 'warning'},
              {'text': _('High'),          'value': 6.91, 'style': 'error'},
            ]
          },
        }

    def update_result_labels(self):
        def clear_css(widget):
            widget.remove_css_class("light-blue")
            widget.remove_css_class("success")
            widget.remove_css_class("warning")
            widget.remove_css_class("error")
        results = self.get_results()
        for item in results:
          widget = results.get(item).get('widget')
          label = results.get(item).get('label')
          value = results.get(item).get('value')
          label.set_label(str(value))
          thresholds = results.get(item).get('thresholds')
          for threshold in thresholds:
              threshold_value = threshold.get('value')
              text = threshold.get('text')
              style = threshold.get('style')
              if value >= threshold_value:
                  clear_css(widget)
                  if widget.get_name() == "GtkLabel":
                      widget.set_label(text)
                      widget.add_css_class(style)
                  if widget.get_name() == "AdwActionRow":
                      widget.set_subtitle(text)
                      widget.add_css_class(style)

        # Creates a spin row and adds it to either self.inputs_group or advanced_inputs_group
    def create_input_row(self, widgetName, title, adjustment, digits, tooltip, advanced):
        # Creating AdwSpinRow with name widgetName
        setattr(self, widgetName, Adw.SpinRow())
        self.widget = getattr(self, widgetName)
        # Customizing the SpinRow
        self.widget.set_title(title)
        self.widget.set_tooltip_text(tooltip)
        self.widget.set_adjustment(adjustment)
        self.widget.set_digits(digits)
        # Deciding where to add the row
        if advanced == True: self.advanced_inputs_group.add(self.widget)
        else: self.inputs_group.add(self.widget)

    # Creates an action row with a label and adds it to self.right_group
    def create_result_row(self, widgetName, title, tooltip):
        setattr(self, widgetName, Adw.ActionRow())
        setattr(self, f"{widgetName}_label", Gtk.Label())
        self.widget = getattr(self, widgetName)
        self.label = getattr(self, f"{widgetName}_label")
        self.widget.set_activatable(True)
        self.widget.set_title(title)
        self.widget.connect("activated", self.clipboard_copy)
        self.widget.set_tooltip_text(tooltip)
        self.widget.add_css_class("heading")
        self.label.set_css_classes(["title-3"])
        # self.label.set_label("21")
        self.widget.add_suffix(self.label)
        self.right_group.add(self.widget)

    # Copying text from result widget
    def clipboard_copy(self, widget):
        # Copying the result label from a result row
        if widget.get_name() == "AdwActionRow":
            value = widget.get_first_child().get_first_child() \
            .get_next_sibling().get_next_sibling().get_next_sibling() \
            .get_first_child().get_label()
            # Hackiest way ever, but it works 🤷
            # Explanation: AdwActionRow has a box inside a box of which the 4th
            #              child is the "suffixes", inside it is the result label
        # Copying a button's label
        if widget.get_name() == "GtkButton":
            value = widget.get_label();
        value = str(value) # Gdk Clipboard only accepts strings
        clipboard = Gdk.Display.get_default().get_clipboard()
        print(f"Copied result '{value}'")
        Gdk.Clipboard.set(clipboard, value);
        # Creating and showing a toast
        self.toast = Adw.Toast(title=_("Result copied"), timeout=1)
        self.toast_overlay.add_toast(self.toast)

    # For easier conversions
    def in_to_cm(self, value): value *= 2.54; return value
    def cm_to_in(self, value): value *= 0.3937008; return value
    def kg_to_lb(self, value): value *= 2.204623; return value
    def lb_to_kg(self, value): value *= 0.4535924; return value

    # Show the About app dialog
    def show_about(self, _button):
        self.about = Adw.AboutWindow(
        application_name = 'BMI',
        application_icon = 'io.github.philippkosarev.bmi',
        developer_name   = 'Philipp Kosarev',
        version          = 'v3.0',
        developers       = ['Philipp Kosarev'],
        artists          = ['Philipp Kosarev'],
        copyright        = '© 2024 Philipp Kosarev',
        license_type     = "GTK_LICENSE_GPL_2_0",
        website          = "https://github.com/philippkosarev/bmi",
        issue_url        = "https://github.com/philippkosarev/bmi/issues"
        ); self.about.present()

    # Action after closing the app window
    def on_close_window(self, widget, *args):
        # Setting gsettings values to adjustments to use them on next launch
        self.settings["mode"] = self.mode_dropdown.get_selected()
        self.settings["forget"] = self.forget_button.get_active()
        self.settings["imperial"] = self.units_button.get_active()
        # Body metrics
        self.settings["height"] = round(self.height, 0)
        self.settings["mass"] = round(self.mass, 0)
        self.settings["waist"] = round(self.waist, 0)
        self.settings["hip"] = round(self.hip, 0)
        # Age and gender
        self.settings["age"] = self.age_input_row.get_value()
        self.settings["gender"] = self.gender_adjustment.get_selected()
        # Resets adjustments if forget button is active
        body_metrics=["height", "mass", "gender", "age", "waist", "hip"]
        if self.settings["forget"] is True:
            for body_metric in body_metrics:
                self.settings.reset(body_metric)
