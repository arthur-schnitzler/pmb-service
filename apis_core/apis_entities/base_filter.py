import django_filters
from django.db.models import Q


class MyBaseFilter(django_filters.FilterSet):
    def construct_lookup(self, value):
        """
        Parses user input for wildcards and returns a tuple containing the interpreted django lookup string and the trimmed value
        E.g.
            'example' -> ('__icontains', 'example')
            '*example' -> ('__iendswith', 'example')
            'example*' -> ('__istartswith', 'example')
            '"example"' -> ('__iexact', 'example')

        :param value : str : text to be parsed for *
        :return: (lookup : str, value : str)
        """

        if value.startswith("*") and not value.endswith("*"):
            value = value[1:]
            return "__iendswith", value

        elif not value.startswith("*") and value.endswith("*"):
            value = value[:-1]
            return "__istartswith", value

        elif value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
            return "__iexact", value

        else:
            if value.startswith("*") and value.endswith("*"):
                value = value[1:-1]

            return "__icontains", value

    def name_label_filter(self, queryset, name, value):
        # TODO __sresch__ : include alternative names queries
        lookup, value = self.construct_lookup(value)
        queryset_related_label = queryset.filter(**{"label__label" + lookup: value})
        queryset_self_name = queryset.filter(**{name + lookup: value})
        return (queryset_related_label | queryset_self_name).distinct().all()
