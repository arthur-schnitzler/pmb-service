from dal import autocomplete
from django.db.models import Q

from .models import TempEntityClass


class TempEntityClassAC(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # select_subclasses() returns the actual entity instances (e.g. Person),
        # so __str__ can include the first name instead of only the surname
        qs = TempEntityClass.objects_inheritance.select_subclasses()

        if self.q:
            if self.q.isdigit() and int(self.q) < 2**63:
                # additionally allow looking up an entry by its db-ID
                qs = qs.filter(Q(name__icontains=self.q) | Q(pk=int(self.q)))
            else:
                qs = qs.filter(name__icontains=self.q)

        return qs
