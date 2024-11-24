import django_tables2 as tables

from network.models import Edge


class EdgeTable(tables.Table):

    class Meta:
        model = Edge
        sequence = (
            "id",
            "source_label",
            "edge_label",
            "target_label",
            "start_date",
            "end_date",
        )
