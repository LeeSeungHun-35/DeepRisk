const express = require('express');
const multer = require('multer');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.static(path.join(__dirname, '../client')));

//uploads 폴더 자동 생성
const uploadDir = path.join(__dirname, 'uploads');
if (!fs.existsSync(uploadDir)) {
    fs.mkdirSync(uploadDir);
}

//Multer 설정
const storage = multer.diskStorage({
    destination: uploadDir,
    filename: (req, file, cb) => {
        cb(null, Date.now() + path.extname(file.originalname));
    }
});
const upload = multer({ storage });

//이미지 분석 API
app.post('/analyze', upload.single('image'), (req, res) => {
    if (!req.file) {
        return res.status(400).json({ error: '파일이 없습니다.' });
    }

    const imagePath = path.join(uploadDir, req.file.filename);
    // Python 스크립트의 절대 경로 사용
    const pythonScriptPath = path.join(__dirname, 'analysis.py');
    const pythonProcess = spawn('python', [pythonScriptPath, imagePath]);

    let dataBuffer = "";
    let errorBuffer = "";

    pythonProcess.stdout.on('data', (data) => {
        dataBuffer += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
        errorBuffer += data.toString();
        console.error('Python 오류:', data.toString());
    });

    pythonProcess.on('close', (code) => {
        // 항상 업로드된 이미지 삭제
        fs.unlink(imagePath, (err) => {
            if (err) console.error('파일 삭제 실패:', err);
        });

        if (code !== 0) {
            return res.status(500).json({ 
                error: '분석 실패', 
                details: errorBuffer 
            });
        }

        try {
            const trimmedData = dataBuffer.trim();
            if (!trimmedData) {
                return res.status(500).json({ error: '얼굴을 찾을 수 없습니다.' });
            }
            const result = JSON.parse(trimmedData);
            if (result.error) {
                return res.status(500).json(result);
            }
            res.json(result);
        } catch (err) {
            res.status(500).json({ 
                error: '결과 처리 실패',
                details: err.message 
            });
        }
    });
});

app.listen(3000, () => {
    console.log('✅ 서버 실행 중: http://localhost:3000');
});