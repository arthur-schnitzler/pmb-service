import inspect
import re
import sys
import unicodedata

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

from apis_core.apis_metainfo.models import TempEntityClass, Uri
from apis_core.apis_vocabularies.models import (
    EventType,
    InstitutionType,
    PlaceType,
    ProfessionType,
    Title,
    WorkType,
)
from apis_core.helper_functions import EntityRelationFieldGenerator

BASE_URI = getattr(settings, "APIS_BASE_URI", "http://apis.info/")
DOMAIN_DEFAULT = "pmb"


class AbstractEntity(TempEntityClass):
    """
    Abstract super class which encapsulates common logic between the different entity kinds and provides various methods
    relating to either all or a specific entity kind.

    Most of the class methods are designed to be used in the sublcass as they are considering contexts which depend on
    the subclass entity type. So they are to be understood in that dynamic context.
    """

    # Placeholder for list filter classes attached to each entity later
    list_filter_class = None

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__class__.create_relation_methods_from_manytomany_fields()

    # Methods dealing with individual data retrievals of instances
    ####################################################################################################################

    def __str__(self):
        if self.__class__ == Person:

            def valid(name):
                return name != "" and name is not None

            if valid(self.first_name) and valid(self.name):
                return "{}, {}".format(self.name, self.first_name)
            elif valid(self.first_name) and not valid(self.name):
                return "{}, {}".format("no surename provided", self.first_name)
            elif not valid(self.first_name) and valid(self.name):
                return self.name
            elif not valid(self.first_name) and not valid(self.name):
                return "no name provided"

        else:
            if self.name != "":
                return self.name
            else:
                return "no name provided"

    @classmethod
    def get_or_create_uri(cls, uri):
        uri = str(uri)
        try:
            if re.match(r"^[0-9]*$", uri):
                p = cls.objects.get(pk=uri)
            else:
                p = cls.objects.get(uri__uri=uri)
            return p
        except Exception as e:
            print(f"Error: {e}")
            print(f"Found no object corresponding to given uri: {uri}.")
            return False

    @classmethod
    def set_list_filter_class(cls, list_filter_class):
        cls.list_filter_class = list_filter_class

    # Various Methods enabling convenient shortcuts between entities, relations, fields, etc
    ####################################################################################################################

    @classmethod
    def create_relation_methods_from_manytomany_fields(cls):
        """
        Creates methods on an entity class with which other related entities can be called without the need to consider
        potential self-references (the A and B sides therein).

        The resulting methods follow the syntax:
        <entity>.get_related_<entity>_instances()

        e.g. for Person:
        person.get_related_work_instances()
        or
        person.get_related_person_instances()

        Note that with these methods it is not necessary to differentiate between
        A and B entities when self-relations exist.

        The result of any such method call is the queryset of the related entities.
        (And not a ManyToManyManager as is the case when calling <entity>.<entity>_set where
        in the case of self-relation
        it must be differentiated between A and B entities, e.g. person.personA_set )

        It was not possible to my understanding to change managers in such a way that two
        (the A and the B) could be combined
        into one manager. Hence these additional shortcut methods.

        :return: None
        """

        def create_function_from_manytomany_field_to_other_entity(
            entity_manytomany_field,
        ):
            """
            creates the individual method from a ManyToMany field by calling the manager's objects.all()

            This method creation has to be done here in a separate method, so that it can be called once
            before assignment
            as otherwise the variable 'entity_name' in the loop below changes with each iteration and with that also the
            method references (due to python's "late binding").
            A method call in between thus forces the content of 'entity_name' to be assigned for good to the
            respective class ( = forced early binding).
            For more details on this: https://stackoverflow.com/questions/3431676/creating-functions-in-a-loop

            :param entity_manytomany_field: the ManyToManyManager to another model
            :return: method which will call the managers's objects.all() method
            """
            return lambda self: getattr(self, entity_manytomany_field).all().distinct()

        def create_function_from_manytomany_field_to_self_entity(
            entityA_manytomany_field, entityB_manytomany_field
        ):
            """
            Same method as above, but with two managers instead of one for the case of self-relations.

            Both managers' objects.all() methods are called and their queryset results are unionised for the
            shortcut method of an entity to its own related entities.

            :param entityA_manytomany_field: ManyToManyManager to entity A in a self-relation
            :param entityB_manytomany_field: ManyToManyManager to entity A in a self-relation
            :return: method to call both and return the distinct union of them
            """
            return lambda self: (
                getattr(self, entityA_manytomany_field)
                .all()
                .union(getattr(self, entityB_manytomany_field).all())
            ).distinct()

        for entity_name in cls.get_all_entity_names():
            # Iterate over each entity defined within this models' module

            related_entity_function_name = "get_related_" + entity_name + "_instances"

            if not hasattr(cls, related_entity_function_name):
                if cls.__name__.lower() == entity_name:
                    # If the related entity is the same as this current one, then set the names of the related functions
                    # to A and B and also combine them into one function where both A and B are returned.

                    related_entityA_function_name = (
                        "get_related_" + entity_name + "A_instances"
                    )
                    related_entityB_function_name = (
                        "get_related_" + entity_name + "B_instances"
                    )
                    entityA_manytomany_field = entity_name + "A_set"
                    entityB_manytomany_field = entity_name + "B_set"

                    setattr(
                        cls,
                        related_entityA_function_name,
                        create_function_from_manytomany_field_to_other_entity(
                            entityA_manytomany_field
                        ),
                    )

                    setattr(
                        cls,
                        related_entityB_function_name,
                        create_function_from_manytomany_field_to_other_entity(
                            entityB_manytomany_field
                        ),
                    )

                    setattr(
                        cls,
                        related_entity_function_name,
                        create_function_from_manytomany_field_to_self_entity(
                            entityA_manytomany_field, entityB_manytomany_field
                        ),
                    )

                else:
                    # If the related entity is a different one, then just build on the usual names

                    entity_manytomany_field = entity_name + "_set"

                    setattr(
                        cls,
                        related_entity_function_name,
                        create_function_from_manytomany_field_to_other_entity(
                            entity_manytomany_field
                        ),
                    )

    # Methods dealing with all entities
    ####################################################################################################################

    _all_entity_classes = None
    _all_entity_names = None

    @classmethod
    def get_all_entity_classes(cls):
        """
        :return: list of all python classes of the entities defined within this models' module
        """

        if cls._all_entity_classes is None:
            entity_classes = []
            entity_names = []

            for entity_name, entity_class in inspect.getmembers(
                sys.modules[__name__], inspect.isclass
            ):
                if (
                    entity_class.__module__ == "apis_core.apis_entities.models"
                    and entity_name != "ent_class"
                    and entity_name != "AbstractEntity"
                ):
                    entity_classes.append(entity_class)
                    entity_names.append(entity_name.lower())

            cls._all_entity_classes = entity_classes
            cls._all_entity_names = entity_names

        return cls._all_entity_classes

    @classmethod
    def get_entity_class_of_name(cls, entity_name):
        """
        :param entity_name: str : The name of an entity
        :return: The model class of the entity respective to the given name
        """

        for entity_class in cls.get_all_entity_classes():
            if entity_class.__name__.lower() == entity_name.lower():
                return entity_class

        raise Exception("Could not find entity class of name:", entity_name)

    @classmethod
    def get_all_entity_names(cls):
        """
        :return: list of all class names in lower case of the entities defined within this models' module
        """

        if cls._all_entity_names == None:
            cls.get_all_entity_classes()

        return cls._all_entity_names

    # Methods dealing with related entities
    ####################################################################################################################

    _related_entity_field_names = None

    @classmethod
    def get_related_entity_field_names(cls):
        """
        :return: a list of names of all ManyToMany field names relating to entities from the respective entity class

        E.g. for Person.get_related_entity_field_names() or person_instance.get_related_entity_field_names() ->
        ['event_set', 'institution_set', 'personB_set', 'personA_set', 'place_set', 'work_set']

        Note: this method depends on the 'generate_all_fields' function of the EntityRelationFieldGenerator class
        which wires the ManyToMany Fields into the entities and respective relationtypes.
        This method is nevertheless defined here within AbstractEntity for documentational purpose.
        """

        if cls._related_entity_field_names == None:
            raise Exception("_related_entity_field_names was not initialized yet.")
        else:
            return cls._related_entity_field_names

    @classmethod
    def add_related_entity_field_name(cls, entity_field_name):
        """
        :param entity_field_name: the name of one of several ManyToMany fields created automatically
        :return: None

        Note: this method depends on the 'generate_all_fields' function of the EntityRelationFieldGenerator class
        which wires the ManyToMany Fields into the entities and respective relationtypes.
        This method is nevertheless defined here within AbstractEntity for documentational purpose.
        """

        if cls._related_entity_field_names == None:
            cls._related_entity_field_names = []

        cls._related_entity_field_names.append(entity_field_name)

    def get_related_entity_instances(self):
        """
        :return: list of queryset of all entity instances which are somehow related to the calling entity instance
        """

        queryset_list = []

        for entity_name in self.get_all_entity_names():
            queryset = getattr(self, "get_related_" + entity_name + "_instances")()
            if len(queryset) > 0:
                queryset_list.append(queryset)

        return queryset_list

    # Methods dealing with related relations
    ####################################################################################################################

    @classmethod
    def get_related_relation_classes(cls):
        """
        :return: list of python classes of the relations which are related to the respective entity class

        E.g. for Place.get_related_relation_classes() or place_instance.get_related_relation_classes() ->
        [ InstitutionPlace, PersonPlace, PlaceEvent, PlacePlace, PlaceWork ]
        """

        # TODO __sresch__ : check for best practice on local imports vs circularity problems.
        from apis_core.apis_relations.models import AbstractRelation

        return AbstractRelation.get_relation_classes_of_entity_class(cls)

    @classmethod
    def get_related_relation_field_names(cls):
        """
        :return: list of class names in lower case of the relations which are related to the respective entity class

        E.g. for Place.get_related_relation_names() or place_instance.get_related_relation_names() ->
        ['institutionplace_set', 'personplace_set', 'placeevent_set', 'placeplace_set', 'placework_set']
        """
        # TODO __sresch__ : check for best practice on local imports vs circularity problems.
        from apis_core.apis_relations.models import AbstractRelation

        return AbstractRelation.get_relation_field_names_of_entity_class(cls)

    def get_related_relation_instances(self):
        """
        :return: list of queryset of all relation instances which are somehow related to the calling entity instance
        """

        queryset_list = []

        for relation_class in self.get_related_relation_classes():
            q_args = Q()

            if relation_class.get_related_entity_classa() == self.__class__:
                q_args |= Q(**{relation_class.get_related_entity_field_namea(): self})

            if relation_class.get_related_entity_classb() == self.__class__:
                q_args |= Q(**{relation_class.get_related_entity_field_nameb(): self})

            queryset = relation_class.objects.filter(q_args)
            queryset_list.extend(list(queryset))

        return queryset_list

    # Methods dealing with related relationtypes
    ####################################################################################################################

    _related_relationtype_classes = None
    _related_relationtype_field_names = None
    _related_relationtype_names = None

    @classmethod
    def get_related_relationtype_classes(cls):
        """
        :return: list of python classes of the relation types which are related to the respective entity class

        E.g. for Place.get_related_relation_classes() or place_instance.get_related_relation_classes() ->
        [ InstitutionPlaceRelation, PersonPlaceRelation, PlaceEventRelation, PlacePlaceRelation, PlaceWorkRelation ]
        """

        if cls._related_relationtype_classes == None:
            relationtype_classes = []
            relationtype_names = []

            # TODO __sresch__ : check for best practice on local imports vs circularity problems.
            from apis_core.apis_vocabularies.models import AbstractRelationType

            for (
                relationtype_class
            ) in AbstractRelationType.get_all_relationtype_classes():
                relationtype_name = relationtype_class.__name__.lower()

                if cls.__name__.lower() in relationtype_name:
                    relationtype_classes.append(relationtype_class)
                    relationtype_names.append(relationtype_name)

            cls._related_relationtype_classes = relationtype_classes
            cls._related_relationtype_names = relationtype_names

        return cls._related_relationtype_classes

    @classmethod
    def get_related_relationtype_names(cls):
        """
        :return: list of class names in lower case of the relation types which are related to the respective entity class

        E.g. for Place.get_related_relation_classes() or place_instance.get_related_relation_classes() ->
        [ 'institutionplacerelation', 'personplacerelation', 'placeeventrelation', 'placeplacerelation', 'placeworkrelation' ]
        """

        if cls._related_relationtype_names == None:
            cls.get_related_relationtype_classes()

        return cls._related_relationtype_names

    @classmethod
    def get_related_relationtype_field_names(cls):
        """
        :return: a list of names of all ManyToMany field names relating to relationtypes from the respective entity class

        E.g. for PersonPerson.get_related_relationtype_field_names() or person_instance.get_related_relationtype_field_names() ->
        ['event_relationtype_set', 'institution_relationtype_set', 'personB_relationtype_set', 'personA_relationtype_set', 'place_relationtype_set', 'work_relationtype_set']

        Note: this method depends on the 'generate_all_fields' function of the EntityRelationFieldGenerator class
        which wires the ManyToMany Fields into the entities and respective relationtypes.
        This method is nevertheless defined here within AbstractEntity for documentational purpose.
        """

        if cls._related_relationtype_field_names == None:
            raise Exception(
                "_related_relationtype_field_names was not initialized yet."
            )
        else:
            return cls._related_relationtype_field_names

    @classmethod
    def add_related_relationtype_field_name(cls, relationtype_field_name):
        """
        :param entity_field_name: the name of one of several ManyToMany fields created automatically
        :return: None

        Note: this method depends on the 'generate_all_fields' function of the EntityRelationFieldGenerator class
        which wires the ManyToMany Fields into the entities and respective relationtypes.
        This method is nevertheless defined here within AbstractEntity for documentational purpose.
        """

        if cls._related_relationtype_field_names == None:
            cls._related_relationtype_field_names = []

        cls._related_relationtype_field_names.append(relationtype_field_name)

    def get_related_relationtype_instances(self):
        """
        :return: list of queryset of all relationtype instances which are somehow related to the calling entity instance
        """

        queryset_list = []

        for entity_name in self.get_all_entity_names():
            queryset = None

            if entity_name != self.__class__.__name__.lower():
                queryset = (
                    getattr(self, entity_name + "_relationtype_set").all().distinct()
                )

            else:
                querysetA = (
                    getattr(self, entity_name + "A_relationtype_set").all().distinct()
                )
                querysetB = (
                    getattr(self, entity_name + "B_relationtype_set").all().distinct()
                )
                queryset = querysetA.union(querysetB)

            if queryset and len(queryset) > 0:
                queryset_list.append(queryset)

        return queryset_list


