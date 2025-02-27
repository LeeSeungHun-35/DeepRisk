document.addEventListener("DOMContentLoaded", () => {
    const fileInput = document.getElementById("fileInput");
    const dropZone = document.getElementById("dropZone");
    const analyzeBtn = document.getElementById("analyzeBtn");
    const previewImage = document.getElementById("previewImage");
    const resultContainer = document.getElementById("resultContainer");
    const loadingSpinner = document.getElementById("loadingSpinner");

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

    function handleFilePreview(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImage.src = e.target.result;
            previewImage.style.display = "block";
            analyzeBtn.style.display = "block";
        };
        reader.readAsDataURL(file);
    }

    analyzeBtn.addEventListener("click", async () => {
        const file = fileInput.files[0];
        if (!file) {
            alert("이미지를 선택하세요.");
            return;
        }

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

            loadingSpinner.style.display = "none";
            resultContainer.style.display = "block";

            if (data.error) {
                resultContainer.innerHTML = `<p class="error"><strong>분석 실패:</strong> ${data.error}</p>`;
                analyzeBtn.style.display = "block";
            } else {
                const riskLevel = data.vulnerability_score > 70 ? '높음' :
                                  data.vulnerability_score > 40 ? '중간' : '낮음';

                resultContainer.innerHTML = `
                    <p class="success">
                        <strong>취약성 점수:</strong> ${data.vulnerability_score}%
                        <br>
                        <span class="risk-level">위험도: ${riskLevel}</span>
                    </p>
                    <p class="details">
                        - 감지된 피부 랜드마크: ${data.details.visible_landmarks_count}/${data.details.total_landmarks}<br>
                        ${data.vulnerability_score > 70 ? '<strong class="warning">주의: 취약성이 높습니다.</strong>' : ''}
                    </p>
                `;
            }
        } catch (error) {
            resultContainer.innerHTML = `<p class="error"><strong>서버 오류:</strong> 다시 시도해주세요.</p>`;
            loadingSpinner.style.display = "none";
            analyzeBtn.style.display = "block";
        }
    });
});
