import os
import logging
import sys
import warnings
import cv2
import mediapipe as mp
import numpy as np
import json

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.ERROR) 
class DeepFakeVulnerabilityAnalyzer:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )
        
        self.EYES = list(range(133, 246))  #눈 주변
        self.NOSE = list(range(1, 50))     #코 주변 
        self.MOUTH = list(range(61, 131))  #입 주변 
        self.FACE_OVAL = list(range(326, 360))  #얼굴 윤곽 

    def get_landmark_visibility(self, landmarks, image):
        height, width = image.shape[:2]
        visible_landmarks = []
        landmark_scores = []

        for idx, landmark in enumerate(landmarks):
            #3D 좌표를 2D 이미지 좌표로
            x, y = int(landmark.x * width), int(landmark.y * height)
            
            #이미지 경계 체크
            if not (0 <= x < width and 0 <= y < height):
                continue
                
            weight = 1.0
            if idx in self.EYES:
                weight = 1.5  #눈 주변은 중요
            elif idx in self.NOSE:
                weight = 1.2  #코 주변
            elif idx in self.FACE_OVAL:
                weight = 0.8  #얼굴 윤곽
                
            brightness = np.mean(image[y-1:y+2, x-1:x+2])  #3x3 영역의 평균 밝기
            visibility_score = (brightness / 255.0) * weight
            
            if visibility_score > 0.3:  
                visible_landmarks.append(idx)
                landmark_scores.append(visibility_score)

        return visible_landmarks, landmark_scores

    def calculate_vulnerability(self, visible_landmarks, landmark_scores, total_landmarks):
        if not visible_landmarks:
            return 0

        base_score = len(visible_landmarks) / total_landmarks * 100
        
        #중요 특징점 체크
        important_features = {
            'eyes': any(idx in self.EYES for idx in visible_landmarks),
            'nose': any(idx in self.NOSE for idx in visible_landmarks),
            'mouth': any(idx in self.MOUTH for idx in visible_landmarks),
            'face_oval': any(idx in self.FACE_OVAL for idx in visible_landmarks)
        }
        
           #중요 특징이 부족하면 점수 감소
        missing_features = sum(1 for present in important_features.values() if not present)
        feature_penalty = missing_features * 15
        
    #최종 점수 계산
        final_score = max(0, min(100, base_score - feature_penalty))
        
        return int(final_score)

    def analyze_image(self, image_path):
        try:
            image = cv2.imread(image_path)
            if image is None:
                return {"error": "이미지를 불러올 수 없습니다."}
            
              #이미지 크기 제한
            max_dimension = 1024
            height, width = image.shape[:2]
            if max(height, width) > max_dimension:
                scale = max_dimension / max(height, width)
                image = cv2.resize(image, (int(width * scale), int(height * scale)))
            
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            #얼굴 감지
            results = self.face_mesh.process(image_rgb)
            if not results.multi_face_landmarks:
                return {"error": "얼굴을 찾을 수 없습니다."}

            landmarks = results.multi_face_landmarks[0].landmark
            visible_landmarks, landmark_scores = self.get_landmark_visibility(landmarks, image)
            
            if not visible_landmarks:
                return {"error": "얼굴 특징점을 충분히 찾을 수 없습니다."}

            #취약성 점수 계산
            vulnerability_score = self.calculate_vulnerability(
                visible_landmarks, 
                landmark_scores, 
                len(landmarks)
            )

            #상세 분석 정보
            details = {
                "visible_landmarks_count": len(visible_landmarks),
                "total_landmarks": len(landmarks),
                "key_features": {
                    "eyes_detected": any(idx in self.EYES for idx in visible_landmarks),
                    "nose_detected": any(idx in self.NOSE for idx in visible_landmarks),
                    "mouth_detected": any(idx in self.MOUTH for idx in visible_landmarks),
                    "face_oval_detected": any(idx in self.FACE_OVAL for idx in visible_landmarks)
                }
            }

            return {
                "vulnerability_score": vulnerability_score,
                "details": details
            }

        except Exception as e:
            logging.error(f"Error during image analysis: {str(e)}")
            return {"error": f"이미지 분석 중 오류 발생: {str(e)}"}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "이미지 경로가 제공되지 않았습니다."}, ensure_ascii=False))
        sys.exit(1)
        
    analyzer = DeepFakeVulnerabilityAnalyzer()
    image_path = sys.argv[1]
    
    if not os.path.exists(image_path):
        print(json.dumps({"error": "이미지 파일을 찾을 수 없습니다."}, ensure_ascii=False))
        sys.exit(1)
        
    result = analyzer.analyze_image(image_path)
    print(json.dumps(result, ensure_ascii=False))