document.addEventListener("DOMContentLoaded", () => {
    const fileInput = document.getElementById("fileInput");
    const dropZone = document.getElementById("dropZone");
    const analyzeBtn = document.getElementById("analyzeBtn");
    const previewImage = document.getElementById("previewImage");
    const resultContainer = document.getElementById("resultContainer");
    const loadingSpinner = document.getElementById("loadingSpinner");

      //드래그 앤 드롭 처리
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

    //파일 선택 클릭 
    dropZone.addEventListener("click", () => {
        fileInput.click();
    });

//파일 입력 변경 
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
            console.log("Received data from server:", data);  //데이터 로깅

            loadingSpinner.style.display = "none";
            resultContainer.style.display = "block";

            if (data.error) {
                resultContainer.innerHTML = `<p class="error">${data.error}</p>`;
            } else {
                const riskLevelClass = data.vulnerability_score > 70 ? 'high-risk' : 
                                     data.vulnerability_score > 40 ? 'medium-risk' : 
                                     'low-risk';
                                     
                resultContainer.innerHTML = `
                    <p class="success ${riskLevelClass}">
                        취약성 점수: ${data.vulnerability_score}%
                    </p>
                    <p class="description">
                        위 취약성 점수가 높을수록 딥페이크 변조되었을떄 자연스러워집니다.<br>
                        - 얼굴 정면도: ${Math.round(data.details.face_alignment * 100)}%<br>
                        - 피부 텍스처: ${Math.round(data.details.skin_texture * 100)}%<br>
                        - 얼굴 대칭성: ${Math.round(data.details.facial_symmetry * 100)}%<br>
                        - 특징 명확도: ${Math.round(data.details.feature_distinctiveness * 100)}%<br>
                        - 이미지 품질: ${Math.round(data.details.image_quality * 100)}%
                    </p>
                `;
            }
            
        } catch (error) {
            console.error("Error during analysis:", error);  //에러 로깅
            resultContainer.style.display = "block";
            resultContainer.innerHTML = `<p class="error">서버 오류 발생! 다시 시도하세요.</p>`;
            loadingSpinner.style.display = "none";
            analyzeBtn.style.display = "block";
        }
    });
});