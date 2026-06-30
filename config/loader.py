from pathlib import Path
import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent
MANIFEST_FILE = ROOT_DIR / "manifest.yaml"


def load_manifest():
    if not MANIFEST_FILE.exists():
        raise FileNotFoundError(
            f"Manifesto não encontrado:\n{MANIFEST_FILE}"
        )

    with MANIFEST_FILE.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)