import yt_dlp
import os
import ffmpeg

playlist_url = "https://youtube.com/playlist?list=PLn_Pl3CGIaYGMJTra9H9p9clHJhSObMKD&si=zS13qlpRnURU8tGR"

output_path = "music"  # 저장할 폴더
audio_format = "mp3"   # 출력 형식
audio_quality = "0"    # 최고 품질

if not os.path.exists(output_path):
    os.makedirs(output_path)

# yt-dlp 설정
ydl_opts = {
    'format': 'bestaudio/best',  # 최상의 오디오 품질 선택
    'extractaudio': True,        # 오디오만 추출
    'audioformat': audio_format, # 출력 형식
    'outtmpl': f"{output_path}/%(title)s.%(ext)s",  # 출력 경로 및 파일명
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',  # FFmpeg로 오디오 추출
        'preferredcodec': audio_format,
        'preferredquality': audio_quality,
    }],

    'noplaylist': False,  # 플레이리스트 전체 처리
    'concurrent_fragments': 4,  # 병렬 다운로드
    'quiet': False,  # 진행 상황 출력
    'no_warnings': True,  # 경고 메시지 비활성화
}

# 다운로드 실행
try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([playlist_url])
    print("플레이리스트 음원 추출 완료!")
except Exception as e:
    print(f"에러 발생: {e}")
