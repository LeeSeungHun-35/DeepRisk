const express = require('express');
const multer = require('multer');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.static(path.join(__dirname, '../client')));

// uploads 폴더 자동 생성
const uploadDir = path.join(__dirname, 'uploads');
if (!fs.existsSync(uploadDir)) {
    fs.mkdirSync(uploadDir);
}

// Multer 설정
const storage = multer.diskStorage({
    destination: uploadDir,
    filename: (req, file, cb) => {
        const ext = path.extname(file.originalname);
        const timestamp = Date.now();
        cb(null, `image_${timestamp}${ext}`);
    }
});

const fileFilter = (req, file, cb) => {
    //이미지 형식 검사
    if (file.mimetype.startsWith('image/')) {
        cb(null, true);
    } else {
        cb(new Error('이미지 파일만 업로드 가능합니다.'), false);
    }
};

const upload = multer({ 
    storage,
    fileFilter,
    limits: {
        fileSize: 10 * 1024 * 1024  //10MB 제한
    }
});

  //이미지 분석 API
app.post('/analyze', upload.single('image'), (req, res) => {
    if (!req.file) {
        return res.status(400).json({ error: '파일이 없습니다.' });
    }

    const imagePath = path.join(uploadDir, req.file.filename);
    const pythonScriptPath = path.join(__dirname, 'analysis.py');

       //Python 실행 환경
    const pythonProcess = spawn('python', [pythonScriptPath, imagePath], {
        env: { ...process.env, PYTHONIOENCODING: 'utf-8' }
    });

    let dataBuffer = "";
    let errorBuffer = "";

    pythonProcess.stdout.on('data', (data) => {
        dataBuffer += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
        errorBuffer += data.toString();
        console.error('Python 오류:', data.toString());
    });

    //타임아웃 설정
    const timeout = setTimeout(() => {
        pythonProcess.kill();
        cleanupAndRespond('분석 시간이 초과되었습니다.');
    }, 30000); //30초 타임아웃

    function cleanupAndRespond(error) {
        clearTimeout(timeout);
        fs.unlink(imagePath, (err) => {
            if (err) console.error('파일 삭제 실패:', err);
        });

        if (error) {
            return res.status(500).json({ 
                error: error,
                details: errorBuffer || '자세한 오류 정보가 없습니다.'
            });
        }
    }

    pythonProcess.on('close', (code) => {
        clearTimeout(timeout);
        
        fs.unlink(imagePath, (err) => {
            if (err) console.error('파일 삭제 실패:', err);
        });

        if (code !== 0) {
            return res.status(500).json({ 
                error: '이미지 분석에 실패했습니다', 
                details: errorBuffer || '알 수 없는 오류가 발생했습니다.'
            });
        }

        try {
            const trimmedData = dataBuffer.trim();
            if (!trimmedData) {
                return res.status(500).json({ 
                    error: '분석 결과가 없습니다.',
                    details: '이미지에서 얼굴을 찾을 수 없습니다.'
                });
            }
            const result = JSON.parse(trimmedData);
            if (result.error) {
                return res.status(500).json({
                    error: result.error,
                    details: result.details || '자세한 오류 정보가 없습니다.'
                });
            }
            res.json(result);
        } catch (err) {
            res.status(500).json({ 
                error: '결과 처리에 실패했습니다.',
                details: err.message 
            });
        }
    });
});

app.use((err, req, res, next) => {
    console.error('서버 에러:', err);
    if (err instanceof multer.MulterError) {
        if (err.code === 'LIMIT_FILE_SIZE') {
            return res.status(400).json({ error: '파일 크기는 10MB 이하여야 합니다.' });
        }
        return res.status(400).json({ error: '파일 업로드 중 오류 발생했습니다.' });
    }
    res.status(500).json({ error: err.message });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`✅ 서버 실행 중: http://localhost:${PORT}`);
});
