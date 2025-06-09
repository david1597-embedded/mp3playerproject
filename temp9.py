import sys
import os
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QGraphicsOpacityEffect, QLabel, QTextEdit, QGraphicsBlurEffect
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import QTimer, QPoint, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from mutagen.mp3 import MP3

class ThumbnailLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.top_widget = None
        self.is_hovered = False

    def set_info_text(self, artist, song):
        self.setProperty("artist", artist)
        self.setProperty("song", song)

    def enterEvent(self, event):
        self.is_hovered = True
        artist = self.property("artist")
        song = self.property("song")
        if artist and song:
            self.parent().show_info_label(artist, song, self)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovered = False
        super().leaveEvent(event)

    def check_hover_state(self):
        if not self.is_hovered:
            self.parent().hide_info_label()

    def mouseDoubleClickEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            idx = self.property("index")
            self.parent().parent().thumbnail_clicked(idx)

class ThumbnailWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dragging = False
        self.last_pos = None
        self.velocity = 0.0
        self.timer = QTimer()
        self.timer.timeout.connect(self.apply_inertia)
        self.offset = 0
        self.target_offset = 0
        self.setStyleSheet("background-color: transparent;")
        self.setFixedSize(600, 200)
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)

        self.smooth_timer = QTimer()
        self.smooth_timer.timeout.connect(self.smooth_animation_step)
        self.animation_speed = 0.15

        self.info_label = QLabel(self)
        self.info_label.setFixedSize(250, 60)
        self.info_label.setStyleSheet("""
            background-color: rgba(0, 0, 0, 0.85);
            color: white;
            font-size: 12px;
            padding: 8px;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        """)
        self.info_label.hide()
        self.info_label.setWordWrap(True)
        self.info_label.setAlignment(QtCore.Qt.AlignCenter)
        self.current_hovered_label = None

        self.info_opacity_effect = QGraphicsOpacityEffect()
        self.info_label.setGraphicsEffect(self.info_opacity_effect)

        self.fade_animation = QPropertyAnimation(self.info_opacity_effect, b"opacity")
        self.fade_animation.setDuration(200)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)

    def show_info_label(self, artist, song, label):
        self.current_hovered_label = label
        self.info_label.setText(f"""
            <div style='text-align: center;'>
                <p style='font-size: 14px; font-weight: bold; color: #FFD700; margin: 2px;'>{artist}</p>
                <p style='font-size: 12px; color: #FFFFFF; margin: 2px;'>{song}</p>
            </div>
        """)
        label_center_x = label.x() + label.width() // 2
        info_x = max(10, min(label_center_x - 125, self.width() - 260))
        info_y = 145
        self.info_label.move(info_x, info_y)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.info_label.show()
        self.fade_animation.start()

    def hide_info_label(self):
        if self.info_label.isVisible():
            self.fade_animation.setStartValue(1.0)
            self.fade_animation.setEndValue(0.0)
            self.fade_animation.finished.connect(self.info_label.hide)
            self.fade_animation.start()
        self.current_hovered_label = None

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and self.parent().songs_list:
            self.dragging = True
            self.last_pos = event.pos().x()
            self.velocity = 0.0
            self.timer.stop()
            self.smooth_timer.stop()

    def mouseMoveEvent(self, event):
        if not self.dragging or not self.parent().songs_list:
            return
        try:
            current_pos = event.pos().x()
            delta = current_pos - self.last_pos
            self.offset += delta
            self.last_pos = current_pos
            self.velocity = delta / 0.05

            while self.offset >= 130:
                self.offset -= 130
                self.parent().current_display_index = (self.parent().current_display_index - 1) % len(
                    self.parent().songs_list)
                self.parent().update_thumbnails()
            while self.offset <= -130:
                self.offset += 130
                self.parent().current_display_index = (self.parent().current_display_index + 1) % len(
                    self.parent().songs_list)
                self.parent().update_thumbnails()

            self.parent().update_thumbnails_with_offset(self.offset)
        except Exception as e:
            print(f"mouseMoveEvent 오류: {e}")

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.dragging = False
            try:
                if abs(self.velocity) > 15:
                    self.timer.start(30)
                else:
                    self.snap_to_grid()
            except Exception as e:
                print(f"mouseReleaseEvent 오류: {e}")

    def apply_inertia(self):
        if not self.parent().songs_list:
            self.timer.stop()
            return
        try:
            if abs(self.velocity) < 3:
                self.timer.stop()
                self.snap_to_grid()
                return

            self.offset += self.velocity * 0.03
            self.velocity *= 0.92

            while self.offset >= 130:
                self.offset -= 130
                self.parent().current_display_index = (self.parent().current_display_index - 1) % len(
                    self.parent().songs_list)
                self.parent().update_thumbnails()
            while self.offset <= -130:
                self.offset += 130
                self.parent().current_display_index = (self.parent().current_display_index + 1) % len(
                    self.parent().songs_list)
                self.parent().update_thumbnails()

            self.parent().update_thumbnails_with_offset(self.offset)
        except Exception as e:
            print(f"apply_inertia 오류: {e}")

    def snap_to_grid(self):
        try:
            steps = round(self.offset / 130)
            self.target_offset = 0
            if steps != 0:
                self.parent().current_display_index = (self.parent().current_display_index - steps) % len(
                    self.parent().songs_list)
            if abs(self.offset) > 5:
                self.smooth_timer.start(16)
            else:
                self.offset = 0
                self.parent().update_thumbnails()
        except Exception as e:
            print(f"snap_to_grid 오류: {e}")

    def smooth_animation_step(self):
        try:
            if abs(self.offset - self.target_offset) < 1:
                self.smooth_timer.stop()
                self.offset = self.target_offset
                self.parent().update_thumbnails()
                return
            diff = self.target_offset - self.offset
            self.offset += diff * self.animation_speed
            self.parent().update_thumbnails_with_offset(self.offset)
        except Exception as e:
            print(f"smooth_animation_step 오류: {e}")

class CurtainWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 0.8);")
        self.setGeometry(0, -600, 800, 600)
        self.dragging = False
        self.start_y = 0
        self.setMouseTracking(True)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.dragging = True
            self.start_y = event.pos().y()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging:
            delta_y = event.pos().y() - self.start_y
            new_y = self.y() + delta_y
            new_y = max(-600, min(0, new_y))
            self.setGeometry(0, new_y, 800, 600)
            self.start_y = event.pos().y()
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.dragging = False
            target_y = -600 if self.y() < -300 else 0
            self.animate_curtain(target_y)
            event.accept()

    def animate_curtain(self, target_y):
        animation = QPropertyAnimation(self, b"geometry")
        animation.setDuration(500)
        animation.setStartValue(self.geometry())
        animation.setEndValue(QRect(0, target_y, 800, 600))
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        animation.start()

class MP3PlayerUI(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.current_song_index = -1
        self.songs_list = []
        self.thumbnail_list = []
        self.music_video_list = []
        self.current_display_index = 0
        self.thumbnail_positions = [0, 130, 260, 390, 520]
        self.top_widget = None
        self.background_label = None
        self.video_widget = None
        self.curtain_widget = None
        self.return_button = None
        self.is_playing = False
        self.is_muted = False
        self.current_mode = "lyrics"  # 초기 모드: 가사
        self.audio_player = QMediaPlayer()
        self.audio_player.setNotifyInterval(100)
        self.audio_player.positionChanged.connect(self.update_progress)
        self.audio_player.stateChanged.connect(self.handle_audio_state)
        self.audio_player.mediaStatusChanged.connect(self.handle_audio_status)
        self.video_player = QMediaPlayer()
        self.video_player.positionChanged.connect(self.sync_video_audio)
        self.song_durations = {}
        self.position_timer = QTimer(self)
        self.position_timer.timeout.connect(self.manual_position_update)
        self.init_ui()
        self.load_files()

    def init_ui(self):
        self.setWindowTitle("MP3 and Video Player")
        self.setFixedSize(800, 600)
        self.main_layout = QtWidgets.QVBoxLayout()
        self.thumbnail_visible = False
        self.original_spacing = None

        # 비디오 위젯 초기화
        self.video_widget = QVideoWidget(self)
        self.video_widget.setGeometry(0, 0, 800, 600)
        self.video_widget.lower()
        self.video_widget.hide()
        self.video_player.setVideoOutput(self.video_widget)

        # 커튼 위젯 초기화
        self.curtain_widget = CurtainWidget(self)
        self.curtain_widget.raise_()

        # 상단 버튼 레이아웃
        button_layout_top = QtWidgets.QHBoxLayout()
        self.button_lyrics = QtWidgets.QPushButton("가사")
        self.button_lyrics.setFixedSize(100, 40)
        self.button_lyrics.setStyleSheet("""
            QPushButton {
                background-color: #FFD700;
                color: #333;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
                border: 1px solid #DAA520;
            }
            QPushButton:hover {
                background-color: #FFEC8B;
            }
            QPushButton:pressed {
                background-color: #DAA520;
            }
        """)
        self.button_video = QtWidgets.QPushButton("뮤직비디오")
        self.button_video.setFixedSize(100, 40)
        self.button_video.setStyleSheet("""
            QPushButton {
                background-color: #87CEEB;
                color: #333;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
                border: 1px solid #4682B4;
            }
            QPushButton:hover {
                background-color: #B0E2FF;
            }
            QPushButton:pressed {
                background-color: #4682B4;
            }
        """)
        button_layout_top.addStretch()
        button_layout_top.addWidget(self.button_lyrics)
        button_layout_top.addWidget(self.button_video)
        button_layout_top.addStretch()

        self.button_lyrics.clicked.connect(self.show_lyrics_mode)
        self.button_video.clicked.connect(self.show_video_mode)

        # 썸네일 위젯
        self.thumbnail_widget = ThumbnailWidget(self)
        self.thumbnail_layout = QtWidgets.QHBoxLayout()
        self.thumbnail_widget.setLayout(self.thumbnail_layout)
        self.thumbnail_widget.hide()

        self.thumbnail_labels = [ThumbnailLabel(self.thumbnail_widget) for _ in range(5)]
        for i, label in enumerate(self.thumbnail_labels):
            label.setFixedSize(120, 120)
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setStyleSheet("""
                border: 2px solid #ddd;
                background-color: white;
                border-radius: 8px;
            """)
            label.move(self.thumbnail_positions[i], 15)
            label.setProperty("index", i)

        # 프로그레스바 레이아웃
        progress_layout = QtWidgets.QHBoxLayout()
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(20)
        self.progress_bar.mousePressEvent = self.seek_position
        self.label_progress = QtWidgets.QLabel("00:00 / 00:00")
        self.label_progress.setAlignment(QtCore.Qt.AlignCenter)
        self.label_progress.setStyleSheet("font-size: 14px;")
        progress_layout.addWidget(self.progress_bar, stretch=3)
        progress_layout.addWidget(self.label_progress, stretch=1)

        # 하단 버튼 레이아웃
        button_layout_bottom = QtWidgets.QHBoxLayout()
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
        button_layout_bottom.addStretch()
        button_layout_bottom.addWidget(self.button_rewind)
        button_layout_bottom.addWidget(self.button_play_pause)
        button_layout_bottom.addWidget(self.button_fastforward)
        button_layout_bottom.addStretch()
        button_layout_bottom.addWidget(self.button_volume)
        button_layout_bottom.addWidget(self.button_songs)

        # 메인 레이아웃 구성
        self.main_layout.addLayout(button_layout_top)
        self.main_layout.addStretch(1)
        self.main_layout.addWidget(self.thumbnail_widget, alignment=QtCore.Qt.AlignCenter)
        self.main_layout.addStretch(1)
        self.main_layout.addLayout(progress_layout)
        self.main_layout.addLayout(button_layout_bottom)
        self.setLayout(self.main_layout)

        QTimer.singleShot(100, self.show_initial_song)

        self.button_rewind.clicked.connect(self.rewind_10_seconds)
        self.button_play_pause.clicked.connect(self.toggle_play_pause)
        self.button_fastforward.clicked.connect(self.forward_10_seconds)
        self.button_volume.clicked.connect(self.toggle_volume)

    def get_song_duration(self, song_path):
        try:
            audio = MP3(song_path)
            duration_ms = int(audio.info.length * 1000)
            return duration_ms
        except Exception as e:
            print(f"mutagen 길이 가져오기 오류: {e}")
            return 0

    def show_initial_song(self):
        if self.songs_list:
            self.current_song_index = 0
            self.thumbnail_clicked(2)
            self.curtain_widget.animate_curtain(0)

    def rewind_10_seconds(self):
        if not self.songs_list:
            return
        try:
            current_pos = self.audio_player.position()
            song_path = os.path.join("music", self.songs_list[self.current_song_index])
            duration = self.song_durations.get(song_path, 0)
            new_pos = current_pos - 10000
            print(f"Rewind: 현재={self.format_time(current_pos)}, 목표={self.format_time(new_pos)}, 길이={self.format_time(duration)}")
            if new_pos <= 0:
                self.previous_song()
            else:
                self.audio_player.setPosition(new_pos)
                self.video_player.setPosition(new_pos)
        except Exception as e:
            print(f"rewind_10_seconds 오류: {e}")

    def forward_10_seconds(self):
        if not self.songs_list:
            return
        try:
            current_pos = self.audio_player.position()
            song_path = os.path.join("music", self.songs_list[self.current_song_index])
            duration = self.song_durations.get(song_path, 0)
            new_pos = current_pos + 10000
            print(f"Fast Forward: 현재={self.format_time(current_pos)}, 목표={self.format_time(new_pos)}, 길이={self.format_time(duration)}")
            if new_pos >= duration and duration > 0:
                self.next_song()
            else:
                self.audio_player.setPosition(new_pos)
                self.video_player.setPosition(new_pos)
        except Exception as e:
            print(f"forward_10_seconds 오류: {e}")

    def previous_song(self):
        if self.songs_list:
            self.audio_player.pause()
            self.video_player.pause()
            self.position_timer.stop()
            self.current_song_index = (self.current_song_index - 1) % len(self.songs_list)
            self.current_display_index = (self.current_song_index - 2) % len(self.songs_list)
            self.thumbnail_clicked(2)

    def next_song(self):
        if self.songs_list:
            self.audio_player.pause()
            self.video_player.pause()
            self.position_timer.stop()
            self.current_song_index = (self.current_song_index + 1) % len(self.songs_list)
            self.current_display_index = (self.current_song_index - 2) % len(self.songs_list)
            self.thumbnail_clicked(2)

    def toggle_play_pause(self):
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.audio_player.play()
            if self.current_mode == "video":
                self.video_player.setPosition(self.audio_player.position())
                self.video_player.play()
            self.button_play_pause.setIcon(QtGui.QIcon("images/pause.png"))
            self.position_timer.start(100)
            print("재생 시작")
        else:
            self.audio_player.pause()
            self.video_player.pause()
            self.button_play_pause.setIcon(QtGui.QIcon("images/play.png"))
            self.position_timer.stop()
            print("재생 일시정지")

    def toggle_volume(self):
        self.is_muted = not self.is_muted
        self.audio_player.setMuted(self.is_muted)
        self.video_player.setMuted(True)  # 비디오 오디오는 항상 음소거
        if self.is_muted:
            self.button_volume.setIcon(QtGui.QIcon("images/mute.png"))
            print("음소거")
        else:
            self.button_volume.setIcon(QtGui.QIcon("images/volume.png"))
            print("음소거 해제")

    def seek_position(self, event):
        try:
            if event.button() == QtCore.Qt.LeftButton:
                song_path = os.path.join("music", self.songs_list[self.current_song_index])
                duration = self.song_durations.get(song_path, 0)
                if duration > 0:
                    width = self.progress_bar.width()
                    click_x = event.pos().x()
                    seek_percentage = click_x / width
                    seek_time = int(seek_percentage * duration)
                    self.audio_player.setPosition(seek_time)
                    self.video_player.setPosition(seek_time)
                    print(f"탐색 위치: {self.format_time(seek_time)}")
        except Exception as e:
            print(f"seek_position 오류: {e}")

    def update_progress(self, position):
        try:
            song_path = os.path.join("music", self.songs_list[self.current_song_index])
            duration = self.song_durations.get(song_path, 0)
            print(f"update_progress 호출: position={self.format_time(position)}, duration={self.format_time(duration)}")
            if duration > 0:
                progress = (position / duration) * 100
                self.progress_bar.setValue(int(progress))
                self.label_progress.setText(
                    f"{self.format_time(position)} / {self.format_time(duration)}"
                )
                if position >= duration - 1000 and self.is_playing:
                    print("노래 종료, 다음 곡으로 전환")
                    self.next_song()
            else:
                self.progress_bar.setValue(0)
                self.label_progress.setText("00:00 / 00:00")
        except Exception as e:
            print(f"update_progress 오류: {e}")

    def manual_position_update(self):
        try:
            if self.is_playing and self.current_song_index >= 0:
                position = self.audio_player.position()
                self.update_progress(position)
        except Exception as e:
            print(f"manual_position_update 오류: {e}")

    def handle_audio_status(self, status):
        try:
            if status == QMediaPlayer.LoadedMedia:
                song_path = os.path.join("music", self.songs_list[self.current_song_index])
                duration = self.song_durations.get(song_path, 0)
                if duration > 0:
                    self.label_progress.setText(
                        f"00:00 / {self.format_time(duration)}"
                    )
                    print(f"오디오 미디어 로드 완료, mutagen 길이: {self.format_time(duration)}")
                else:
                    self.label_progress.setText("00:00 / 00:00")
                    print("오디오 미디어 로드 완료, 유효한 길이 없음")
                if self.is_playing:
                    self.audio_player.play()
                    if self.current_mode == "video":
                        self.video_player.setPosition(self.audio_player.position())
                        self.video_player.play()
        except Exception as e:
            print(f"handle_audio_status 오류: {e}")

    def handle_audio_state(self, state):
        try:
            if state == QMediaPlayer.StoppedState and self.is_playing:
                song_path = os.path.join("music", self.songs_list[self.current_song_index])
                duration = self.song_durations.get(song_path, 0)
                if self.audio_player.position() >= duration - 1000:
                    print("오디오 플레이어 정지, 다음 곡으로 전환")
                    self.next_song()
        except Exception as e:
            print(f"handle_audio_state 오류: {e}")

    def sync_video_audio(self, position):
        try:
            audio_pos = self.audio_player.position()
            if abs(position - audio_pos) > 500:
                self.video_player.setPosition(audio_pos)
                print(f"비디오 동기화: 오디오={self.format_time(audio_pos)}, 비디오={self.format_time(position)}")
        except Exception as e:
            print(f"sync_video_audio 오류: {e}")

    def load_files(self):
        try:
            if not os.path.isdir("music"):
                print("music 디렉토리가 없습니다.")
                return
            self.songs_list = [f for f in os.listdir("music") if f.lower().endswith(".mp3")]
            self.songs_list.sort()
            print(f"로드된 .mp3 파일: {self.songs_list}")

            for song in self.songs_list:
                song_path = os.path.join("music", song)
                duration = self.get_song_duration(song_path)
                self.song_durations[song_path] = duration
                print(f"{song} 길이: {self.format_time(duration)}")

            if not os.path.isdir("thumbnail"):
                print("thumbnail 디렉토리가 없습니다.")
            else:
                self.thumbnail_list = [f for f in os.listdir("thumbnail") if f.lower().endswith(".webp")]
                self.thumbnail_list.sort()
                print(f"로드된 .webp 파일: {self.thumbnail_list}")

            if not os.path.isdir("mv"):
                print("mv 디렉토리가 없습니다.")
            else:
                self.music_video_list = [f for f in os.listdir("mv") if f.lower().endswith(".mp4")]
                self.music_video_list.sort()
                print(f"로드된 .mp4 파일: {self.music_video_list}")

            if self.songs_list:
                self.update_thumbnails()
        except Exception as e:
            print(f"load_files 오류: {e}")

    def match_thumbnail(self, song_name):
        try:
            song_name = song_name.lower().replace(".mp3", "")
            for thumbnail in self.thumbnail_list:
                if song_name in thumbnail.lower():
                    thumbnail_path = os.path.join("thumbnail", thumbnail)
                    return thumbnail_path
            return None
        except Exception as e:
            print(f"match_thumbnail 오류: {e}")
            return None

    def match_music_video(self, song_name):
        try:
            song_name = song_name.lower().replace(".mp3", "").strip()
            print(f"뮤직비디오 매칭 시도: song_name='{song_name}'")
            for mv in self.music_video_list:
                mv_lower = mv.lower().replace(".mp4", "").strip()
                print(f"  - 비교 대상: mv='{mv_lower}'")
                if song_name in mv_lower or mv_lower in song_name:
                    mv_path = os.path.join("mv", mv)
                    print(f"뮤직비디오 찾음: {mv_path}")
                    return mv_path
            print(f"뮤직비디오 매칭 실패: {song_name}")
            return None
        except Exception as e:
            print(f"match_music_video 오류: {e}")
            return None

    def parse_song_info(self, filename):
        try:
            name_without_ext = filename.replace(".mp3", "")
            parts = name_without_ext.split("_", 1)
            if len(parts) >= 2:
                artist = parts[0].strip()
                song_name = parts[1].strip()
            else:
                artist = "Unknown Artist"
                song_name = parts[0].strip()
            return artist, song_name
        except Exception as e:
            print(f"parse_song_info 오류: {e}")
            return "Unknown Artist", filename.replace(".mp3", "")

    def update_thumbnails(self):
        if not self.songs_list:
            return
        try:
            print(f"update_thumbnails 호출: current_display_index={self.current_display_index}")
            for i, label in enumerate(self.thumbnail_labels):
                song_index = (self.current_display_index + i) % len(self.songs_list)
                artist, song_name = self.parse_song_info(self.songs_list[song_index])
                thumbnail_path = self.match_thumbnail(song_name)

                label.setProperty("song_index", song_index)
                label.set_info_text(artist, song_name)

                if thumbnail_path and os.path.exists(thumbnail_path):
                    pixmap = QtGui.QPixmap(thumbnail_path)
                    if not pixmap.isNull():
                        pixmap = pixmap.scaled(116, 116, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                        label.setPixmap(pixmap)
                    else:
                        label.clear()
                        label.setText("No Image")
                        label.setStyleSheet(label.styleSheet() + "color: #999;")
                else:
                    label.clear()
                    label.setText("No Image")
                    label.setStyleSheet(label.styleSheet() + "color: #999;")

                print(f"라벨 {i}: song_index={song_index}, song={self.songs_list[song_index]}")
        except Exception as e:
            print(f"update_thumbnails 오류: {e}")

    def update_thumbnails_with_offset(self, offset):
        try:
            center_position = 260
            for i, label in enumerate(self.thumbnail_labels):
                current_x = self.thumbnail_positions[i] + offset
                label.move(current_x, 15)
                distance_from_center = abs(current_x + 60 - center_position)
                if distance_from_center < 65:
                    opacity = 1.0
                    scale_factor = 1.1
                    border_color = "#FFD700"
                    border_width = 3
                elif distance_from_center < 130:
                    opacity = 0.8
                    scale_factor = 0.95
                    border_color = "#87CEEB"
                    border_width = 2
                else:
                    opacity = max(0.4, 1.0 - (distance_from_center / 300))
                    scale_factor = 0.8
                    border_color = "#ddd"
                    border_width = 1
                if (i == 0 and offset > 0) or (i == 4 and offset < 0):
                    opacity = max(0.2, 1.0 - abs(offset) / 130)
                opacity_effect = QGraphicsOpacityEffect()
                label.setGraphicsEffect(opacity_effect)
                opacity_effect.setOpacity(opacity)
                size = int(120 * scale_factor)
                label.setFixedSize(size, size)
                label.setStyleSheet(f"""
                    border: {border_width}px solid {border_color};
                    background-color: white;
                    border-radius: 8px;
                """)
        except Exception as e:
            print(f"update_thumbnails_with_offset 오류: {e}")

    def create_blurred_background(self, pixmap):
        try:
            scaled_pixmap = pixmap.scaled(800, 600, QtCore.Qt.KeepAspectRatioByExpanding,
                                          QtCore.Qt.SmoothTransformation)
            temp_label = QLabel()
            temp_label.setPixmap(scaled_pixmap)
            temp_label.setFixedSize(800, 600)
            blur_effect = QGraphicsBlurEffect()
            blur_effect.setBlurRadius(15)
            temp_label.setGraphicsEffect(blur_effect)
            blurred_pixmap = temp_label.grab()
            overlay = QtGui.QPixmap(800, 600)
            overlay.fill(QtGui.QColor(0, 0, 0, 100))
            painter = QtGui.QPainter(blurred_pixmap)
            painter.drawPixmap(0, 0, overlay)
            painter.end()
            return blurred_pixmap
        except Exception as e:
            print(f"create_blurred_background 오류: {e}")
            fallback = QtGui.QPixmap(800, 600)
            fallback.fill(QtGui.QColor(240, 240, 240))
            return fallback

    def create_top_widget(self, song_index):
        try:
            print(f"create_top_widget 호출: song_index={song_index}")
            artist, song_name = self.parse_song_info(self.songs_list[song_index])
            thumbnail_path = self.match_thumbnail(song_name)

            # 기존 top_widget 제거
            if self.top_widget:
                print("기존 top_widget 제거")
                self.main_layout.removeWidget(self.top_widget)
                self.top_widget.deleteLater()
                self.top_widget = None

            self.top_widget = QtWidgets.QWidget(self)  # 부모 위젯 명시
            self.top_widget.setFixedSize(600, 320)
            self.top_widget.setStyleSheet("""
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255, 255, 255, 0.15),
                    stop:1 rgba(255, 255, 255, 0.05));
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 10px;
            """)
            main_layout = QtWidgets.QHBoxLayout()
            main_layout.setContentsMargins(10, 10, 10, 10)
            main_layout.setSpacing(10)

            # 썸네일 컨테이너 (왼쪽)
            thumbnail_container = QtWidgets.QWidget()
            thumbnail_container.setFixedSize(220, 220)
            thumbnail_container.setStyleSheet("""
                background-color: rgba(0, 0, 0, 0.1);
                border-radius: 10px;
                border: 2px solid rgba(255, 255, 255, 0.3);
            """)
            thumbnail_label = QLabel(thumbnail_container)
            thumbnail_label.setFixedSize(216, 216)
            thumbnail_label.move(2, 2)
            thumbnail_label.setAlignment(QtCore.Qt.AlignCenter)
            thumbnail_label.setStyleSheet("border: none; background-color: transparent; border-radius: 8px;")
            if thumbnail_path and os.path.exists(thumbnail_path):
                pixmap = QtGui.QPixmap(thumbnail_path)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(216, 216, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                    rounded_pixmap = QtGui.QPixmap(216, 216)
                    rounded_pixmap.fill(QtCore.Qt.transparent)
                    painter = QtGui.QPainter(rounded_pixmap)
                    painter.setRenderHint(QtGui.QPainter.Antialiasing)
                    painter.setBrush(QtGui.QBrush(pixmap))
                    painter.setPen(QtCore.Qt.NoPen)
                    painter.drawRoundedRect(0, 0, 216, 216, 8, 8)
                    painter.end()
                    thumbnail_label.setPixmap(rounded_pixmap)
                else:
                    print(f"썸네일 이미지 로드 실패: {thumbnail_path}")
            else:
                print(f"썸네일 경로 없음: {song_name}")

            # 정보 컨테이너 (오른쪽)
            info_container = QtWidgets.QWidget()
            info_layout = QtWidgets.QVBoxLayout(info_container)
            info_layout.setContentsMargins(0, 0, 0, 0)
            info_layout.setSpacing(5)

            artist_label = QLabel(artist)
            artist_label.setStyleSheet("""
                font-size: 18px;
                font-weight: 700;
                color: #FFFFFF;
                text-shadow: 0px 0px 10px rgba(255, 255, 255, 0.8),
                             1px 1px 4px rgba(0, 0, 0, 0.8);
                background-color: transparent;
                padding: 0px;
            """)
            artist_label.setAlignment(QtCore.Qt.AlignLeft)

            song_label = QLabel(song_name)
            song_label.setStyleSheet("""
                font-size: 14px;
                font-weight: 400;
                color: rgba(255, 255, 255, 0.9);
                text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.6);
                background-color: transparent;
                padding: 0px;
            """)
            song_label.setAlignment(QtCore.Qt.AlignLeft)
            song_label.setWordWrap(True)

            lyrics_text = QTextEdit()
            lyrics_text.setReadOnly(True)
            lyrics_text.setText(f"♪ {song_name} ♪\n\n[Sample Lyrics]\n가사를 여기에 입력하세요.\n\n예시:\n첫 번째 구절...\n두 번째 구절...")
            lyrics_text.setStyleSheet("""
                font-size: 12px;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                background-color: rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.95);
                padding: 10px;
            """)
            lyrics_text.setFixedHeight(200)

            info_layout.addWidget(artist_label)
            info_layout.addWidget(song_label)
            info_layout.addWidget(lyrics_text)
            info_layout.addStretch()

            main_layout.addWidget(thumbnail_container)
            main_layout.addWidget(info_container)
            self.top_widget.setLayout(main_layout)
            self.main_layout.insertWidget(1, self.top_widget, alignment=QtCore.Qt.AlignCenter)
            self.top_widget.show()  # 명시적 표시
            print(f"top_widget 생성 완료: visible={self.top_widget.isVisible()}, size={self.top_widget.size()}")
        except Exception as e:
            print(f"create_top_widget 오류: {e}")

    def show_lyrics_mode(self):
        try:
            print(
                f"show_lyrics_mode 호출: current_song_index={self.current_song_index}, current_mode={self.current_mode}")
            self.current_mode = "lyrics"
            self.video_widget.hide()
            self.video_player.pause()
            if self.return_button:
                self.return_button.hide()
                print("return_button 숨김")

            # 썸네일 흐린 배경 표시
            artist, song_name = self.parse_song_info(self.songs_list[self.current_song_index])
            thumbnail_path = self.match_thumbnail(song_name)
            if thumbnail_path and os.path.exists(thumbnail_path):
                original_pixmap = QtGui.QPixmap(thumbnail_path)
                if not original_pixmap.isNull():
                    blurred_bg = self.create_blurred_background(original_pixmap)
                    if not self.background_label:
                        self.background_label = QLabel(self)
                    self.background_label.setPixmap(blurred_bg)
                    self.background_label.setGeometry(0, 0, 800, 600)
                    self.background_label.lower()
                    self.background_label.show()
                    print("배경 이미지 표시")
                else:
                    print(f"배경 이미지 로드 실패: {thumbnail_path}")
            else:
                print(f"배경 썸네일 경로 없음: {song_name}")

            self.create_top_widget(self.current_song_index)
            self.update()  # UI 갱신 강제
            print(f"가사 모드 활성화 완료: top_widget visible={self.top_widget.isVisible() if self.top_widget else False}")
        except Exception as e:
            print(f"show_lyrics_mode 오류: {e}")

    def show_video_mode(self):
        try:
            print(f"show_video_mode 호출: current_song_index={self.current_song_index}")
            self.current_mode = "video"
            if self.top_widget:
                print("top_widget 제거")
                self.main_layout.removeWidget(self.top_widget)
                self.top_widget.deleteLater()
                self.top_widget = None
            if self.background_label:
                self.background_label.hide()
                print("background_label 숨김")

            artist, song_name = self.parse_song_info(self.songs_list[self.current_song_index])
            mv_path = self.match_music_video(song_name)
            if mv_path and os.path.exists(mv_path):
                print(f"비디오 파일 로드 시도: {mv_path}")
                self.video_player.setMedia(QMediaContent(QtCore.QUrl.fromLocalFile(mv_path)))
                self.video_widget.show()
                self.video_widget.setGeometry(0, 0, 800, 600)
                self.video_widget.lower()
                self.video_widget.raise_()  # 비디오 위젯 계층 조정
                if self.is_playing:
                    current_pos = self.audio_player.position()
                    print(f"비디오 위치 설정: {self.format_time(current_pos)}")
                    self.video_player.setPosition(current_pos)
                    self.video_player.play()

                # 복귀 버튼
                if not self.return_button:
                    self.return_button = QtWidgets.QPushButton("가사로 돌아가기", self)
                    self.return_button.setFixedSize(150, 40)
                    self.return_button.setStyleSheet("""
                        QPushButton {
                            background-color: rgba(255, 215, 0, 0.8);
                            color: #333;
                            font-size: 14px;
                            font-weight: bold;
                            border-radius: 8px;
                            border: 1px solid rgba(218, 165, 32, 0.8);
                        }
                        QPushButton:hover {
                            background-color: rgba(255, 236, 139, 0.8);
                        }
                        QPushButton:pressed {
                            background-color: rgba(218, 165, 32, 0.8);
                        }
                    """)
                    self.return_button.clicked.connect(self.show_lyrics_mode)
                self.return_button.move(20, 20)
                self.return_button.show()
                self.return_button.raise_()
                print(f"return_button 표시: visible={self.return_button.isVisible()}")

                print(f"뮤직비디오 모드 활성화: {mv_path}")
            else:
                print(f"뮤직비디오 없음: {song_name}")
                self.video_widget.hide()
                self.video_player.setMedia(QMediaContent())
                self.show_lyrics_mode()
            self.update()
        except Exception as e:
            print(f"show_video_mode 오류: {e}")
            self.show_lyrics_mode()  # 오류 시 가사 모드로 대체

    def thumbnail_clicked(self, label_index):
        try:
            song_index = self.thumbnail_labels[label_index].property("song_index")
            if song_index is None:
                song_index = self.current_song_index
            if song_index is not None:
                self.audio_player.pause()
                self.video_player.pause()
                self.position_timer.stop()
                self.current_song_index = song_index
                self.current_display_index = (song_index - 2) % len(self.songs_list)
                self.thumbnail_widget.hide()
                self.is_playing = False
                self.button_play_pause.setIcon(QtGui.QIcon("images/play.png"))
                self.progress_bar.setValue(0)
                self.label_progress.setText("00:00 / 00:00")

                song_path = os.path.join("music", self.songs_list[song_index])
                self.audio_player.setMedia(QMediaContent(QtCore.QUrl.fromLocalFile(song_path)))

                # 현재 모드에 따라 UI 업데이트
                if self.current_mode == "lyrics":
                    self.show_lyrics_mode()
                else:
                    self.show_video_mode()

                # 오디오 재생 시작
                self.audio_player.play()
                self.is_playing = True
                self.button_play_pause.setIcon(QtGui.QIcon("images/pause.png"))
                self.position_timer.start(100)

                print(f"썸네일 클릭: song_index={song_index}, 모드={self.current_mode}")
        except Exception as e:
            print(f"thumbnail_clicked 오류: {e}")

    def toggle_thumbnails(self):
        try:
            self.thumbnail_visible = not self.thumbnail_visible
            if self.thumbnail_visible:
                if self.original_spacing is None:
                    self.original_spacing = self.main_layout.spacing()
                self.main_layout.setSpacing(10)
                self.thumbnail_widget.show()
                self.update_thumbnails()
            else:
                if self.original_spacing is not None:
                    self.main_layout.setSpacing(self.original_spacing)
                self.thumbnail_widget.hide()
        except Exception as e:
            print(f"toggle_thumbnails 오류: {e}")

    def handle_video_status(self, status):
        try:
            status_map = {
                QMediaPlayer.NoMedia: "NoMedia",
                QMediaPlayer.LoadingMedia: "LoadingMedia",
                QMediaPlayer.LoadedMedia: "LoadedMedia",
                QMediaPlayer.BufferedMedia: "BufferedMedia",
                QMediaPlayer.StalledMedia: "StalledMedia",
                QMediaPlayer.EndOfMedia: "EndOfMedia",
                QMediaPlayer.InvalidMedia: "InvalidMedia",
                QMediaPlayer.UnknownMediaStatus: "UnknownMediaStatus"
            }
            print(f"비디오 미디어 상태: {status_map.get(status, 'Unknown')}")
            if status == QMediaPlayer.LoadedMedia:
                if self.is_playing and self.current_mode == "video":
                    current_pos = self.audio_player.position()
                    self.video_player.setPosition(current_pos)
                    self.video_player.play()
                    print(f"비디오 로드 완료, 재생 시작: {self.format_time(current_pos)}")
            elif status == QMediaPlayer.InvalidMedia:
                print("비디오 파일 유효하지 않음")
                self.show_lyrics_mode()
            elif status == QMediaPlayer.EndOfMedia:
                print("비디오 종료, 다음 곡으로 전환")
                self.next_song()
        except Exception as e:
            print(f"handle_video_status 오류: {e}")
    def format_time(self, ms):
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

def main():
    try:
        if not os.path.exists("images"):
            print("images 디렉토리가 없습니다. images 디렉토리에 play.png, pause.png, rewind.png, fastforward.png, songs.png, mute.png를 준비하세요.")
            return
        app = QtWidgets.QApplication(sys.argv)
        window = MP3PlayerUI()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"main 오류: {e}")

if __name__ == "__main__":
    main()