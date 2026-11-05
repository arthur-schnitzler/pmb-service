from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from dumper.uri_sync import (
    UriSyncError,
    apply_plan,
    build_plan,
    check_delete_ratio,
    load_csv,
)

EXAMPLES = 10


class Command(BaseCommand):
    help = """syncs the uris of the projects listed in settings.PMB_URI_SOURCES with their pmb_uris-in-use.csv\
        e.g. python manage.py sync_uris_in_use --domain schnitzler-briefe --dry-run"""

    def add_arguments(self, parser):
        parser.add_argument(
            "--domain",
            type=str,
            help="only sync this project, default: all projects in PMB_URI_SOURCES",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="only report what would be added, changed and deleted",
        )
        parser.add_argument(
            "--max-delete-ratio",
            type=float,
            default=0.05,
            help="abort a project if more than this share of its uris would be deleted",
        )

    def handle(self, *args, **options):
        sources = settings.PMB_URI_SOURCES
        if options["domain"]:
            if options["domain"] not in sources:
                raise CommandError(
                    f"{options['domain']} is not in PMB_URI_SOURCES ({', '.join(sources)})"
                )
            sources = {options["domain"]: sources[options["domain"]]}
        if not sources:
            raise CommandError("PMB_URI_SOURCES is empty")

        failed = []
        for domain, url in sources.items():
            self.stdout.write(f"{domain}: {url}")
            try:
                plan = build_plan(domain, load_csv(url, domain))
                self.report(plan, options["dry_run"])
                check_delete_ratio(plan, options["max_delete_ratio"])
                if not options["dry_run"]:
                    apply_plan(plan)
            except UriSyncError as e:
                self.stderr.write(f"{domain}: {e}")
                failed.append(domain)
        if failed:
            raise CommandError(f"aborted for {', '.join(failed)}")

    def report(self, plan, dry_run):
        sections = [
            ("added", [f"{e}: {u}" for e, u in plan.to_add]),
            ("changed", [f"{o.entity_id}: {o.uri} -> {n}" for o, n in plan.to_change]),
            ("deleted", [f"{u.entity_id}: {u.uri}" for u in plan.to_delete]),
            (
                "already merged into another entity",
                [f"{p}: {u} (now {e})" for p, u, e in plan.merged],
            ),
            (
                "skipped",
                [f"{t} {p}: {u} ({reason})" for t, p, u, reason in plan.skipped],
            ),
            (
                "conflicts",
                [
                    f"{e}: {u} (held by entity {h.entity_id}, domain {h.domain!r})"
                    for e, u, h in plan.conflicts
                ],
            ),
        ]
        dry = " (dry run)" if dry_run else ""
        self.stdout.write(
            f"{plan.domain}{dry}: "
            + ", ".join(f"{len(items)} {name}" for name, items in sections)
        )
        for name, items in sections:
            for item in items[:EXAMPLES]:
                self.stdout.write(f"  {name}: {item}")
            if len(items) > EXAMPLES:
                self.stdout.write(f"  {name}: ... and {len(items) - EXAMPLES} more")
