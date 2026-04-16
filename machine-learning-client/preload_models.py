"""Preload DeepFace models during image build."""

import os

os.environ["TF_USE_LEGACY_KERAS"] = "1"

from deepface import DeepFace


def main():
    """Download and cache the detector and emotion models used at runtime."""
    DeepFace.build_model("retinaface", task="face_detector")
    DeepFace.build_model("Emotion", task="facial_attribute")
    print("DeepFace models preloaded.")


if __name__ == "__main__":
    main()
