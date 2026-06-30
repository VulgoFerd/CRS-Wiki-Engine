from pathlib import Path

import yaml

from models.portal import Portal


class ManifestService:

    def __init__(self):

        self.path = Path("manifest.yaml")

        self.data = {}

    def load(self):

        with self.path.open(
            "r",
            encoding="utf8"
        ) as file:

            self.data = yaml.safe_load(file)

    def get_portals(self):

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