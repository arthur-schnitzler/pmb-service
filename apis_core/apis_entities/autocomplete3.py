#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
import operator
import re
from functools import reduce

from dal import autocomplete
from django import http
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from apis_core.apis_vocabularies.models import VocabsBaseClass

from .models import AbstractEntity


class CustomEntityAutocompletes(object):
    """A class for collecting all the custom autocomplete functions for one entity.

    Attributes:

    - self.entity: (string) entity types
    - self.more: (boolean) if more results can be fetched (pagination)
    - self.page_size: (integer) page size
    - self.results: (list) results
    - self.query: (string) query string

    Methods:
    - self.more(): fetch more results
    """

    def __init__(self, entity, query, page_size=20, offset=0, *args, **kwargs):
        """
        :param entity: (string) entity type to fetch additional autocompletes for
        """
        func_list = {}
        if entity not in func_list.keys():
            self.results = None
            return None
        res = []
        more = dict()
        more_gen = False
        for x in func_list[entity]:
            res2 = x().query(query, page_size, offset)
            if len(res2) == page_size:
                more[x.__name__] = (True, offset + 1)
                more_gen = True
            res.extend(res2)
        self.results = res
        self.page_size = page_size
        self.more = more_gen
        self._more_dict = more
        self.query = query
        self.offset = offset

    def get_more(self):
        """
        Function to retrieve more results.
        """
        res4 = []
        for key, value in self._more_dict.items():
            if value[0]:
                res3 = globals()[key](self.query, self.page_size, value[1])
                if len(res3) == self.page_size:
                    self._more_dict[key] = (True, value[1] + 1)
                else:
                    self._more_dict[key] = (False, value[1])
                self.results.extend(res3)
                res4.extend(res3)
        return res4


class GenericEntitiesAutocomplete(autocomplete.Select2ListView):
    def get(self, request, *args, **kwargs):
        page_size = 20
        offset = (int(self.request.GET.get("page", 1)) - 1) * page_size
        ac_type = self.kwargs["entity"]
        db_include = self.kwargs.get("db_include", False)
        ent_merge_pk = self.kwargs.get("ent_merge_pk", False)
        choices = []
        ent_model = AbstractEntity.get_entity_class_of_name(ac_type)
        if not self.q:
            q3 = False
        if self.q.startswith("http"):
            res = ent_model.objects.filter(uri__uri=self.q.strip())
        elif len(self.q) > 0:
            q1 = re.match("^([^\[]+)\[([^\]]+)\]$", self.q)
            if q1:
                q = q1.group(1).strip()
                q3 = q1.group(2).split(",")
                q3 = [e.strip() for e in q3]
            else:
                q = re.match("^[^\[]+", self.q).group(0)
                q3 = False
            if re.match("^[^*]+\*$", q.strip()):
                search_type = "__istartswith"
                q = re.match("^([^*]+)\*$", q.strip()).group(1)
            elif re.match("^\*[^*]+$", q.strip()):
                search_type = "__iendswith"
                q = re.match("^\*([^*]+)$", q.strip()).group(1)
            elif re.match('^"[^"]+"$', q.strip()):
                search_type = ""
                q = re.match('^"([^"]+)"$', q.strip()).group(1)
            elif re.match("^[^*]+$", q.strip()):
                search_type = "__icontains"
                q = q.strip()
            else:
                search_type = "__icontains"
                q = q.strip()
            arg_list = [
                Q(**{x + search_type: q})
                for x in settings.APIS_ENTITIES[ac_type.title()]["search"]
            ]
            res = ent_model.objects.filter(reduce(operator.or_, arg_list)).order_by('id').distinct()
            if q3:
                f_dict2 = {}
                for fd in q3:
                    f_dict2[fd.split("=")[0].strip()] = fd.split("=")[1].strip()
                try:
                    res = res.filter(**f_dict2)
                except Exception as e:
                    choices.append({"name": str(e)})
        else:
            q = ""
            res = []
        test_db = True
        test_stanbol = False
        more = True
        if not db_include:
            for r in res[offset : offset + page_size]:
                if int(r.pk) == int(ent_merge_pk):
                    continue

                f = dict()
                dataclass = ""
                try:
                    f["id"] = r.id
                except:
                    continue
                f["text"] = (
                    "<span {}><small>db</small> <b>{}</b> <small>db-ID: {}</small> </span> ".format(
                        dataclass, str(r), str(r.id)
                    )
                )
                choices.append(f)
            if len(choices) < page_size:
                test_db = False
        else:
            test_db = False
        test_stanbol = False
        cust_auto_more = False
        if q:
            cust_auto = CustomEntityAutocompletes(
                ac_type, q, page_size=page_size, offset=offset
            )
            if cust_auto.results is not None:
                cust_auto_more = cust_auto.more
                if len(cust_auto.results) > 0:
                    choices.extend(cust_auto.results)
        if not test_db and not test_stanbol and not cust_auto_more:
            more = False

        return http.HttpResponse(
            json.dumps({"results": choices + [], "pagination": {"more": more}}),
            content_type="application/json",
        )


class GenericVocabulariesAutocomplete(autocomplete.Select2ListView):
    def get(self, request, *args, **kwargs):
        page_size = 20
        offset = (int(self.request.GET.get("page", 1)) - 1) * page_size
        more = False
        vocab = self.kwargs["vocab"]
        direct = self.kwargs["direct"]
        q = self.q
        vocab_model = ContentType.objects.get(
            app_label="apis_vocabularies", model=vocab
        ).model_class()
        if direct == "normal":
            if vocab_model.__bases__[0] == VocabsBaseClass:
                choices = [
                    {"id": x.pk, "text": x.label}
                    for x in vocab_model.objects.filter(name__icontains=q).order_by(
                        "parent_class__name", "name"
                    )[offset : offset + page_size]
                ]
            else:
                choices = [
                    {"id": x.pk, "text": x.label}
                    for x in vocab_model.objects.filter(
                        Q(name__icontains=q) | Q(name_reverse__icontains=q)
                    ).order_by("parent_class__name", "name")[
                        offset : offset + page_size
                    ]
                ]
        elif direct == "reverse":
            choices = [
                {"id": x.pk, "text": x.label_reverse}
                for x in vocab_model.objects.filter(
                    Q(name__icontains=q) | Q(name_reverse__icontains=q)
                ).order_by("parent_class__name", "name")[offset : offset + page_size]
            ]
        if len(choices) == page_size:
            more = True
        return http.HttpResponse(
            json.dumps({"results": choices + [], "pagination": {"more": more}}),
            content_type="application/json",
        )
