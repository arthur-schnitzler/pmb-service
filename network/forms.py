from crispy_forms.helper import FormHelper

from crispy_forms.layout import Layout
from crispy_forms.bootstrap import AccordionGroup
from crispy_bootstrap5.bootstrap5 import BS5Accordion


class EdgeFilterFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(EdgeFilterFormHelper, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.form_class = "genericFilterForm"
        self.form_method = "GET"
        self.form_tag = False
        self.layout = Layout(
            BS5Accordion(
                AccordionGroup(
                    "Quellknoten",
                    "source_label",
                    "source_kind",
                ),
                AccordionGroup(
                    "Zielknoten",
                    "target_label",
                    "target_kind",
                ),
                AccordionGroup(
                    "Beziehung",
                    "edge_label",
                    "edge_kind",
                    "start_date",
                    "end_date",
                ),
            ),
        )
