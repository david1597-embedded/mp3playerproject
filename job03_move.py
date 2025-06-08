import os
import shutil

# 설정
mv_path = "mv"  # 원본 폴더 (webp, m4a 파일이 있는 곳)
thumbnail_path = "thumbnail"  # 대상 폴더 (webp 파일을 이동할 곳)

# thumbnail 폴더 생성
if not os.path.exists(thumbnail_path):
    os.makedirs(thumbnail_path)

# .webp 파일 이동 및 .m4a 파일 삭제
moved_count = 0
deleted_count = 0

for filename in os.listdir(mv_path):
    file_path = os.path.join(mv_path, filename)

    # .webp 파일 이동
    if filename.lower().endswith(".webp"):
        dst_file = os.path.join(thumbnail_path, filename)
        try:
            shutil.move(file_path, dst_file)
            print(f"이동 완료: {filename}")
            moved_count += 1
        except Exception as e:
            print(f"이동 실패: {filename} - {e}")

    # .m4a 파일 삭제
    elif filename.lower().endswith(".m4a"):
        try:
            os.remove(file_path)
            print(f"삭제 완료: {filename}")
            deleted_count += 1
        except Exception as e:
            print(f"삭제 실패: {filename} - {e}")

print(f"총 {moved_count}개의 .webp 파일을 이동하고, {deleted_count}개의 .m4a 파일을 삭제했습니다.")