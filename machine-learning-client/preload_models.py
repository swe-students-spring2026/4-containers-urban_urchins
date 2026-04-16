"""preload DeepFace models during image build"""

from deepface.modules import modeling


def main():
    """Download and cache the detector and emotion models used at runtime."""
    modeling.build_model(task="face_detector", model_name="retinaface")
    modeling.build_model(task="facial_attribute", model_name="Emotion")
    print("DeepFace models preloaded.")


if __name__ == "__main__":
    main()