class Person(AbstractEntity):
    GENDER_CHOICES = (
        ("female", "female"),
        ("male", "male"),
        ("third gender", "third gender"),
    )
    first_name = models.CharField(
        max_length=255,
        help_text="The persons´s forename. In case of more then one name...",
        blank=True,
        null=True,
    )
    profession = models.ManyToManyField(ProfessionType, blank=True)
    title = models.ManyToManyField(Title, blank=True)
    gender = models.CharField(
        max_length=15, choices=GENDER_CHOICES, blank=True, null=True
    )

    def save(self, *args, **kwargs):
        if self.first_name:
            # secure correct unicode encoding
            if self.first_name != unicodedata.normalize("NFC", self.first_name):
                self.first_name = unicodedata.normalize("NFC", self.first_name)
        super(Person, self).save(*args, **kwargs)
        return self

    class Meta:
        verbose_name = "Person"
        verbose_name_plural = "Personen"
        ordering = [
            "-id",
        ]

    def get_tei_url(self):
        return reverse("apis_core:apis_tei:person_as_tei", kwargs={"pk": self.id})

    def get_api_url(self):
        return f"/apis/api/entities/person/{self.id}/"

    @classmethod
    def get_icon(self):
        return "bi bi-people apis-person"

    @classmethod
    def get_color(self):
        return "#720e07"


