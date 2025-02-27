import cv2
import mediapipe as mp
import sys
import numpy as np
import json

# 이미지 경로
image_path = sys.argv[1]

# MediaPipe Face Mesh 모델 초기화
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

# 이미지 로드
image = cv2.imread(image_path)
image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
height, width, _ = image.shape

# 얼굴 랜드마크 탐지
results = face_mesh.process(image_rgb)

# 얼굴 랜드마크의 개수를 카운트
if results.multi_face_landmarks:
    for face_landmarks in results.multi_face_landmarks:
        landmarks = face_landmarks.landmark
        skin_landmarks = [landmark for i, landmark in enumerate(landmarks) if i in range(0, 468)]  # 얼굴 전체 랜드마크

        # 랜드마크가 많을수록 딥페이크 취약성이 높다고 판단
        visible_landmarks_count = len(skin_landmarks)
        total_landmarks = 468  # MediaPipe FaceMesh는 최대 468개의 랜드마크를 제공합니다.

        vulnerability_score = (visible_landmarks_count / total_landmarks) * 100

        result = {
            'vulnerability_score': vulnerability_score,
            'details': {
                'visible_landmarks_count': visible_landmarks_count,
                'total_landmarks': total_landmarks
            }
        }

        # 결과를 JSON 형식으로 출력
        print(json.dumps(result))

else:
    # 얼굴을 찾을 수 없으면 오류 메시지 출력
    print(json.dumps({'error': '얼굴을 감지할 수 없습니다.'}))
