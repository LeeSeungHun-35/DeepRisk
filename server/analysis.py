import cv2
import mediapipe as mp
import numpy as np
import json
import sys

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=True)

def detect_face_landmarks(image):
    try:
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_image)
        if results.multi_face_landmarks:
            return results.multi_face_landmarks[0].landmark
        else:
            raise ValueError("얼굴을 찾을 수 없습니다.")
    except Exception as e:
        return {"error": f"얼굴 랜드마크 추출 중 오류 발생 : {str(e)}"}

def detect_blur(image):
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return cv2.Laplacian(gray, cv2.CV_64F).var()
    except Exception as e:
        return {"error": f"블러 점수 계산 중 오류 발생: {str(e)}"}

if __name__ == "__main__":
    try:
        # 커맨드 라인 인자로 이미지 경로 받기
        image_path = sys.argv[1] if len(sys.argv) > 1 else "face.jpg"
        image = cv2.imread(image_path)

        if image is None:
            print(json.dumps({"error": "이미지를 로드할 수 없습니다."}))
        else:
            landmarks = detect_face_landmarks(image)
            if isinstance(landmarks, dict) and "error" in landmarks:
                print(json.dumps(landmarks))
            else:
                blur_score = detect_blur(image)
                # 0-100 사이의 점수로 정규화
                normalized_score = min(100, max(0, int(blur_score * 100 / 1000)))
                result = {"vulnerability_score": normalized_score}
                print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"error": f"전체 분석 중 오류 발생: {str(e)}"}))