class Place(AbstractEntity):
    kind = models.ForeignKey(
        PlaceType, blank=True, null=True, on_delete=models.SET_NULL
    )
    lat = models.FloatField(blank=True, null=True, verbose_name="latitude")
    lng = models.FloatField(blank=True, null=True, verbose_name="longitude")

    def save(self, *args, **kwargs):
        # see archemd/tests.py for the test
        if not self.lat or not self.lng:
            self.lat = None
            self.lng = None
        try:
            if self.lat < -90 or self.lat > 90:
                self.lat = None
                self.lng = None
            elif self.lng < -180 or self.lng > 180:
                self.lat = None
                self.lng = None
            else:
                pass
        except TypeError:
            self.lat = None
            self.lng = None
        super(Place, self).save(*args, **kwargs)
        return self

    class Meta:
        verbose_name = "Ort"
        verbose_name_plural = "Orte"
        ordering = [
            "-id",
        ]

    def get_tei_url(self):
        return reverse("apis_core:apis_tei:place_as_tei", kwargs={"pk": self.id})

    def get_api_url(self):
        return f"/apis/api/entities/{self.__class__.__name__.lower()}/{self.id}/"

    @classmethod
    def get_icon(self):
        return "bi bi-map apis-place"

    @classmethod
    def get_color(self):
        return "#5bc0eb"


