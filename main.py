from services.manifest_service import ManifestService


def main():

    manifest = ManifestService()

    manifest.load()

    print("\n=== Registered Portals ===\n")

    for portal in manifest.get_portals():

        print(
            f"{portal.name} ({portal.difficulty})"
        )


if __name__ == "__main__":
    main()