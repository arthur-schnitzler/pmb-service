import django_tables2
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django_tables2.export.views import ExportMixin


def get_entities_table(model_class):
    class GenericEntitiesTable(django_tables2.Table):
        id = django_tables2.LinkColumn()

        class Meta:
            model = model_class
            attrs = {"class": "table table-hover table-striped table-condensed"}

    return GenericEntitiesTable


class GenericFilterFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(GenericFilterFormHelper, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.form_class = "genericFilterForm"
        self.form_method = "GET"
        self.helper.form_tag = False
        self.add_input(Submit("Filter", "Search"))


class GenericListView(ExportMixin, django_tables2.SingleTableView):
    filter_class = None
    formhelper_class = None
    context_filter_name = "filter"
    paginate_by = 25
    template_name = "browsing/generic_list.html"
    init_columns = []
    excluded_cols = []
    verbose_name = "Personen"
    help_text = "Personen help text"

    def get_table_class(self):
        if self.table_class:
            return self.table_class
        else:
            return get_entities_table(self.model)

    def get_all_cols(self):
        all_cols = {
            key: value.header for key, value in self.get_table().base_columns.items()
        }
        return all_cols

    def get_queryset(self, **kwargs):
        qs = super(GenericListView, self).get_queryset()
        self.filter = self.filter_class(self.request.GET, queryset=qs)
        self.filter.form.helper = self.formhelper_class()
        return self.filter.qs.distinct()

    def get_table(self, **kwargs):
        table = super(GenericListView, self).get_table()
        default_cols = self.init_columns
        all_cols = table.base_columns.keys()
        print(default_cols, all_cols)
        selected_cols = self.request.GET.getlist("columns") + default_cols
        exclude_vals = [x for x in all_cols if x not in selected_cols]
        table.exclude = exclude_vals
        return table

    def get_context_data(self, **kwargs):
        context = super(GenericListView, self).get_context_data()
        togglable_colums = {
            key: value
            for key, value in self.get_all_cols().items()
            if key not in self.init_columns and key not in self.exclude_columns
        }
        context["togglable_colums"] = togglable_colums
        context[self.context_filter_name] = self.filter
        context["docstring"] = "{}".format(self.model.__doc__)
        if self.model._meta.verbose_name_plural:
            context["class_name"] = "{}".format(self.model._meta.verbose_name.title())
        else:
            if self.model.__name__.endswith("s"):
                context["class_name"] = "{}".format(self.model.__name__)
            else:
                context["class_name"] = "{}s".format(self.model.__name__)
        try:
            context["create_view_link"] = self.model.get_createview_url()
        except AttributeError:
            context["create_view_link"] = None
        model_name = self.model.__name__.lower()
        context["entity"] = model_name
        context["app_name"] = self.model._meta.app_label
        context["verbose_name"] = self.verbose_name
        context["help_text"] = self.help_text
        try:
            context["icon"] = self.model.get_icon()
        except AttributeError:
            context["icon"] = "bi bi-infinity"
        try:
            context["second_icon"] = self.model.get_second_icon()
        except AttributeError:
            context["second_icon"] = "bi bi-infinity"
        if self.get_queryset().count() < 1001:
            context["download"] = True
        else:
            context["download"] = False
        return context


class BaseDetailView(DetailView):
    model = None
    template_name = "browsing/generic_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["docstring"] = "{}".format(self.model.__doc__)
        context["class_name"] = "{}".format(self.model.__name__)
        context["app_name"] = "{}".format(self.model._meta.app_label)
        return context


class BaseCreateView(CreateView):
    model = None
    form_class = None
    template_name = "browsing/generic_create.html"

    def get_context_data(self, **kwargs):
        context = super(BaseCreateView, self).get_context_data()
        context["docstring"] = "{}".format(self.model.__doc__)
        context["class_name"] = "{}".format(self.model.__name__)
        return context


class BaseUpdateView(UpdateView):
    model = None
    form_class = None
    template_name = "browsing/generic_create.html"

    def get_context_data(self, **kwargs):
        context = super(BaseUpdateView, self).get_context_data()
        context["docstring"] = "{}".format(self.model.__doc__)
        context["class_name"] = "{}".format(self.model.__name__)
        return context