class Institution(AbstractEntity):
    kind = models.ForeignKey(
        InstitutionType, blank=True, null=True, on_delete=models.SET_NULL
    )

    class Meta:
        verbose_name = "Institution"
        verbose_name_plural = "Institutionen"
        ordering = [
            "-id",
        ]

    def get_tei_url(self):
        return reverse("apis_core:apis_tei:org_as_tei", kwargs={"pk": self.id})

    def get_api_url(self):
        return f"/apis/api/entities/{self.__class__.__name__.lower()}/{self.id}/"

    @classmethod
    def get_icon(self):
        return "bi bi-building-gear apis-institution"

    @classmethod
    def get_color(self):
        return "#1d3461"


class Event(AbstractEntity):
    kind = models.ForeignKey(
        EventType, blank=True, null=True, on_delete=models.SET_NULL
    )

    class Meta:
        verbose_name = "Ereignis"
        verbose_name_plural = "Ereignisse"
        ordering = [
            "-id",
        ]

    def get_tei_url(self):
        return reverse("apis_core:apis_tei:event_as_tei", kwargs={"pk": self.id})

    def get_api_url(self):
        return f"/apis/api/entities/{self.__class__.__name__.lower()}/{self.id}/"

    @classmethod
    def get_icon(self):
        return "bi bi-calendar3 apis-event"

    @classmethod
    def get_color(self):
        return "#9bc53d"


