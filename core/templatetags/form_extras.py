from django import template

register = template.Library()

CHECKBOX_TYPES = {"checkboxinput", "checkboxselectmultiple", "radioselect"}
SELECT_TYPES = {"select", "selectmultiple"}


@register.filter(name="bootstrap_field")
def bootstrap_field(field):
    widget_type = field.widget_type
    if widget_type in CHECKBOX_TYPES:
        css_class = "form-check-input"
    elif widget_type in SELECT_TYPES:
        css_class = "form-select"
    else:
        css_class = "form-control"

    existing = field.field.widget.attrs.get("class", "")
    combined = f"{existing} {css_class}".strip()
    return field.as_widget(attrs={"class": combined})
