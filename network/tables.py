import django_tables2 as tables

from network.models import Edge


class EdgeTable(tables.Table):

    source_label = tables.TemplateColumn(
        """
        <a href="{% url 'entity-resolver' record.source_id %}" class="">{{ record.source_label }}</a>
        """
    )
    target_label = tables.TemplateColumn(
        """
        <a href="{% url 'entity-resolver' record.target_id %}">{{ record.target_label }}</a>
        """
    )
    # this does not work, because the querystring template tag needs a requests object in context
    # and passing this in the matching view does not work for reasons unknown to me
    # edge_label = tables.TemplateColumn(
    #     """
    #     <a href="{{ request.get_full_path }}{% querystring edge_label=edge_label %}">
    #         {{ record.edge_label }}
    #     </a>
    #     """,
    #     extra_context={"request": None}
    # )
    edge_label = tables.TemplateColumn(
        """
        <a href="{{ request.get_full_path }}{% if '?' in request.get_full_path %}&edge_label={{ record.edge_label }}{% else %}?edge_label={{ record.edge_label }}{% endif %}">
            {{ record.edge_label }}
        </a>
        """,  # noqa:
    )

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
