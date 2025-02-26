document.addEventListener("DOMContentLoaded", () => {
    const fileInput = document.getElementById("fileInput");
    const dropZone = document.getElementById("dropZone");
    const analyzeBtn = document.getElementById("analyzeBtn");
    const previewImage = document.getElementById("previewImage");
    const resultContainer = document.getElementById("resultContainer");
    const loadingSpinner = document.getElementById("loadingSpinner");

//드래그 앤 드롭
    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.classList.add("dragover");
    });

    dropZone.addEventListener("dragleave", () => {
        dropZone.classList.remove("dragover");
    });

    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.classList.remove("dragover");
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith("image/")) {
            fileInput.files = e.dataTransfer.files;
            handleFilePreview(file);
        } else {
            alert("이미지 파일만 업로드 가능합니다.");
        }
    });

    dropZone.addEventListener("click", () => {
        fileInput.click();
    });

    fileInput.addEventListener("change", () => {
        const file = fileInput.files[0];
        if (file) {
            handleFilePreview(file);
        }
    });

//파일 미리보기 처리 
    function handleFilePreview(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImage.src = e.target.result;
            previewImage.style.display = "block";
            analyzeBtn.style.display = "block";
        };
        reader.readAsDataURL(file);
    }

 //분석 버튼 클릭
    analyzeBtn.addEventListener("click", async () => {
        const file = fileInput.files[0];
        if (!file) {
            alert("이미지를 선택하세요.");
            return;
        }

        //파일 크기 10MB 제한
        if (file.size > 10 * 1024 * 1024) {
            alert("파일 크기는 10MB 이하여야 합니다.");
            return;
        }

        const formData = new FormData();
        formData.append("image", file);

        loadingSpinner.style.display = "block";
        analyzeBtn.style.display = "none";
        resultContainer.style.display = "none";
        resultContainer.innerHTML = "";

        try {
            const response = await fetch("http://localhost:3000/analyze", {
                method: "POST",
                body: formData,
            });

            const data = await response.json();
            console.log("Received data from server:", data);

            loadingSpinner.style.display = "none";
            resultContainer.style.display = "block";

            if (data.error) {
                resultContainer.innerHTML = `
                    <p class="error">
                        <strong>분석 실패:</strong> ${data.error}
                        ${data.details ? `<br><small>${data.details}</small>` : ''}
                    </p>
                `;
                analyzeBtn.style.display = "block";
            } else {
                const riskLevelClass = data.vulnerability_score > 70 ? 'high-risk' :
                                     data.vulnerability_score > 40 ? 'medium-risk' :
                                     'low-risk';
                
                const riskLevel = data.vulnerability_score > 70 ? '높음' :
                                data.vulnerability_score > 40 ? '중간' :
                                '낮음';
                                       
                resultContainer.innerHTML = `
                    <p class="success ${riskLevelClass}">
                        <strong>취약성 점수:</strong> ${data.vulnerability_score}%
                        <br>
                        <span class="risk-level">위험도: ${riskLevel}</span>
                    </p>
                    <p class="details">
                        <strong>분석 결과:</strong><br>
                        - 감지된 특징점: ${data.details.visible_landmarks_count}/${data.details.total_landmarks}<br>
                       
                        <br>
                        <strong>해석:</strong><br>
                        - 특징점이 많이 감지될수록 딥페이크 변조가 용이할 수 있습니다.<br>
                        - 주요 특징(눈, 코, 입 등)이 잘 보일수록 위험도가 높아집니다.
                        ${data.vulnerability_score > 70 ? 
                          '<br><br><strong class="warning">주의: 이 이미지는 딥페이크 취약성이 높습니다.</strong>' : ''}
                    </p>
                `;
            }

        } catch (error) {
            console.error("Error during analysis:", error);
            resultContainer.style.display = "block";
            resultContainer.innerHTML = `
                <p class="error">
                    <strong>서버 오류:</strong> 서버와 통신 중 문제가 발생했습니다.<br>
                    잠시 후 다시 시도해주세요.
                </p>`;
            loadingSpinner.style.display = "none";
            analyzeBtn.style.display = "block";
        }
    });
});
