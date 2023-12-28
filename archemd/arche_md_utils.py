from rdflib import RDF, XSD, Graph, Literal, Namespace, URIRef

from apis_core.apis_metainfo.models import TempEntityClass


class ArcheMd:
    """simple class to express basic info about an entity in ARCHE-MD schema"""

    def return_graph(self):
        g = Graph()
        subj = URIRef(self.uri)
        g.add((subj, RDF.type, self.ARCHE[self.arche_class]))
        g.add((subj, self.ARCHE["hasIdentifier"], subj))
        if self.entity_class_name == "person":
            g.add(
                (
                    subj,
                    self.ARCHE["hasTitle"],
                    Literal(
                        f"{self.entity.name}, {self.entity.first_name}", lang="und"
                    ),
                )
            )
            g.add(
                (
                    subj,
                    self.ARCHE["hasUrl"],
                    Literal(self.detail_view_url, datatype=XSD.anyURI),
                )
            )
        else:
            g.add(
                (
                    subj,
                    self.ARCHE["hasTitle"],
                    Literal(f"{self.entity.name}", lang="und"),
                )
            )
        for x in self.entity_uris:
            g.add((subj, self.ARCHE["hasIdentifier"], URIRef(x)))
        try:
            g.add((subj, self.ARCHE["hasLatitude"], Literal(f"{self.entity.lat}")))
            g.add((subj, self.ARCHE["hasLongitude"], Literal(f"{self.entity.lng}")))
        except AttributeError:
            pass
        for x in self.other_pmb_ids:
            g.add((subj, self.ARCHE["hasIdentifier"], URIRef(x)))
        return g

    def __init__(self, entity_id):
        self.ARCHE = Namespace("https://vocabs.acdh.oeaw.ac.at/schema#")
        self.entity_id = entity_id
        self.uri = f"https://pmb.acdh.oeaw.ac.at/entity/{self.entity_id}/"
        self.item = TempEntityClass.objects.get(id=entity_id)
        self.entity = self.item.get_child_entity()
        self.entity_class_name = self.entity.__class__.__name__.lower()
        self.detail_view_url = f"https://pmb.acdh.oeaw.ac.at{self.entity.get_absolute_url()}"
        if self.entity_class_name == "institution":
            self.arche_class = "Organization"
        else:
            self.arche_class = self.entity_class_name.capitalize()
        self.all_entity_uris = [x.uri for x in self.entity.uri_set.all()]
        self.entity_uris = [
            x
            for x in self.all_entity_uris
            if "gnd" in x or "geonames" in x or "wikidata" in x
        ]
        self.other_pmb_ids = [
            x for x in self.all_entity_uris if "https://pmb.acdh.oeaw.ac.at" in x
        ]
