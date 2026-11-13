"""Encodes the reading direction of a relation type in autocomplete values.

For relations between entities of the same class (e.g. PersonPerson) the
current entity can be either source or target. The autocomplete therefore
offers every relation type in both readings: "1109" means "current entity
ist Elternteil von target", "1109:r" means "current entity ist Kind von
target" (i.e. the current entity is stored as target).
"""

REVERSE_SUFFIX = ":r"


def directed_relation_type_value(type_id, reverse=False):
    return f"{type_id}{REVERSE_SUFFIX}" if reverse else f"{type_id}"


def split_directed_relation_type(value):
    """
    :param value: autocomplete value like "1109" or "1109:r"
    :return: tuple of the relation type id (str) and whether the reading is reversed
    """
    value = f"{value}".strip()
    if value.endswith(REVERSE_SUFFIX):
        return value[: -len(REVERSE_SUFFIX)], True
    return value, False
