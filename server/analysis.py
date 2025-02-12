import sys
import cv2
import numpy as np
import json
from PIL import Image, ExifTags
import dlib

    #얼굴 정면도 계산을 위한 모델 로드
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")  #얼굴 랜드마크 예측기 로드

def calculate_face_score(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    faces = detector(gray)

    if len(faces) == 0:
        return 0  #얼굴이 검출되지 않으면 0점
    
    face_score = 0
    for face in faces:
        landmarks = predictor(gray, face)

        left_eye = (landmarks.part(36).x, landmarks.part(36).y)
        right_eye = (landmarks.part(45).x, landmarks.part(45).y)
        nose = (landmarks.part(30).x, landmarks.part(30).y)

        eye_vector = np.array([right_eye[0] - left_eye[0], right_eye[1] - left_eye[1]])
        nose_vector = np.array([nose[0] - left_eye[0], nose[1] - left_eye[1]])

        dot_product = np.dot(eye_vector, nose_vector)
        eye_magnitude = np.linalg.norm(eye_vector)
        nose_magnitude = np.linalg.norm(nose_vector)
        cosine_similarity = dot_product / (eye_magnitude * nose_magnitude)
        
                 #코사인 유사도 값에서 각도 계산 (0 ~ 180도 범위)
        angle = np.arccos(cosine_similarity) * 180 / np.pi

        #각도에 따른 점수 부여 (정면일수록 100, 옆을 향할수록 낮은 점수)
        if angle < 10:   #거의 정면
            face_score = 100
        elif angle < 30:
            face_score = 80
        elif angle < 50:
            face_score = 60
        elif angle < 70: 
            face_score = 40
        elif angle < 90:  
            face_score = 20
        else:  #옆모습
            face_score = 0

    return face_score

        #해상도, 밝기, 메타데이터, 얼굴 정면도, 배경 복잡도 검사 함수
def check_image_quality(image_path):
    try:
        #Pillow를 이용해 이미지 파일 형식 확인
        img = Image.open(image_path)
        img.verify()  # 이미지 파일 확인 (형식 검사)
        
        #이미지를 OpenCV로 로드
        img = cv2.imread(image_path)
        if img is None:
            return {"error": "이미지를 가져올 수 없음"}

    #해상도
        height, width, _ = img.shape
        resolution_score = min(100, (width * height) / (1920 * 1080) * 100)

#밝기
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray)
        brightness_score = max(0, min(100, (brightness / 255) * 100))

   #메타데이터(EXIF 정보)
        try:
            image = Image.open(image_path)
            exif_data = image._getexif()
            metadata_score = 100 if exif_data is not None else 50
        except Exception as e:
            metadata_score = 50  #예외 발생할 경우 기본값 설정

        #얼굴 정면도 점수 계산
        face_score = calculate_face_score(img)

                    #배경 복잡도 (단순 배경 색상 변화로 평가)
        background_complexity_score = 0
        blurred = cv2.GaussianBlur(img, (21, 21), 0)  #배경을 흐리게 처리
        diff = cv2.absdiff(img, blurred)  #차이 계산
        non_zero_count = np.count_nonzero(diff)  #차이 나는 픽셀 개수 계산
        background_complexity_score = min(100, (non_zero_count / (width * height)) * 100)

        #취약성 계산 (가중치를 둔 점수 합산)
        vulnerability_score = (
            (resolution_score * 0.2) +
            (brightness_score * 0.2) +
            (metadata_score * 0.2) +
            (face_score * 0.2) +
            (background_complexity_score * 0.2)
        )

        return {"vulnerability_score": round(vulnerability_score, 2)}

    except Exception as e:
        return {"error": f"처리 중 오류 발생: {str(e)}"}

if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            print(json.dumps({"error": "이미지 경로를 인자로 전달해 주세요."}))
            sys.exit(1)

        image_path = sys.argv[1]
        result = check_image_quality(image_path)
        print(json.dumps(result))  #JSON 형태로 출력
    except Exception as e:
        print(json.dumps({"error": f"스크립트 실행 오류: {str(e)}"}))