class Work(AbstractEntity):
    kind = models.ForeignKey(WorkType, blank=True, null=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = "Werk"
        verbose_name_plural = "Werke"
        ordering = [
            "-id",
        ]

    def get_tei_url(self):
        return reverse("apis_core:apis_tei:work_as_tei", kwargs={"pk": self.id})

    def get_api_url(self):
        return f"/apis/api/entities/{self.__class__.__name__.lower()}/{self.id}/"

    @classmethod
    def get_icon(self):
        return "bi bi-book apis-work"

    @classmethod
    def get_color(self):
        return "#ff8600"


a_ents = getattr(settings, "APIS_ADDITIONAL_ENTITIES", False)


def prepare_fields_dict(fields_list, vocabs, vocabs_m2m):
    res = dict()
    for f in fields_list:
        res[f["name"]] = getattr(models, f["field_type"])(**f["attributes"])
    for v in vocabs:
        res[v] = models.ForeignKey(
            f"apis_vocabularies.{v}", blank=True, null=True, on_delete=models.SET_NULL
        )
    for v2 in vocabs_m2m:
        res[v2] = models.ManyToManyField(f"apis_vocabularies.{v2}", blank=True)
    return res


ents_cls_list = []


@receiver(post_save, dispatch_uid="create_default_uri")
def create_default_uri(sender, instance, **kwargs):
    if (
        kwargs["created"]
        and sender in [Person, Institution, Place, Work, Event] + ents_cls_list
    ):
        if BASE_URI.endswith("/"):
            base1 = BASE_URI[:-1]
        else:
            base1 = BASE_URI
        uri_c = f"{base1}/entity/{instance.pk}/"
        uri2 = Uri(uri=uri_c, domain=DOMAIN_DEFAULT, entity=instance)
        uri2.save()


lst_entities_complete = [
    globals()[x]
    for x in globals()
    if isinstance(globals()[x], models.base.ModelBase)
    and globals()[x].__module__ == "apis_core.apis_entities.models"
    and x != "AbstractEntity"
    and globals()[x]
]
lst_entities_complete = list(dict.fromkeys(lst_entities_complete))

EntityRelationFieldGenerator.generate_all_fields()
