"""Constants used throughout the application."""

KNOWN_BARCODES_DIR = "known_barcode"

# UI Constants
WINDOW_MIN_WIDTH = 1000
WINDOW_MIN_HEIGHT = 800

# Theme Colors
COLORS = {
    'MAC': {
        'bg': "#2D2D2D",
        'accent': "#0073BB",
        'hover': "#0095EE",
        'text': "white"
    },
    'DEFAULT': {
        'bg': "#1A1A1A",
        'accent': "#0073BB",
        'hover': "#0095EE",
        'text': "white"
    }
}

# Barcode Types
BARCODE_CONFIGS = {
    "Code128": {
        "dir": "Code128",
        "patterns": ["hcX"]
    },
    "QR Code": {
        "dir": "QR",
        "patterns": ["qr", "QR"]
    },
    "DataMatrix": {
        "dir": "DataMatrix",
        "patterns": ["matrix", "dm"]
    }
}
