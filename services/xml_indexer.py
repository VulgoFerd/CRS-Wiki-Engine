from pathlib import Path
from collections import Counter
import xml.etree.ElementTree as ET
import json


class XMLIndexer:

    def __init__(self, source_path: str):

        self.source = Path(source_path)

        self.index = {}

        self.statistics = {
            "processed": 0,
            "failed": 0,
            "elements": Counter(),
        }

    def build(self):

        for xml in self.source.rglob("*.xml"):

            try:

                tree = ET.parse(xml)
                root = tree.getroot()

                counter = Counter()
                node_count = 0

                for node in root.iter():

                    counter[node.tag] += 1
                    self.statistics["elements"][node.tag] += 1
                    node_count += 1

                self.index[str(xml.relative_to(self.source))] = {
                    "root": root.tag,
                    "nodes": node_count,
                    "tags": dict(counter),
                }

                self.statistics["processed"] += 1

            except Exception as error:

                self.statistics["failed"] += 1

                print(f"Failed to parse '{xml}': {error}")

    def save(self):

        output = Path("workspace/reports/xml_index.json")

        output.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "statistics": {
                "processed": self.statistics["processed"],
                "failed": self.statistics["failed"],
                "elements": dict(self.statistics["elements"]),
            },
            "files": self.index,
        }

        with output.open("w", encoding="utf8") as file:

            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False,
            )