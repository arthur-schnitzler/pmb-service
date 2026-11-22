from django.apps import AppConfig


class NetworkConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "network"

    def ready(self):
        from django.db.models.signals import post_delete

        from apis_core.apis_relations.models import AbstractRelation
        from network.models import Edge

        def delete_edge(sender, instance, **kwargs):
            Edge.objects.filter(
                edge_id=instance.pk, edge_kind=sender.__name__.lower()
            ).delete()

        for relation_class in AbstractRelation.get_all_relation_classes():
            post_delete.connect(
                delete_edge,
                sender=relation_class,
                weak=False,
                dispatch_uid="network.delete_relation_edge",
            )
