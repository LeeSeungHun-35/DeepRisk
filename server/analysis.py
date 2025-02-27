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

# 이미지 로드
image = cv2.imread(image_path)
image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
height, width, _ = image.shape

# 얼굴 랜드마크 탐지
results = face_mesh.process(image_rgb)

# 마스크/손/가려진 부분 찾기 (Canny 엣지 검출 + 윤곽선 분석)
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
edges = cv2.Canny(gray, 50, 150)  # 엣지 검출
contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# 가려진 영역을 표시할 마스크 생성
mask = np.ones((height, width), dtype=np.uint8) * 255  # 기본값: 흰색 (얼굴 보이는 부분)
cv2.drawContours(mask, contours, -1, 0, thickness=cv2.FILLED)  # 검은색(0)으로 가려진 부분 표시

# 얼굴 랜드마크 필터링
if results.multi_face_landmarks:
    for face_landmarks in results.multi_face_landmarks:
        visible_landmarks_count = 0
        total_landmarks = 468  # MediaPipe FaceMesh의 전체 랜드마크 수

        for landmark in face_landmarks.landmark:
            x, y = round(landmark.x * width), round(landmark.y * height)  # 정수 변환 시 반올림

            # 가려진 영역(검은색)인지 확인 → 0이면 가려진 부분이므로 제외
            if 0 <= x < width and 0 <= y < height and mask[y, x] == 255:
                visible_landmarks_count += 1  # 보이는 부분만 카운트

        # 취약성 점수 계산 (가려지지 않은 랜드마크 기준)
        vulnerability_score = (visible_landmarks_count / total_landmarks) * 100

        result = {
            'vulnerability_score': vulnerability_score,
            'details': {
                'visible_landmarks_count': visible_landmarks_count,
                'total_landmarks': total_landmarks
            }
        }

        # 결과 JSON 출력
        print(json.dumps(result))

else:
    # 얼굴을 찾을 수 없으면 오류 메시지 출력
    print(json.dumps({'error': '얼굴을 감지할 수 없습니다.'}))
