from typing import Dict, Any


class WikiSchema:
    """
    Validates WikiPage structure to prevent Discord/runtime crashes.
    """

    REQUIRED_KEYS = ["meta", "boss", "loot", "phases"]

    @staticmethod
    def validate(page: Dict[str, Any]) -> bool:
        if not isinstance(page, dict):
            return False

        for key in WikiSchema.REQUIRED_KEYS:
            if key not in page:
                return False

        if not isinstance(page["meta"], dict):
            return False

        if not isinstance(page["boss"], dict):
            return False

        if not isinstance(page["loot"], dict):
            return False

        if "items" not in page["loot"]:
            page["loot"]["items"] = []

        if not isinstance(page["phases"], list):
            page["phases"] = []

        return True

    @staticmethod
    def safe(page: Dict[str, Any]) -> Dict[str, Any]:
        """
        Forces schema compliance instead of crashing.
        """
        if not isinstance(page, dict):
            page = {}

        page.setdefault("meta", {})
        page.setdefault("boss", {})
        page.setdefault("loot", {"items": []})
        page.setdefault("phases", [])

        if "items" not in page["loot"]:
            page["loot"]["items"] = []

        return page