# backend/config.py
import json
from pathlib import Path

# Project Root (determined dynamically)
PROJECT_ROOT = Path(__file__).parent.parent.parent  # Go up three levels from config.py
SRC_ROOT = PROJECT_ROOT / "src"

# UI Configs
WINDOW_WIDTH = 1250
WINDOW_HEIGHT = 900
LIGHT_THEME_QSS_PATH = SRC_ROOT / "UI" / "resource" / "light" / "demo.qss"
DARK_THEME_QSS_PATH = SRC_ROOT / "UI" / "resource" / "dark" / "demo.qss"
FOLDER_CLOSE_ICON_PATH = ":/qfluentwidgets/images/folder_list_dialog/Close_{c}.png"  # Consider changing this if it's not dynamic
FOLDER_ADD_ICON_PATH = ":/qfluentwidgets/images/folder_list_dialog/Add_{c}.png"    # Consider changing this if it's not dynamic
APP_ICON_PATH = SRC_ROOT / "UI" / "resource" / "logo_small-modified.png"

# Card Dimensions (These remain unchanged)
GALLERY_CARD_WIDTH = 128
GALLERY_CARD_HEIGHT = 136
GALLERY_CARD_IMAGE_HEIGHT = 78

CLASS_CARD_WIDTH = 128
CLASS_CARD_HEIGHT = 136

CLUSTERS_CARD_WIDTH = 180
CLUSTERS_CARD_HEIGHT = 198
CLUSTERS_CARD_IMAGE_HEIGHT = 145

ANALYSIS_CARD_WIDTH = 440
ANALYSIS_CARD_HEIGHT = 340
ANALYSIS_CARD_IMAGE_HEIGHT = 302

# Analysis View Configs (These remain unchanged)
DEFAULT_HISTOGRAM_BIN_COUNT = 10
HISTOGRAM_BIN_COUNT_RANGE = (5, 5000)

# Chart Fonts (These remain unchanged)
CHART_TITLE_FONT = dict(family="Arial", size=20, weight="bold")
CHART_AXIS_TITLE_FONT = dict(family="Arial", size=18, weight="bold")
CHART_DEFAULT_FONT = dict(family="Arial", size=14)

# Backend Configs
MODELS = {
    "mobilenetv3s": {
        "path": SRC_ROOT / "backend" / "resources" / "mobilenetv3_small_extractor.onnx",
        "dimension": 1024
    },
    "mobilenetv3l": {
        "path": SRC_ROOT / "backend" / "resources" / "mobilenetv3_large_extractor.onnx",
        "dimension": 1280
    },
    "dinov2s": {
        "path": SRC_ROOT / "backend" / "resources" / "dinov2_small.onnx",
        "dimension": 384
    },
    "dinov2b": {
        "path": SRC_ROOT / "backend" / "resources" / "dinov2_base.onnx",
        "dimension": 384
    },
    "hiera_huge": {
        "path": SRC_ROOT / "backend" / "resources" / "hiera_huge.onnx",
        "dimension": 384
    }
}
CLUSTERING_N_ITER = 300
CLUSTERING_N_REDO = 10
CLUSTERING_DEFAULT_N_CLUSTERS = 10
SEGMENTATION_MODEL_PATH = SRC_ROOT / "backend" / "resources" / "mobilenetv2_segmentation.onnx"

# Data Manager and Presenter Configs (These remain unchanged)
IMAGES_PER_PREVIEW = 25
COLLAGE_RES_SCALE = 0.3
SAMPLE_RES_SCALE = 0.5

DEFAULT_SETTINGS = {
    "theme": "light",
    "model": "mobilenetv3s",
    "provider": "CPUExecutionProvider",
    "thumbnail_quality": 75,
    "images_per_collage": IMAGES_PER_PREVIEW,
    "collage_res_scale": COLLAGE_RES_SCALE
}

SETTINGS_FILE = PROJECT_ROOT.parent / "settings.json"
SESSIONS_INDEX_FILE = PROJECT_ROOT.parent / "sessions_index.json"

def load_settings():
    """Loads settings from a file (or uses defaults if the file doesn't exist)."""
    try:
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
    except FileNotFoundError:
        settings = DEFAULT_SETTINGS
        save_settings(settings)  # Save default settings
    return settings

def save_settings(settings):
    """Saves settings to a file."""
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)