from pathlib import Path

import yaml

from models.portal import Portal


class ManifestService:

    def __init__(self, path: Path = Path("manifest.yaml")) -> None:

        self.path = path

        self.data = {}

    def load(self) -> None:

        with self.path.open(
            "r",
            encoding="utf8"
        ) as file:

            self.data = yaml.safe_load(file)

    def get_source_path(self) -> Path:
        source = self.data.get("source", {})
        raw_path = source.get("path", "")

        if not raw_path:
            raise ValueError("source.path must be configured in manifest.yaml")

        path = Path(raw_path).expanduser()
        if path.is_absolute():
            return path

        return (self.path.parent / path).resolve()

    def get_portals(self) -> list[Portal]:

        result = []

        difficulty = self.data["difficulty"]

        for stage in difficulty:

            for portal in difficulty[stage]:

                result.append(
                    Portal(
                        name=portal,
                        difficulty=stage
                    )
                )

        return result
