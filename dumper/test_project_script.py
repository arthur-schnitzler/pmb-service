import csv
import importlib.util
import json
import tempfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

SCRIPT = Path(settings.BASE_DIR) / "project_scripts" / "process_list_xml.py"
NS = 'xmlns="http://www.tei-c.org/ns/1.0"'


def list_xml(*lists):
    return f"<TEI {NS}><text><body>{''.join(lists)}</body></text></TEI>"


class ProcessListXmlTestCase(SimpleTestCase):
    """The script that projects copy to write their pmb_uris-in-use.csv."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        spec = importlib.util.spec_from_file_location("process_list_xml", SCRIPT)
        cls.script = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.script)

    def collect(self, files, **config):
        with tempfile.TemporaryDirectory() as tmp:
            for name, text in files.items():
                (Path(tmp) / name).write_text(text, encoding="utf-8")
            config = {
                "domain": "mein-projekt",
                "uri_template": "https://mein-projekt.example/{xml_id}.html",
                "index_glob": f"{tmp}/list*.xml",
                "id_pattern": r"^pmb(\d+)$",
                **config,
            }
            out = StringIO()
            with redirect_stdout(out):
                _, rows = self.script.collect(config)
        return rows, out.getvalue()

    def test_01_rows_are_sorted_by_type_and_numeric_id(self):
        rows, _ = self.collect(
            {
                "listperson.xml": list_xml(
                    '<listPerson><person xml:id="pmb10"/><person xml:id="pmb9"/></listPerson>'
                ),
                "listbibl.xml": list_xml('<listBibl><bibl xml:id="pmb2"/></listBibl>'),
            }
        )
        self.assertEqual(
            rows,
            [
                [2, "bibl", "https://mein-projekt.example/pmb2.html", "mein-projekt"],
                [9, "person", "https://mein-projekt.example/pmb9.html", "mein-projekt"],
                [
                    10,
                    "person",
                    "https://mein-projekt.example/pmb10.html",
                    "mein-projekt",
                ],
            ],
        )

    def test_02_entity_type_comes_from_the_entry_not_the_list(self):
        rows, out = self.collect(
            {
                "listperson.xml": list_xml(
                    '<listPerson><person xml:id="pmb1"/><personGrp xml:id="pmb99"/></listPerson>'
                    '<listObject><object xml:id="pmb5"/></listObject>'
                )
            }
        )
        self.assertEqual([r[:2] for r in rows], [[1, "person"]])
        self.assertIn("pmb99", out)
        self.assertIn("pmb5", out)

    def test_03_duplicates_are_skipped_and_reported(self):
        rows, out = self.collect(
            {
                "lista.xml": list_xml(
                    '<listPerson><person xml:id="pmb7"/><person xml:id="pmb007"/></listPerson>'
                    '<listPlace><place xml:id="pmb7"/></listPlace>'
                ),
                "listb.xml": list_xml(
                    '<listPerson><person xml:id="pmb7"/></listPerson>'
                ),
            }
        )
        self.assertEqual([r[:2] for r in rows], [[7, "person"], [7, "place"]])
        self.assertEqual(rows[0][2], "https://mein-projekt.example/pmb7.html")
        self.assertEqual(out.count("duplicate"), 2)

    def test_04_ids_not_matching_the_pattern_are_skipped(self):
        rows, out = self.collect(
            {"lista.xml": list_xml('<listPerson><person xml:id="foo"/></listPerson>')}
        )
        self.assertEqual(rows, [])
        self.assertIn("does not match id_pattern", out)

    def test_05_exclude_is_optional_and_skips_files(self):
        files = {
            "lista.xml": list_xml('<listPerson><person xml:id="pmb1"/></listPerson>'),
            "listb.xml": list_xml('<listPerson><person xml:id="pmb2"/></listPerson>'),
        }
        self.assertEqual(len(self.collect(files)[0]), 2)
        self.assertEqual(len(self.collect(files, exclude=["listb.xml"])[0]), 1)

    def test_06_unparsable_file_aborts(self):
        with self.assertRaises(SystemExit):
            self.collect({"lista.xml": "<TEI"})

    def test_07_lists_wrapped_in_div_or_p_are_found(self):
        rows, out = self.collect(
            {
                "listperson.xml": list_xml(
                    '<div type="index_persons"><listPerson xml:id="listperson">'
                    '<person xml:id="pmb1"/></listPerson></div>'
                ),
                "listwork.xml": list_xml(
                    '<p><listBibl xml:id="listwork"><bibl xml:id="pmb2"/></listBibl></p>'
                ),
            }
        )
        self.assertEqual([r[:2] for r in rows], [[2, "bibl"], [1, "person"]])
        self.assertEqual(out, "")

    def test_08_lists_inside_entries_are_not_searched(self):
        rows, out = self.collect(
            {
                "listperson.xml": list_xml(
                    '<listPerson><person xml:id="pmb1">'
                    '<listEvent><event xml:id="pmb50"/></listEvent>'
                    '<listBibl><bibl xml:id="pmb60"/></listBibl>'
                    '<affiliation><orgName xml:id="pmb70"/></affiliation>'
                    "</person></listPerson>"
                )
            }
        )
        self.assertEqual([r[:2] for r in rows], [[1, "person"]])
        self.assertEqual(out, "")

    def test_09_main_writes_the_contract_and_refuses_an_empty_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "listperson.xml").write_text(
                list_xml('<listPerson><person xml:id="pmb1"/></listPerson>'),
                encoding="utf-8",
            )
            config = {
                "domain": "mein-projekt",
                "uri_template": "https://mein-projekt.example/{xml_id}.html",
                "index_glob": f"{tmp}/list*.xml",
                "id_pattern": r"^pmb(\d+)$",
                "output": f"{tmp}/csv/pmb_uris-in-use.csv",
            }
            config_path = Path(tmp) / "pmb-uris.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            with redirect_stdout(StringIO()):
                self.script.sys.argv = ["process_list_xml.py", str(config_path)]
                self.script.main()
            with open(config["output"], newline="", encoding="utf-8") as f:
                self.assertEqual(
                    list(csv.reader(f)),
                    [
                        ["pmb_id", "entity_type", "uri", "domain"],
                        [
                            "1",
                            "person",
                            "https://mein-projekt.example/pmb1.html",
                            "mein-projekt",
                        ],
                    ],
                )

            Path(config["output"]).unlink()
            config["index_glob"] = f"{tmp}/gibt-es-nicht*.xml"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            with redirect_stdout(StringIO()), self.assertRaises(SystemExit):
                self.script.main()
            self.assertFalse(Path(config["output"]).exists())
