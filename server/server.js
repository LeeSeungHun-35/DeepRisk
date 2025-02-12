const express = require('express');
const multer = require('multer');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');  //파일 읽기, 쓰기, 삭제 등 파일 처리 기능 모듈


//서버 생성, 설정
const app = express();
const upload = multer({ dest: 'uploads/' });
app.use(express.static('../client'));

//파일 업로드 및 Python 스크립트 실행
app.post('/analyze', upload.single('image'), (req, res) => {
    if (!req.file) {
        return res.status(400).json({ error: '파일이 없습니다.' });
    }

    const imagePath = path.join(__dirname, req.file.path);
    const pythonProcess = spawn('python', ['analysis.py', imagePath]);

//파이썬 스크립트 출력 처리하는 부분ㄴ
    let dataBuffer = "";

    pythonProcess.stdout.on('data', (data) => {
        dataBuffer += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error('Python 오류:', data.toString());
    });

    pythonProcess.on('close', (code) => {
        if (code !== 0) {
            console.error(`Python 프로세스 종료 코드: ${code}`);
            return res.status(500).json({ error: 'Python 스크립트 실행 실패' });
        }

        try {
            const result = JSON.parse(dataBuffer);
            res.json(result);
        } catch (err) {
            console.error('JSON 파싱 오류:', err);
            res.status(500).json({ error: '결과 데이터 처리 실패' });
        } finally {
            fs.unlink(imagePath, (err) => {
                if (err) console.error('파일 삭제 오류:', err);
            });
        }
    });
//파일 삭제, 오류 처리하는 부ㅜㅂ
    pythonProcess.on('error', (err) => {
        console.error('Python 프로세스 실행 오류:', err);
        res.status(500).json({ error: 'Python 실행 실패' });
    });
});

//서버 시작
app.listen(3000, () => {
    console.log('http://localhost:3000에서 서버 실행 중');
});