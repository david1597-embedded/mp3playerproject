import yt_dlp
import os

# 설정
playlist_url = "https://youtube.com/playlist?list=PLn_Pl3CGIaYGMJTra9H9p9clHJhSObMKD"
mv_path = "mv"          # 뮤직비디오 저장 폴더
thumbnail_path = "thumbnail"  # 썸네일 저장 폴더
video_format = "mp4"    # 영상 출력 형식

# 출력 폴더 생성
if not os.path.exists(mv_path):
    os.makedirs(mv_path)
if not os.path.exists(thumbnail_path):
    os.makedirs(thumbnail_path)

# yt-dlp 설정
ydl_opts = {
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',  # 최상의 MP4 영상과 오디오 조합
    'outtmpl': {
        'default': f"{mv_path}/%(title)s.%(ext)s",  # 뮤직비디오 저장 경로
        'thumbnail': f"{thumbnail_path}/%(title)s.%(ext)s"  # 썸네일 저장 경로
    },
    'writethumbnail': True,      # 썸네일 다운로드 활성화
    'postprocessors': [
        {
            'key': 'FFmpegVideoConvertor',  # 영상을 MP4로 변환
            'preferedformat': video_format,
        },
        {
            'key': 'FFmpegThumbnailsConvertor',  # 썸네일을 JPG로 변환
            'format': 'jpg',
        },
    ],
    'ffmpeg_location': 'D:/utils/ffmpeg-2025-06-04-git-a4c1a5b084-full_build/bin/ffmpeg.exe',  # FFmpeg 경로 (실제 경로로 변경)
    'ffprobe_location': 'D:/utils/ffmpeg-2025-06-04-git-a4c1a5b084-full_build/bin/ffprobe.exe',  # ffprobe 경로 (실제 경로로 변경)
    'noplaylist': False,  # 플레이리스트 전체 처리
    'concurrent_fragments': 4,  # 병렬 다운로드
    'verbose': True,  # 디버그 로그 활성화
    'ignoreerrors': True,  # 실패한 영상 건너뛰기
}

# 다운로드 실행
try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([playlist_url])
    print("플레이리스트 뮤직비디오 및 썸네일 다운로드 완료!")
except Exception as e:
    print(f"에러 발생: {e}")