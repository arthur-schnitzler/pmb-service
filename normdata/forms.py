from django import forms


class GndForm(forms.Form):
    gnd_url = forms.URLField(
        label="Normdata URL",
        help_text="Zum Beispiel: http://lobid.org/gnd/118566512 oder https://www.geonames.org/2772400/linz.html",
        max_length=100,
    )
    entity_type = forms.ChoiceField(
        label="Entität",
        help_text="Wähle die Art der Entität: Person, Ort, ...",
        choices=(("person", "Person"), ("place", "Ort")),
    )
