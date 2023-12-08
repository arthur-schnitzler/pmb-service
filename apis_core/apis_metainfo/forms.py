from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from dal import autocomplete
from django import forms

from .models import *


class UriForm(forms.ModelForm):
    class Meta:
        model = Uri
        fields = "__all__"
        widgets = {
            "entity": autocomplete.ModelSelect2(
                url="apis_core:apis_metainfo-ac:apis_tempentity-autocomplete"
            ),
        }

    def __init__(self, *args, **kwargs):
        super(UriForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-md-3"
        self.helper.field_class = "col-md-9"
        self.helper.add_input(
            Submit("submit", "save"),
        )
