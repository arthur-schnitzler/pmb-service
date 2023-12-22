from django import forms


class GndForm(forms.Form):
    gnd_url = forms.URLField(label="GND/LOBID URL einer Person", max_length=100)
