### backend/config.py
import json

# UI Configs
WINDOW_WIDTH = 1250
WINDOW_HEIGHT = 900
LIGHT_THEME_QSS_PATH = "src/UI/resource/light/demo.qss"
DARK_THEME_QSS_PATH = "src/UI/resource/dark/demo.qss"
FOLDER_CLOSE_ICON_PATH = ":/qfluentwidgets/images/folder_list_dialog/Close_{c}.png"
FOLDER_ADD_ICON_PATH = ":/qfluentwidgets/images/folder_list_dialog/Add_{c}.png"
APP_ICON_PATH = "src/UI/resource/logo_small-modified.png"

# Card Dimensions
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

# Analysis View Configs
DEFAULT_HISTOGRAM_BIN_COUNT = 10
HISTOGRAM_BIN_COUNT_RANGE = (5, 5000)

# Chart Fonts
CHART_TITLE_FONT = dict(family="Arial", size=20, weight="bold")
CHART_AXIS_TITLE_FONT = dict(family="Arial", size=18, weight="bold")
CHART_DEFAULT_FONT = dict(family="Arial", size=14)

# Backend Configs
MODELS = {
    "mobilenetv3s": {
        "path": "src/backend/resources/mobilenetv3_small_extractor.onnx",
        "dimension": 1024
    },
    "mobilenetv3l": {
        "path": "src/backend/resources/mobilenetv3_large_extractor.onnx",
        "dimension": 1280
    },
    "dinov2s": {
        "path": "src/backend/resources/dinov2_small.onnx",
        "dimension": 384
    },
    "dinov2b": {
        "path": "src/backend/resources/dinov2_base.onnx",
        "dimension": 384
    },
    "hiera_huge": {
        "path": "src/backend/resources/hiera_huge.onnx",
        "dimension": 384
    }
}
CLUSTERING_N_ITER = 300
CLUSTERING_N_REDO = 10
CLUSTERING_DEFAULT_N_CLUSTERS = 10
SEGMENTATION_MODEL_PATH = r'src/backend/resources/mobilenetv2_segmentation.onnx'

# Data Manager and Presenter Configs
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

def load_settings():
    """Loads settings from a file (or uses defaults if the file doesn't exist)."""
    settings_path = "settings.json"
    try:
        with open(settings_path, 'r') as f:
            settings = json.load(f)
    except FileNotFoundError:
        settings = DEFAULT_SETTINGS
        save_settings(settings) # Save default settings
    return settings

def save_settings(settings):
    """Saves settings to a file."""
    settings_path = "settings.json"
    with open(settings_path, 'w') as f:
        json.dump(settings, f, indent=4)
