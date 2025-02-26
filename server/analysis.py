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

        # 랜드마크 그룹 정의
        self.EYES = list(range(133, 246))
        self.NOSE = list(range(1, 50))
        self.MOUTH = list(range(61, 131))
        self.FACE_OVAL = list(range(326, 360))

    def check_landmark_visibility(self, image, x, y, threshold=20):
        """
        주변 픽셀 분석을 통해 실제 랜드마크가 보이는지 확인
        """
        height, width = image.shape[:2]
        if not (0 <= x < width and 0 <= y < height):
            return False

        # 랜드마크 주변 영역 추출 (5x5 윈도우)
        window_size = 5
        half_size = window_size // 2
        
        x1 = max(0, x - half_size)
        x2 = min(width, x + half_size + 1)
        y1 = max(0, y - half_size)
        y2 = min(height, y + half_size + 1)
        
        window = image[y1:y2, x1:x2]
        
        if window.size == 0:
            return False

        # 그레이스케일 변환
        if len(window.shape) == 3:
            window = cv2.cvtColor(window, cv2.COLOR_BGR2GRAY)
        
        # 지역적 대비 계산
        local_std = np.std(window)
        local_mean = np.mean(window)
        
        # 엣지 검출
        gradient_x = cv2.Sobel(window, cv2.CV_64F, 1, 0, ksize=3)
        gradient_y = cv2.Sobel(window, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(gradient_x**2 + gradient_y**2)
        
        # 복합적인 가시성 점수 계산
        edge_score = np.mean(gradient_magnitude)
        contrast_score = local_std
        
        # 최종 가시성 점수
        visibility_score = (edge_score * 0.7 + contrast_score * 0.3)
        
        # 특정 랜드마크 그룹별로 다른 임계값 적용
        if x1 < 0 or x2 > width or y1 < 0 or y2 > height:
            return False
        
        # 눈 주변은 더 엄격한 임계값
        if any(idx in self.EYES for idx in range(max(0, x-10), min(width, x+10))):
            return visibility_score > threshold * 1.2
        # 입 주변은 덜 엄격한 임계값
        elif any(idx in self.MOUTH for idx in range(max(0, x-10), min(width, x+10))):
            return visibility_score > threshold * 0.8
        
        return visibility_score > threshold

    def get_visible_landmarks(self, image, landmarks):
        height, width = image.shape[:2]
        visible_landmarks = []
        landmark_groups = {
            'eyes': 0,  # 카운터로 변경
            'nose': 0,
            'mouth': 0,
            'face_oval': 0
        }

        for idx, landmark in enumerate(landmarks):
            x = int(landmark.x * width)
            y = int(landmark.y * height)

            if self.check_landmark_visibility(image, x, y):
                visible_landmarks.append(idx)
                
                # 그룹별 카운터 증가
                if idx in self.EYES:
                    landmark_groups['eyes'] += 1
                elif idx in self.NOSE:
                    landmark_groups['nose'] += 1
                elif idx in self.MOUTH:
                    landmark_groups['mouth'] += 1
                elif idx in self.FACE_OVAL:
                    landmark_groups['face_oval'] += 1

        # 각 그룹의 가시성을 비율로 판단
        min_visible_ratio = 0.3  # 30% 이상이면 해당 부위가 보인다고 판단
        
        total_landmarks = {
            'eyes': len(self.EYES),
            'nose': len(self.NOSE),
            'mouth': len(self.MOUTH),
            'face_oval': len(self.FACE_OVAL)
        }

        visible_features = {
            key: (count / total_landmarks[key]) > min_visible_ratio
            for key, count in landmark_groups.items()
        }

        return visible_landmarks, visible_features

    def calculate_vulnerability(self, visible_landmarks, visible_features, total_landmarks):
        if not visible_landmarks:
            return 0

        # 기본 점수 계산
        base_score = len(visible_landmarks) / total_landmarks * 100
        
        # 가려진 주요 특징에 따른 감점
        feature_penalty = 0
        if not visible_features['eyes']:
            feature_penalty += 25
        if not visible_features['nose']:
            feature_penalty += 15
        if not visible_features['mouth']:
            feature_penalty += 15
        if not visible_features['face_oval']:
            feature_penalty += 5

        # 최종 점수 계산
        final_score = max(0, min(100, base_score - feature_penalty))
        return int(final_score)

    def analyze_image(self, image_path):
        try:
            image = cv2.imread(image_path)
            if image is None:
                return {"error": "이미지를 불러올 수 없습니다."}
            
            # 이미지 크기 제한
            max_dimension = 1024
            height, width = image.shape[:2]
            if max(height, width) > max_dimension:
                scale = max_dimension / max(height, width)
                image = cv2.resize(image, (int(width * scale), int(height * scale)))
            
            # BGR to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # 얼굴 감지
            results = self.face_mesh.process(image_rgb)
            if not results.multi_face_landmarks:
                return {"error": "얼굴을 찾을 수 없습니다."}

            landmarks = results.multi_face_landmarks[0].landmark
            visible_landmarks, visible_features = self.get_visible_landmarks(image, landmarks)
            
            if not visible_landmarks:
                return {"error": "얼굴 특징점을 충분히 찾을 수 없습니다."}

            # 취약성 점수 계산
            vulnerability_score = self.calculate_vulnerability(
                visible_landmarks, 
                visible_features, 
                len(landmarks)
            )

            return {
                "vulnerability_score": vulnerability_score,
                "details": {
                    "visible_landmarks_count": len(visible_landmarks),
                    "total_landmarks": len(landmarks),
                    "key_features": visible_features
                }
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