import cv2
import numpy as np
import sys
import json

def check_image_quality(image):
    """이미지 품질 검사"""
    # 이미지 크기 확인
    height, width = image.shape[:2]
    if width < 512 or height < 512:
        return False, "이미지 해상도가 너무 낮습니다"
    
    # 이미지 선명도 확인
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    if laplacian_var < 100:
        return False, "이미지가 흐릿합니다"
    
    return True, "이미지 품질이 양호합니다"

def check_face_visibility(image):
    """얼굴 가시성 검사"""
    # 얼굴 검출기 로드
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    # 그레이스케일 변환
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 얼굴 검출
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    
    if len(faces) == 0:
        return False, "이미지에서 얼굴을 찾을 수 없습니다"
    
    # 가장 큰 얼굴 영역 찾기
    max_face = max(faces, key=lambda x: x[2] * x[3])
    face_area = max_face[2] * max_face[3]
    total_area = image.shape[0] * image.shape[1]
    face_ratio = face_area / total_area
    
    if face_ratio < 0.1:
        return False, "얼굴이 너무 작게 보입니다"
    
    return True, "얼굴이 잘 보입니다"

def check_background(image):
    """배경 검사"""
    # 엣지 검출
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    
    # 배경 복잡도 계산
    edge_density = np.sum(edges > 0) / (image.shape[0] * image.shape[1])
    
    if edge_density > 0.1:
        return False, "배경이 너무 복잡합니다"
    
    return True, "배경이 단순합니다"

def analyze_image_vulnerability(image_path):
    """이미지 취약성 분석"""
    try:
        # 이미지 로드
        image = cv2.imread(image_path)
        if image is None:
            return json.dumps({'error': '이미지를 불러올 수 없습니다.'})

        # 각 항목별 검사
        quality_ok, quality_msg = check_image_quality(image)
        face_ok, face_msg = check_face_visibility(image)
        background_ok, background_msg = check_background(image)

  #취약성 점수 계산 (기본 100점에서 감점)
        score = 100
        if not quality_ok:
            score -= 30
        if not face_ok:
            score -= 40
        if not background_ok:
            score -= 20

        # 최종 점수는 0-100 사이로 조정
        score = max(0, min(100, score))

        result = {
            'vulnerability_score': score,
            'details': {
                'image_quality': quality_msg,
                'face_visibility': face_msg,
                'background': background_msg
            }
        }
        return json.dumps(result)

    except Exception as e:
        return json.dumps({'error': '분석 중 오류가 발생했습니다.', 'details': str(e)})

if __name__ == "__main__":
    image_path = sys.argv[1]
    analysis_result = analyze_image_vulnerability(image_path)
    print(analysis_result)
