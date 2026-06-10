from django.core.exceptions import ValidationError


class StartDateAfterEndDateError(ValidationError):
    default_message = "Das End-Datum muss gleich oder spaeter als das Start-Datum sein."

    def __init__(self, message=None):
        final_message = message or self.default_message
        super().__init__({"end_date_written": [final_message]})
