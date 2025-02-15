document.addEventListener("DOMContentLoaded", () => {
    const fileInput = document.getElementById("fileInput");
    const dropZone = document.getElementById("dropZone");
    const analyzeBtn = document.getElementById("analyzeBtn");
    const previewImage = document.getElementById("previewImage");
    const resultContainer = document.getElementById("resultContainer");
    const loadingSpinner = document.getElementById("loadingSpinner");

    dropZone.addEventListener("click", () => {
        fileInput.click();
    });

    fileInput.addEventListener("change", () => {
        const file = fileInput.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                previewImage.src = e.target.result;
                previewImage.style.display = "block";
                analyzeBtn.style.display = "block";
            };
            reader.readAsDataURL(file);
        }
    });

    analyzeBtn.addEventListener("click", async () => {
        const file = fileInput.files[0];
        if (!file) {
            alert("이미지를 선택하세요.");
            return;
        }

        const formData = new FormData();
        formData.append("image", file);

        loadingSpinner.style.display = "block";
        analyzeBtn.style.display = "none";
        resultContainer.style.display = "none";  // 결과 컨테이너 초기화
        resultContainer.innerHTML = "";

        try {
            const response = await fetch("http://localhost:3000/analyze", {
                method: "POST",
                body: formData,
            });

            const data = await response.json();
            loadingSpinner.style.display = "none";
            resultContainer.style.display = "block";  // 결과 컨테이너 표시

            if (data.error) {
                resultContainer.innerHTML = `<p class="error">${data.error}</p>`;
            } else {
                resultContainer.innerHTML = `
                    <p class="success">분석 결과: ${data.vulnerability_score}% 취약</p>
                    <p class="description">점수가 높을수록 딥페이크 변조에 취약합니다.</p>
                `;
            }
            analyzeBtn.style.display = "block";  // 분석 버튼 다시 표시
        } catch (error) {
            console.error("분석 중 오류 발생했습니다:", error);
            resultContainer.style.display = "block";
            resultContainer.innerHTML = `<p class="error">서버 오류 발생! 다시 시도하세요.</p>`;
            loadingSpinner.style.display = "none";
            analyzeBtn.style.display = "block";
        }
    });
});