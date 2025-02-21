import os
import logging
import sys
import warnings
import cv2
import mediapipe as mp
import numpy as np
import json
import torch
import absl.logging
from facenet_pytorch import InceptionResnetV1
from torchvision import transforms
from PIL import Image

warnings.filterwarnings('ignore')

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  #모든 로그 숨기기
logging.getLogger('tensorflow').setLevel(logging.ERROR)

import absl.logging
absl.logging.set_verbosity(absl.logging.ERROR)
logging.root.removeHandler(absl.logging._absl_handler)
absl.logging._warn_preinit_stderr = False

class DummyFile:
    def write(self, x): pass
    def flush(self): pass
sys.stderr = DummyFile()

class DeepFakeVulnerabilityAnalyzer:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )

        self.facenet = InceptionResnetV1(pretrained='vggface2').eval()
        
        self.transform = transforms.Compose([
            transforms.Resize((160, 160)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
        ])

    def extract_face_features(self, image):
        """얼굴의 주요 특징들을 추출"""
        results = self.face_mesh.process(image)
        if not results.multi_face_landmarks:
            return None, "얼굴을 찾을 수 없습니다."

        landmarks = results.multi_face_landmarks[0].landmark
        h, w = image.shape[:2]

        features = {
            'face_alignment': self._calculate_face_alignment(landmarks),
            'skin_texture': self._analyze_skin_texture(image, landmarks),
            'facial_symmetry': self._calculate_facial_symmetry(landmarks, w, h),
            'feature_distinctiveness': self._calculate_feature_distinctiveness(landmarks),
            'image_quality': self._analyze_image_quality(image)
        }
        
        return features, None

    def _calculate_face_alignment(self, landmarks):
        left_eye = np.mean([[landmarks[33].x, landmarks[33].y]], axis=0)
        right_eye = np.mean([[landmarks[263].x, landmarks[263].y]], axis=0)
        nose = np.array([landmarks[4].x, landmarks[4].y])
        
        eye_line = right_eye - left_eye
        angle = np.abs(np.arctan2(eye_line[1], eye_line[0])) * 180 / np.pi
        
        alignment_score = 1 - min(abs(90 - angle) / 90, 1)
        return alignment_score

    def _analyze_skin_texture(self, image, landmarks):
        face_region = self._get_face_region(image, landmarks)
        if face_region is None:
            return 0.5

        gray = cv2.cvtColor(face_region, cv2.COLOR_RGB2GRAY)
        texture_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        return min(texture_score / 1000, 1)

    def _calculate_facial_symmetry(self, landmarks, width, height):
        center_x = width / 2
        symmetry_points = [
            (33, 263),
            (61, 291),
            (57, 287),
        ]
        
        symmetry_scores = []
        for left, right in symmetry_points:
            left_point = np.array([landmarks[left].x * width, landmarks[left].y * height])
            right_point = np.array([landmarks[right].x * width, landmarks[right].y * height])
            
            diff = abs(center_x - left_point[0]) - abs(center_x - right_point[0])
            symmetry_scores.append(1 - min(abs(diff) / center_x, 1))
        
        return np.mean(symmetry_scores)

    def _calculate_feature_distinctiveness(self, landmarks):
        feature_points = [
            (33, 133),
            (61, 291),
            (13, 14),
            (4, 152),
        ]
        
        distances = []
        for p1, p2 in feature_points:
            point1 = np.array([landmarks[p1].x, landmarks[p1].y])
            point2 = np.array([landmarks[p2].x, landmarks[p2].y])
            distances.append(np.linalg.norm(point2 - point1))
        
        distinctiveness = np.std(distances) / np.mean(distances)
        return min(distinctiveness, 1)

    def _analyze_image_quality(self, image):

        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        noise = cv2.fastNlMeansDenoising(gray)
        noise_level = np.mean(np.abs(gray - noise))
        
        quality_score = (1 - (noise_level / 255)) * 0.5 + (min(sharpness / 1000, 1)) * 0.5
        return quality_score

    def _get_face_region(self, image, landmarks):

        h, w = image.shape[:2]
        points = np.array([[int(landmark.x * w), int(landmark.y * h)] 
                          for landmark in landmarks])
        
        rect = cv2.boundingRect(points)
        x, y, w, h = rect
        
        if x < 0 or y < 0 or x + w > image.shape[1] or y + h > image.shape[0]:
            return None
            
        return image[y:y+h, x:x+w]

    def predict_vulnerability(self, features):

        weights = {
            'face_alignment': 0.25,
            'skin_texture': 0.2,
            'facial_symmetry': 0.2,
            'feature_distinctiveness': 0.15,
            'image_quality': 0.2
        }
        
        vulnerability_score = sum(features[k] * weights[k] for k in weights)
        
        return int(vulnerability_score * 100)

    def analyze_image(self, image_path):
        try:
            image = cv2.imread(image_path)
            if image is None:
                return {"error": "이미지를 불러올 수 없습니다."}
            
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # 이미지 크기 확인
            if image.size == 0:
                return {"error": "잘못된 이미지 형식입니다."}
                
            features, error = self.extract_face_features(image)
            if error:
                return {"error": error}
            
            vulnerability_score = self.predict_vulnerability(features)
            
            # 결과에 상세 설명 추가
            risk_level = "높음" if vulnerability_score > 70 else "중간" if vulnerability_score > 40 else "낮음"
            
            return {
                "vulnerability_score": vulnerability_score,
                "risk_level": risk_level,
                "details": features
            }

        except Exception as e:
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