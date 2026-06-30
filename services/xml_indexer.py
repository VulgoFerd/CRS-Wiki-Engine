from pathlib import Path
from collections import Counter
import xml.etree.ElementTree as ET
import json


class XMLIndexer:

    def __init__(self, source_path: str):
        self.source = Path(source_path)
        self.index = {}

    def build(self):

        for xml in self.source.rglob("*.xml"):

            try:

                tree = ET.parse(xml)
                root = tree.getroot()

                counter = Counter()

                for node in root.iter():
                    counter[node.tag] += 1

                self.index[str(xml.relative_to(self.source))] = dict(counter)

            except Exception:
                continue

    def save(self):

        output = Path("workspace/reports/xml_index.json")

        output.parent.mkdir(parents=True, exist_ok=True)

        with output.open("w", encoding="utf8") as f:
            json.dump(self.index, f, indent=4)