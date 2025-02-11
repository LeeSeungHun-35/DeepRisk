document.getElementById('uploadBtn').addEventListener('click', async () => { // '업로드' 버튼 클릭 시 이벤트 리스너 추가
    const fileInput = document.getElementById('imageInput'); // 이미지 입력 요소 가져오기
    const file = fileInput.files[0]; // 선택한 첫 번째 파일 가져오기

    if (!file) { // 파일이 선택되지 않은 경우
        alert('이미지를 선택하세요.'); // 이미지 선택 요청 알림
        return; // 함수 종료
    }

    const formData = new FormData(); // 폼 데이터 객체 생성
    formData.append('image', file); // 'image' 키에 파일 추가

    try {
        const response = await fetch('/analyze', { // '/analyze' 엔드포인트로 POST 요청
            method: 'POST', // HTTP 메소드: POST
            body: formData // 폼 데이터 본문으로 전송
        });

        const data = await response.json(); // 서버 응답을 JSON 형식으로 변환
        document.getElementById('result').innerHTML = `<p>분석 결과: ${data.vulnerability_score}% 취약</p>`; // 분석 결과를 HTML에 출력
    } catch (error) { // 에러 발생 시
        console.error('분석 중 오류 발생:', error); // 콘솔에 오류 출력
        document.getElementById('result').innerHTML = `<p>오류 발생! 다시 시도하세요.</p>`; // 오류 메시지 출력
    }
});