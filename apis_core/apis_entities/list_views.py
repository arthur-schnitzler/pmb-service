from browsing.browsing_utils import GenericListView

from apis_core.apis_entities.models import Person
from apis_core.apis_entities.tables import PersonTable
from apis_core.apis_entities.forms import GenericFilterFormHelper
from apis_core.apis_entities.filters import PersonListFilter


class PersonListView(GenericListView):
    model = Person
    filter_class = PersonListFilter
    formhelper_class = GenericFilterFormHelper
    table_class = PersonTable
    init_columns = [
        "id",
        "name",
        "start_date",
        "end_date",
    ]
    exclude_columns = []
    enable_merge = False
