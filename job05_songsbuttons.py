import sys
import os
from PyQt5 import QtWidgets, QtGui, QtCore

class MP3PlayerUI(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.current_song_index = -1  # 현재 재생 중인 노래 인덱스 (-1은 재생 중 아님)
        self.songs_list = []  # music 디렉토리의 mp3 파일 목록 (순서 기준)
        self.thumbnail_list = []  # thumbnail 디렉토리의 webp 파일 목록
        self.current_display_index = 0  # 썸네일 표시 시작 인덱스
        self.init_ui()
        self.load_files()

    def init_ui(self):
        # 창 설정
        self.setWindowTitle("MP3 Player")
        self.setFixedSize(800, 600)

        # 메인 레이아웃 (수직)
        self.main_layout = QtWidgets.QVBoxLayout()

        # 프로그레스바와 진행 상황 라벨 레이아웃 (수평)
        progress_layout = QtWidgets.QHBoxLayout()

        # 프로그레스바
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(20)

        # 진행 상황 라벨
        self.label_progress = QtWidgets.QLabel("00:00 / 00:00")
        self.label_progress.setAlignment(QtCore.Qt.AlignCenter)
        self.label_progress.setStyleSheet("font-size: 14px;")

        # 프로그레스바와 라벨을 레이아웃에 추가
        progress_layout.addWidget(self.progress_bar, stretch=3)
        progress_layout.addWidget(self.label_progress, stretch=1)

        # 썸네일 표시를 위한 위젯 (초기에는 숨김)
        self.thumbnail_widget = QtWidgets.QWidget()
        self.thumbnail_layout = QtWidgets.QHBoxLayout()
        self.thumbnail_widget.setLayout(self.thumbnail_layout)
        self.thumbnail_widget.hide()

        # 썸네일 이미지 라벨 (5개)
        self.thumbnail_labels = [QtWidgets.QLabel() for _ in range(5)]
        for label in self.thumbnail_labels:
            label.setFixedSize(100, 100)
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setStyleSheet("border: 1px solid gray;")
            self.thumbnail_layout.addWidget(label)

        # 좌우 방향키 버튼
        self.button_left = QtWidgets.QPushButton("<")
        self.button_left.setFixedSize(30, 30)
        self.button_left.clicked.connect(self.shift_thumbnails_left)
        self.button_right = QtWidgets.QPushButton(">")
        self.button_right.setFixedSize(30, 30)
        self.button_right.clicked.connect(self.shift_thumbnails_right)

        # 썸네일 레이아웃에 방향키 추가
        self.thumbnail_layout.insertWidget(0, self.button_left)
        self.thumbnail_layout.addWidget(self.button_right)

        # 버튼 레이아웃 (수평)
        button_layout = QtWidgets.QHBoxLayout()

        # 버튼 생성
        self.button_rewind = QtWidgets.QPushButton()
        self.button_rewind.setFixedSize(50, 50)
        self.button_rewind.setIcon(QtGui.QIcon("images/rewind.png"))
        self.button_rewind.setIconSize(QtCore.QSize(40, 40))

        self.button_play_pause = QtWidgets.QPushButton()
        self.button_play_pause.setFixedSize(50, 50)
        self.button_play_pause.setIcon(QtGui.QIcon("images/play.png"))
        self.button_play_pause.setIconSize(QtCore.QSize(40, 40))

        self.button_fastforward = QtWidgets.QPushButton()
        self.button_fastforward.setFixedSize(50, 50)
        self.button_fastforward.setIcon(QtGui.QIcon("images/fastforward.png"))
        self.button_fastforward.setIconSize(QtCore.QSize(40, 40))

        self.button_volume = QtWidgets.QPushButton()
        self.button_volume.setFixedSize(50, 50)
        self.button_volume.setIcon(QtGui.QIcon("images/volume.png"))
        self.button_volume.setIconSize(QtCore.QSize(40, 40))

        self.button_songs = QtWidgets.QPushButton()
        self.button_songs.setFixedSize(50, 50)
        self.button_songs.setIcon(QtGui.QIcon("images/songs.png"))
        self.button_songs.setIconSize(QtCore.QSize(40, 40))
        self.button_songs.clicked.connect(self.toggle_thumbnails)

        # 버튼을 레이아웃에 추가
        button_layout.addStretch()
        button_layout.addWidget(self.button_rewind)
        button_layout.addWidget(self.button_play_pause)
        button_layout.addWidget(self.button_fastforward)
        button_layout.addStretch()
        button_layout.addWidget(self.button_volume)
        button_layout.addWidget(self.button_songs)

        # 메인 레이아웃에 추가
        self.main_layout.addStretch()
        self.main_layout.addLayout(progress_layout)
        self.main_layout.addWidget(self.thumbnail_widget)
        self.main_layout.addLayout(button_layout)
        self.main_layout.addSpacing(10)

        # 메인 레이아웃 설정
        self.setLayout(self.main_layout)

    def load_files(self):
        # music 디렉토리에서 .mp3 파일 목록 가져오기
        if not os.path.isdir("music"):
            print("music 디렉토리가 없습니다.")
            return
        self.songs_list = [f for f in os.listdir("music") if f.lower().endswith(".mp3")]
        self.songs_list.sort()
        print(f"로드된 .mp3 파일: {self.songs_list}")

        # thumbnail 디렉토리에서 .webp 파일 목록 가져오기
        if not os.path.isdir("thumbnail"):
            print("thumbnail 디렉토리가 없습니다.")
            return
        self.thumbnail_list = [f for f in os.listdir("thumbnail") if f.lower().endswith(".webp")]
        self.thumbnail_list.sort()
        print(f"로드된 .webp 파일: {self.thumbnail_list}")

    def match_thumbnail(self, song_name):
        # .mp3 파일의 노래 제목으로 .webp 썸네일 파일 찾기
        print(f"매칭 시도: 노래 제목 '{song_name}'")
        for thumbnail in self.thumbnail_list:
            if song_name.lower() in thumbnail.lower():
                thumbnail_path = os.path.join("thumbnail", thumbnail)
                print(f"매칭 성공: '{song_name}' -> '{thumbnail_path}'")
                return thumbnail_path
        print(f"매칭 실패: '{song_name}'에 해당하는 썸네일 없음")
        return None

    def update_thumbnails(self):
        # 썸네일 업데이트
        if not self.songs_list:
            print("썸네일 업데이트 실패: songs_list가 비어 있음")
            return

        for label in self.thumbnail_labels:
            label.clear()  # 기존 이미지 지우기

        if self.current_song_index == -1:
            # 재생 중인 노래가 없으면 music 디렉토리 순서대로 표시
            start_index = self.current_display_index
            print(f"썸네일 표시 (재생 중 아님), 시작 인덱스: {start_index}")
            for i, label in enumerate(self.thumbnail_labels):
                song_index = start_index + i
                if song_index < len(self.songs_list):
                    song_name = self.songs_list[song_index].split("_")[1].replace(".mp3", "")
                    thumbnail_path = self.match_thumbnail(song_name)
                    if thumbnail_path and os.path.exists(thumbnail_path):
                        pixmap = QtGui.QPixmap(thumbnail_path)
                        if not pixmap.isNull():
                            pixmap = pixmap.scaled(100, 100, QtCore.Qt.KeepAspectRatio)
                            label.setPixmap(pixmap)
                            print(f"썸네일 로드 성공: {thumbnail_path}")
                        else:
                            print(f"썸네일 로드 실패: {thumbnail_path} (이미지 손상 또는 형식 오류)")
                    else:
                        print(f"썸네일 경로 없음: {song_name}")
                else:
                    print(f"인덱스 초과: {song_index}")
                    break
        else:
            # 재생 중인 노래를 중앙에 표시
            center_index = 2  # 5개 중 중앙은 3번째 (인덱스 2)
            print(f"썸네일 표시 (재생 중), 중앙 인덱스: {self.current_song_index}")
            song_name = self.songs_list[self.current_song_index].split("_")[1].replace(".mp3", "")
            thumbnail_path = self.match_thumbnail(song_name)
            if thumbnail_path and os.path.exists(thumbnail_path):
                pixmap = QtGui.QPixmap(thumbnail_path)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(100, 100, QtCore.Qt.KeepAspectRatio)
                    self.thumbnail_labels[center_index].setPixmap(pixmap)
                    print(f"중앙 썸네일 로드 성공: {thumbnail_path}")
                else:
                    print(f"중앙 썸네일 로드 실패: {thumbnail_path} (이미지 손상 또는 형식 오류)")

            # 좌측 두 개 (이전 노래)
            for i in range(center_index):
                song_index = self.current_song_index - (center_index - i)
                if song_index >= 0:
                    song_name = self.songs_list[song_index].split("_")[1].replace(".mp3", "")
                    thumbnail_path = self.match_thumbnail(song_name)
                    if thumbnail_path and os.path.exists(thumbnail_path):
                        pixmap = QtGui.QPixmap(thumbnail_path)
                        if not pixmap.isNull():
                            pixmap = pixmap.scaled(100, 100, QtCore.Qt.KeepAspectRatio)
                            self.thumbnail_labels[i].setPixmap(pixmap)
                            print(f"좌측 썸네일 로드 성공: {thumbnail_path}")
                        else:
                            print(f"좌측 썸네일 로드 실패: {thumbnail_path} (이미지 손상 또는 형식 오류)")
                    else:
                        print(f"좌측 썸네일 경로 없음: {song_name}")

            # 우측 두 개 (다음 노래)
            for i in range(center_index + 1, 5):
                song_index = self.current_song_index + (i - center_index)
                if song_index < len(self.songs_list):
                    song_name = self.songs_list[song_index].split("_")[1].replace(".mp3", "")
                    thumbnail_path = self.match_thumbnail(song_name)
                    if thumbnail_path and os.path.exists(thumbnail_path):
                        pixmap = QtGui.QPixmap(thumbnail_path)
                        if not pixmap.isNull():
                            pixmap = pixmap.scaled(100, 100, QtCore.Qt.KeepAspectRatio)
                            self.thumbnail_labels[i].setPixmap(pixmap)
                            print(f"우측 썸네일 로드 성공: {thumbnail_path}")
                        else:
                            print(f"우측 썸네일 로드 실패: {thumbnail_path} (이미지 손상 또는 형식 오류)")
                    else:
                        print(f"우측 썸네일 경로 없음: {song_name}")

    def shift_thumbnails_left(self):
        # 썸네일 왼쪽으로 이동
        if self.current_song_index == -1 and self.current_display_index > 0:
            self.current_display_index -= 1
            print(f"썸네일 왼쪽 이동, 새 시작 인덱스: {self.current_display_index}")
            self.update_thumbnails()

    def shift_thumbnails_right(self):
        # 썸네일 오른쪽으로 이동
        if self.current_song_index == -1 and self.current_display_index < len(self.songs_list) - 5:
            self.current_display_index += 1
            print(f"썸네일 오른쪽 이동, 새 시작 인덱스: {self.current_display_index}")
            self.update_thumbnails()

    def toggle_thumbnails(self):
        # 썸네일 위젯 표시/숨김 토글
        if self.thumbnail_widget.isHidden():
            self.thumbnail_widget.show()
            print("썸네일 위젯 표시")
            self.update_thumbnails()
        else:
            self.thumbnail_widget.hide()
            print("썸네일 위젯 숨김")

def main():
    # images 디렉토리 확인
    if not os.path.exists("images"):
        print("images 디렉토리가 없습니다. images 디렉토리에 play.png, pause.png, rewind.png, fastforward.png, songs.png를 준비하세요.")
        return
    
    app = QtWidgets.QApplication(sys.argv)
    window = MP3PlayerUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"오류 발생: {e}")