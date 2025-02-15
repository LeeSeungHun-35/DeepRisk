const express = require('express');
const multer = require('multer');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.static(path.join(__dirname, '../client')));

// 📌 uploads 폴더 자동 생성
const uploadDir = path.join(__dirname, 'uploads');
if (!fs.existsSync(uploadDir)) {
    fs.mkdirSync(uploadDir);
}

// 📌 Multer 설정
const storage = multer.diskStorage({
    destination: uploadDir,
    filename: (req, file, cb) => {
        cb(null, Date.now() + path.extname(file.originalname));
    }
});
const upload = multer({ storage });

// 📌 이미지 분석 API
app.post('/analyze', upload.single('image'), (req, res) => {
    if (!req.file) {
        return res.status(400).json({ error: '파일이 없습니다.' });
    }

    const imagePath = path.join(uploadDir, req.file.filename);
    const pythonProcess = spawn('python', ['analysis.py', imagePath]);

    let dataBuffer = "";

    pythonProcess.stdout.on('data', (data) => {
        dataBuffer += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error('Python 오류:', data.toString());
    });

    pythonProcess.on('close', (code) => {
        if (code !== 0) {
            return res.status(500).json({ error: 'Python 실행 실패' });
        }
        try {
            if (!dataBuffer.trim()) {
                return res.status(500).json({ error: '얼굴을 찾을 수 없습니다.' });
            }
            const result = JSON.parse(dataBuffer);
            res.json(result);
        } catch (err) {
            res.status(500).json({ error: '결과 처리 실패' });
        } finally {
            fs.unlink(imagePath, () => {});
        }
    });
});

app.listen(3000, () => {
    console.log('✅ 서버 실행 중: http://localhost:3000');
});
