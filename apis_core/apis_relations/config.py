import django_tables2 as tables

FIELDS_TO_EXCLUDE = [
    "start_start_date",
    "start_end_date",
    "end_start_date",
    "end_end_date",
    "status",
    "source",
    "published",
    "tempentityclass_ptr",
    "review",
    "name",
    "img_url",
    "img_last_checked",
]


CRUD_COLUMN = tables.TemplateColumn(
    """
        <a href="{{ record.get_edit_url }}">
            <i class="bi bi-pencil-square p-1 fs-5" title="Verbindung bearbeiten" aria-hidden="true">
                <span class="visually-hidden">Verbindung bearbeiten</span>
            </i>
        </a>
        <i class="bi bi-clipboard p-1 fs-5"></i>
        <i class="bi bi-trash p-1 fs-5"></i>
    """,
    verbose_name="Ändern, Kopieren oder Löschen",
)