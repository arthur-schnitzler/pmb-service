from django.db import models

EDGE_TYPES = (
    ("personperson", "Personen und Personen"),
    ("personplace", "Personen und Orte"),
    ("personwork", "Personen und Werke"),
    ("personevent", "Personen und Ereignisse"),
    ("personinstitution", "Personen und Institutionen"),
    ("institutioninstitution", "Institutionen und Institutionen"),
    ("institutionplace", "Institutionen und Orte"),
    ("institutionwork", "Institutionen und Werke"),
    ("institutionevent", "Institutionen und Ereignisse"),
    ("placeplace", "Orte und Orte"),
    ("placework", "Orte und Werke"),
    ("placeevent", "Orte und Ereignisse"),
    ("eventevent", "Ereignisse und Ereignisse"),
    ("eventwork", "Ereignisse und Werke"),
    ("workwork", "Werke und Werke"),
)

NODE_TYPES = (
    ("person", "Person"),
    ("institution", "Institution"),
    ("place", "Ort"),
    ("event", "Ereignis"),
    ("work", "Werk"),
)


class Edge(models.Model):
    edge_id = models.IntegerField(verbose_name="ID der Kante", help_text="ID der Kante")
    edge_kind = models.CharField(
        max_length=100,
        choices=EDGE_TYPES,
        verbose_name="Kantentyp",
        help_text="Art der Beziehung (Personen und Orte, Werke und Werke, ...)",
    )
    source_label = models.CharField(
        max_length=250,
        verbose_name="Name der Quelle",
        help_text="Name der Quelle",
    )
    source_kind = models.CharField(
        max_length=250,
        verbose_name="Art der Quelle",
        help_text="Art der Quelle (Person, Ort, Werk, Institution, Ereignis)",
    )
    source_id = models.IntegerField(
        verbose_name="ID der Quelle", help_text="ID der Quelle"
    )
    edge_label = models.CharField(
        max_length=250,
        verbose_name="Art der Beziehung",
        help_text="Art der Beziehung von Quell- und Zielknoten",
    )
    target_label = models.CharField(
        max_length=250,
        verbose_name="Name des Ziels",
        help_text="Name des Ziels",
    )
    target_kind = models.CharField(
        max_length=250,
        verbose_name="Art des Ziels",
        help_text="Art des Ziels (Person, Ort, Werk, Institution, Ereignis)",
    )
    target_id = models.IntegerField(
        verbose_name="ID des Ziels", help_text="ID des Ziels"
    )
    start_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="Beginn der Beziehung",
        help_text="Beginn der Beziehung (YYYY-MM-DD)",
    )
    end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="Ende der Beziehung",
        help_text="Ende der Beziehung (YYYY-MM-DD)",
    )

    class Meta:
        verbose_name = ("Kante",)
        verbose_name_plural = "Kanten"
        ordering = ["-id"]

    def __str__(self):
        return f"{self.source_label}, {self.edge_label}, {self.target_label}"
