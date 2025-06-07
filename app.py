from flask import Flask, render_template, request, send_from_directory, redirect, url_for
from werkzeug.utils import secure_filename
import os
import subprocess
import uuid

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'video' not in request.files:
        return 'No file part', 400
    file = request.files['video']
    if file.filename == '':
        return 'No selected file', 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # 출력 파일 경로 생성
    output_filename = os.path.splitext(filename)[0] + '.mp3'
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

    # ffmpeg로 mp3 변환
    subprocess.run(['ffmpeg', '-i', filepath, '-vn', '-acodec', 'libmp3lame', output_path])

    return redirect(url_for('download_file', filename=output_filename))

@app.route('/download_link', methods=['POST'])
def download_from_link():
    url = request.form.get('video_url')
    if not url:
        return 'No URL provided', 400

    unique_id = str(uuid.uuid4())[:8]
    output_filename = f"yt_audio_{unique_id}.mp3"
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

    # yt-dlp로 YouTube에서 오디오만 추출
    try:
        subprocess.run([
            'yt-dlp',
            '-x', '--audio-format', 'mp3',
            '-o', os.path.join(app.config['OUTPUT_FOLDER'], f"yt_audio_{unique_id}.%(ext)s"),
            url
        ], check=True)
    except subprocess.CalledProcessError:
        return "YouTube 링크에서 추출 실패", 500

    return redirect(url_for('download_file', filename=output_filename))

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
