from core.banner import show_banner
from core.logger import info
from config.loader import load_manifest


class Engine:

    def __init__(self):

        self.manifest = None

    def boot(self):

        show_banner()

        info("Loading manifest...")

        self.manifest = load_manifest()

        info("Manifest loaded.")

        info("CRS Wiki Engine initialized successfully.")