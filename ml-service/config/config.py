import os

DIR_PATH = os.getenv("ML_DIR_PATH", "/app")
DATASET_PATH = os.path.join(DIR_PATH, "dataset")

LABELS_FILE_PATH = os.path.join(DATASET_PATH, "annotations", "labels.csv")
VIDEO_PATH = os.path.join(DATASET_PATH, "videos")
FEATURES_PATH = os.path.join(DATASET_PATH, "features")

MODELS_PATH = os.path.join(DIR_PATH, "models")
MODEL_YOLO_NAME = os.path.join(MODELS_PATH, "yolov8n-pose.pt")
DEFAULT_MODEL = os.path.join(MODELS_PATH, "trained_model_random_forest.pkl")

ANALYZE_MV_CONFIG = {
    "abrupt_movement_threshold": 2.5,
    "min_movement_speed": 100,
    "sampling_rate": 60,
}
