from django.db.models import CharField, F, Func, Value
from django.db.models.functions import Coalesce
from django.utils.html import format_html

# order_FOO methods for start_date_written and end_date_written to be used in all kinds of tables where a queryset is loaded
# whose model has start_date_written and end_date_written. These methods order the *_date_written by the content of the
# angle brackets if there is any (e.g. 'um 1900<1900-03-03>'), otherwise by the field itself.
#
# The django-tables2 plugin searches for each column through the table class for corresponding order_* and render_* methods
# E.g. to define custom ordering for a column 'start_date_written' the table class must have an 'order_start_date_written'
# method. In order to use the functions here, assign them to a correspondingly named class variable of the table, e.g.
# 'order_start_date_written = written_order_start_date_written'


def written_date_sort_key(field_name):
    """
    Sort key for a *_date_written field: if the field contains a normalized date in angle brackets
    (e.g. 'um 1900<1900-03-03>'), the content of the brackets is used; otherwise the field itself.
    """
    bracket_content = Func(
        F(field_name),
        Value("<([^>]*)>"),
        function="substring",
        output_field=CharField(),
    )
    return Coalesce(bracket_content, F(field_name), output_field=CharField())


def _order_by_written_date(queryset, field_name, is_descending):
    key = written_date_sort_key(field_name)
    key = key.desc(nulls_last=True) if is_descending else key.asc(nulls_last=True)
    return (queryset.order_by(key), True)


def written_order_start_date_written(self, queryset, is_descending):
    return _order_by_written_date(queryset, "start_date_written", is_descending)


def written_order_end_date_written(self, queryset, is_descending):
    return _order_by_written_date(queryset, "end_date_written", is_descending)


def helper_render_date(value, var_date, var_start_date, var_end_date):
    """
    helper function to avoid duplicated code. It checks the various sub-dates of a model's date field for them being None
    or having values. If a field is None then check for the next, and if all are None, return '—' inditcating no value.

    If there are values, use them as mouse overlay helptext to inform the user about the parsing result behind a written
    date field.

    :param value: str : the *_date_written (either start_date_written or end_date_written) field of an entity or relation
    :param var_date: datetime : either the precisely parsed date or the average in between two dates when *_date_written is a range
    :param var_start_date: datetime : The sub-date of var_date, indicating the start date of the range
    :param var_end_date: datetime : The sub-date of var_date, indicating the end date of the range
    :return: html string : which has the value of the written date and the parsed dates as mouse overlay helptext
    """

    # Various if-else branches checking which of the date fields are not None and should be used

    if var_start_date != None and var_end_date != None:
        overlay_help_text = str(var_start_date) + " - " + str(var_end_date)

    elif var_date != None:
        overlay_help_text = str(var_date)

    else:
        return "—"

    return format_html("<abbr title='{}'>{}</abbr>", overlay_help_text, value)


# Again this function serves a generic purpose and must be assigned as class method to django-tables2 tables.Table class
# The whole logic is very similare to the generic_order_* functions above, so see their comments for more details.
def generic_render_start_date_written(self, record, value):
    return helper_render_date(
        value=value,
        var_date=record.start_date,
        var_start_date=record.start_start_date,
        var_end_date=record.start_end_date,
    )


def generic_render_end_date_written(self, record, value):
    return helper_render_date(
        value=value,
        var_date=record.end_date,
        var_start_date=record.end_start_date,
        var_end_date=record.end_end_date,
    )
