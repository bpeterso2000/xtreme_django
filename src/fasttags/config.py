import os

class FastTagConfig:
    def __init__(self):
        self.enable_validation: bool = False
        self.escape_by_default: bool = True
        self.pretty_print: bool = False
        self.indent_size: int = 2
        self.auto_heal: bool = False
        self.heal_fuzzy: bool = False  # New: Opt-in for fuzzy attribute healing
        self.validate_mode: str = os.environ.get('FASTTAG_VALIDATE_MODE', 'none')  # Env var support

config = FastTagConfig()
