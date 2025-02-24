import cv2
import numpy as np
import json
import logging
import os

class DeepFakeVulnerabilityAnalyzer:
    def __init__(self):
        # Haar Cascade 분류기 로드
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # 눈 검출을 위한 분류기
        eye_cascade_path = cv2.data.haarcascades + 'haarcascade_eye.xml'
        self.eye_cascade = cv2.CascadeClassifier(eye_cascade_path)

    def analyze_image(self, image_path):
        try:
            # 이미지 로드
            image = cv2.imread(image_path)
            if image is None:
                return {"error": "이미지를 불러올 수 없습니다."}
            
            # 그레이스케일 변환
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 얼굴 검출
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            if len(faces) == 0:
                return {"error": "얼굴을 찾을 수 없습니다."}
            
            # 디버그 이미지 생성
            debug_image = image.copy()
            
            # 가장 큰 얼굴 선택
            max_face = max(faces, key=lambda x: x[2] * x[3])
            x, y, w, h = max_face
            
            # 얼굴 영역 표시
            cv2.rectangle(debug_image, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # 얼굴 영역 추출
            face_roi = gray[y:y+h, x:x+w]
            
            # 눈 검출
            eyes = self.eye_cascade.detectMultiScale(face_roi)
            
            # 점수 계산을 위한 변수들
            orientation_score = 0
            visibility_score = 0
            size_score = 0
            
            # 1. 크기 점수 계산
            image_area = image.shape[0] * image.shape[1]
            face_area = w * h
            size_ratio = (face_area / image_area) * 100
            size_score = min(100, max(0, size_ratio * 3))
            
            # 2. 가시성 점수 계산
            visibility_score = 100
            # 얼굴이 이미지 경계에 너무 가까운 경우 감점
            margin = 10
            if x < margin or y < margin or \
               x + w > image.shape[1] - margin or y + h > image.shape[0] - margin:
                visibility_score -= 30
            
            # 3. 정면도 점수 계산
            if len(eyes) >= 2:  # 두 눈이 모두 검출된 경우
                orientation_score = 80
                # 눈 위치 표시
                for (ex, ey, ew, eh) in eyes:
                    cv2.rectangle(debug_image, (x+ex, y+ey), (x+ex+ew, y+ey+eh), (255, 0, 0), 2)
            else:
                orientation_score = 40
            
            # 디버그 이미지 저장
            debug_path = os.path.join(os.path.dirname(image_path), 'debug_face.jpg')
            cv2.imwrite(debug_path, debug_image)
            
            # 최종 취약성 점수 계산
            vulnerability_score = int(
                orientation_score * 0.5 +    # 정면도 (눈 검출 기반)
                visibility_score * 0.3 +     # 가시성
                size_score * 0.2             # 크기
            )
            
            return {
                "vulnerability_score": vulnerability_score,
                "details": {
                    "orientation_score": orientation_score,
                    "visibility_score": visibility_score,
                    "size_score": int(size_score),
                    "eyes_detected": len(eyes)
                }
            }

        except Exception as e:
            logging.error(f"분석 중 오류 발생: {str(e)}")
            return {"error": f"이미지 분석 중 오류가 발생했습니다: {str(e)}"}

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print(json.dumps({"error": "이미지 경로가 필요합니다."}, ensure_ascii=False))
        sys.exit(1)

    analyzer = DeepFakeVulnerabilityAnalyzer()
    result = analyzer.analyze_image(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False))