class LootResolver:
    def __init__(self, item_index=None):
        self.item_index = item_index or {}
        self.unknown_items = []

    def resolve_item(self, raw_name):
        item_id = self.item_index.get(raw_name)
        if not item_id:
            self.unknown_items.append(raw_name)
            return None
        return item_id

    def normalize_drop(self, drop):
        if not isinstance(drop, dict):
            return None

        raw_name = drop.get("item")
        if not raw_name:
            return None

        item_id = self.resolve_item(raw_name)
        if not item_id:
            return None

        return {
            "item_id": item_id,
            "display_name": raw_name,
            "drop_rate": float(drop.get("rate", 0.0))
        }

    def resolve_loot_table(self, source_name, drops):
        normalized_items = []
        for drop in drops or []:
            r = self.normalize_drop(drop)
            if r:
                normalized_items.append(r)

        return {
            "source": source_name,
            "type": "enemy_loot_table",
            "items": normalized_items
        }