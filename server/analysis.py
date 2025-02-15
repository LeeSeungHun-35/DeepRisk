import cv2
import mediapipe as mp
import numpy as np
import json

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=True)

def detect_face_landmarks(image):
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_image)
    return results.multi_face_landmarks[0].landmark if results.multi_face_landmarks else None

def detect_blur(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()

if __name__ == "__main__":
    image_path = "face.jpg"
    image = cv2.imread(image_path)

    if image is None:
        print(json.dumps({"error": "이미지를 로드할 수 없습니다."}))
    else:
        landmarks = detect_face_landmarks(image)
        blur_score = detect_blur(image) if landmarks else 0
        result = {"vulnerability_score": blur_score}
        print(json.dumps(result))
