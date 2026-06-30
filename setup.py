from pathlib import Path

ROOT = Path.cwd()

folders = [
    "core",
    "config",
    "models",
    "services",
    "plugins",
    "plugins/discord",
    "plugins/parser",
    "plugins/export",
    "workspace",
    "workspace/cache",
    "workspace/database",
    "workspace/reports",
    "workspace/temp",
    "docs",
    "tests",
    "tools",
    "logs",
]

files = {
    "main.py": "",
    "manifest.yaml": "",
    "requirements.txt": "",
    ".env.example": "",
    ".gitignore": "",
    "README.md": "",
}

for folder in folders:
    path = ROOT / folder
    path.mkdir(parents=True, exist_ok=True)
    (path / "__init__.py").touch(exist_ok=True)

for file in files:
    (ROOT / file).touch(exist_ok=True)

print("\nProjeto criado com sucesso!\n")