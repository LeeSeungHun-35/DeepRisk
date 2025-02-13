const express = require('express');
const multer = require('multer');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.static(path.join(__dirname, '../client')));

const storage = multer.diskStorage({
    destination: 'uploads/',
    filename: (req, file, cb) => {
        cb(null, Date.now() + path.extname(file.originalname));
    }
});
const upload = multer({ storage });

app.post('/analyze', upload.single('image'), (req, res) => {
    if (!req.file) {
        return res.status(400).json({ error: '파일이 없습니다.' });
    }

    const imagePath = path.join(__dirname, req.file.path);
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
