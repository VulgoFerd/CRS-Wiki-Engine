from pathlib import Path
import json


class SourceAnalyzer:

    def __init__(self, source_path: str):

        self.source = Path(source_path)

        self.report = {
            "xml_files": [],
            "directories": [],
            "statistics": {}
        }

    def scan(self):

        xml_count = 0

        for file in self.source.rglob("*"):

            if file.is_dir():
                self.report["directories"].append(
                    str(file.relative_to(self.source))
                )

            elif file.suffix.lower() == ".xml":

                xml_count += 1

                self.report["xml_files"].append(
                    str(file.relative_to(self.source))
                )

        self.report["statistics"] = {
            "xml_files": xml_count,
            "directories": len(self.report["directories"])
        }

    def save(self):

        report_dir = Path("workspace/reports")

        report_dir.mkdir(parents=True, exist_ok=True)

        output = report_dir / "source_analysis.json"

        with output.open(
            "w",
            encoding="utf8"
        ) as file:

            json.dump(
                self.report,
                file,
                indent=4
            )

        print(f"\nReport saved: {output}")