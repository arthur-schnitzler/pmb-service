from django import template

register = template.Library()


@register.simple_tag
def smart_page_range(current, num_pages, delta=2):
    """Return a list of page numbers with None as ellipsis placeholder."""
    pages = []
    left = max(1, current - delta)
    right = min(num_pages, current + delta)

    if left > 1:
        pages.append(1)
        if left > 2:
            pages.append(None)

    pages.extend(range(left, right + 1))

    if right < num_pages:
        if right < num_pages - 1:
            pages.append(None)
        pages.append(num_pages)

    return pages
