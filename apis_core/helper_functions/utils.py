def get_child_classes(objids, obclass, labels=False):
    """used to retrieve a list of primary keys of sub classes"""
    if labels:
        labels_lst = []
    for obj in objids:
        obj = obclass.objects.get(pk=obj)
        p_class = list(obj.vocabsbaseclass_set.all())
        p = p_class.pop() if len(p_class) > 0 else False
        while p:
            if p.pk not in objids:
                if labels:
                    labels_lst.append((p.pk, p.label))
                objids.append(p.pk)
            p_class += list(p.vocabsbaseclass_set.all())
            p = p_class.pop() if len(p_class) > 0 else False
    if labels:
        return (objids, labels_lst)
    else:
        return objids
