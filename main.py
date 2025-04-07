import sys
import os
import json
import threading
import time
import shutil
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# PyQt6를 사용하여 현대적인 UI 구현
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLineEdit, QPushButton, QLabel, QComboBox, QProgressBar, 
                            QListWidget, QListWidgetItem, QFileDialog, QMenu, QSystemTrayIcon, 
                            QSplitter, QTabWidget, QScrollArea, QFrame, QSlider, QSpacerItem,
                            QSizePolicy, QCheckBox, QMessageBox, QToolButton)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QUrl, QTimer, QPoint
from PyQt6.QtGui import QIcon, QPixmap, QAction, QPalette, QColor, QFont, QDesktopServices

# pytube를 사용하여 YouTube 동영상 다운로드
from pytube import YouTube
from pytube.exceptions import RegexMatchError, VideoUnavailable

# 데이터베이스 연결을 위한 sqlite3
import sqlite3

# 현재 사용자의 다운로드 폴더 경로를 기본값으로 설정
DEFAULT_DOWNLOAD_PATH = str(Path.home() / "Downloads")

# 스타일 상수
DARK_MODE = """
    QMainWindow, QWidget {
        background-color: #1e1e2e;
        color: #cdd6f4;
    }
    QLabel {
        color: #cdd6f4;
    }
    QPushButton {
        background-color: #89b4fa;
        color: #1e1e2e;
        border-radius: 4px;
        padding: 8px 16px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #b4befe;
    }
    QPushButton:pressed {
        background-color: #74c7ec;
    }
    QLineEdit {
        background-color: #313244;
        color: #cdd6f4;
        border: 1px solid #45475a;
        border-radius: 4px;
        padding: 8px;
    }
    QComboBox {
        background-color: #313244;
        color: #cdd6f4;
        border: 1px solid #45475a;
        border-radius: 4px;
        padding: 8px;
    }
    QComboBox QAbstractItemView {
        background-color: #313244;
        color: #cdd6f4;
        selection-background-color: #45475a;
    }
    QProgressBar {
        border: 1px solid #45475a;
        border-radius: 4px;
        text-align: center;
    }
    QProgressBar::chunk {
        background-color: #89b4fa;
        border-radius: 4px;
    }
    QListWidget {
        background-color: #313244;
        color: #cdd6f4;
        border: 1px solid #45475a;
        border-radius: 4px;
    }
    QScrollBar:vertical {
        border: none;
        background-color: #313244;
        width: 10px;
        margin: 0px;
    }
    QScrollBar::handle:vertical {
        background-color: #45475a;
        min-height: 20px;
        border-radius: 5px;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    QSplitter::handle {
        background-color: #45475a;
    }
    QTabWidget::pane {
        border: 1px solid #45475a;
        border-radius: 4px;
    }
    QTabBar::tab {
        background-color: #313244;
        color: #cdd6f4;
        padding: 8px 16px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }
    QTabBar::tab:selected {
        background-color: #45475a;
    }
    QCheckBox {
        color: #cdd6f4;
    }
    QToolButton {
        background-color: transparent;
        border: none;
        color: #cdd6f4;
    }
"""

LIGHT_MODE = """
    QMainWindow, QWidget {
        background-color: #f5f5f5;
        color: #333333;
    }
    QLabel {
        color: #333333;
    }
    QPushButton {
        background-color: #3b82f6;
        color: white;
        border-radius: 4px;
        padding: 8px 16px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #2563eb;
    }
    QPushButton:pressed {
        background-color: #1d4ed8;
    }
    QLineEdit {
        background-color: white;
        color: #333333;
        border: 1px solid #d1d5db;
        border-radius: 4px;
        padding: 8px;
    }
    QComboBox {
        background-color: white;
        color: #333333;
        border: 1px solid #d1d5db;
        border-radius: 4px;
        padding: 8px;
    }
    QComboBox QAbstractItemView {
        background-color: white;
        color: #333333;
        selection-background-color: #e5e7eb;
    }
    QProgressBar {
        border: 1px solid #d1d5db;
        border-radius: 4px;
        text-align: center;
    }
    QProgressBar::chunk {
        background-color: #3b82f6;
        border-radius: 4px;
    }
    QListWidget {
        background-color: white;
        color: #333333;
        border: 1px solid #d1d5db;
        border-radius: 4px;
    }
    QScrollBar:vertical {
        border: none;
        background-color: #f5f5f5;
        width: 10px;
        margin: 0px;
    }
    QScrollBar::handle:vertical {
        background-color: #d1d5db;
        min-height: 20px;
        border-radius: 5px;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    QSplitter::handle {
        background-color: #d1d5db;
    }
    QTabWidget::pane {
        border: 1px solid #d1d5db;
        border-radius: 4px;
    }
    QTabBar::tab {
        background-color: #f9fafb;
        color: #333333;
        padding: 8px 16px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }
    QTabBar::tab:selected {
        background-color: #e5e7eb;
    }
    QCheckBox {
        color: #333333;
    }
    QToolButton {
        background-color: transparent;
        border: none;
        color: #333333;
    }
"""

class Database:
    """데이터베이스 관리 클래스"""
    def __init__(self):
        self.db_path = os.path.join(os.path.expanduser("~"), ".youtube_downloader.db")
        self.conn = sqlite3.connect(self.db_path)
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # 설정 테이블
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            download_path TEXT,
            theme TEXT,
            max_concurrent_downloads INTEGER
        )
        ''')
        
        # 다운로드 히스토리 테이블
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS download_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT,
            title TEXT,
            url TEXT,
            file_path TEXT,
            thumbnail_path TEXT,
            format TEXT,
            resolution TEXT,
            download_date TIMESTAMP,
            file_size INTEGER
        )
        ''')
        
        # 기본 설정이 없으면 추가
        cursor.execute("SELECT COUNT(*) FROM settings")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
            INSERT INTO settings (id, download_path, theme, max_concurrent_downloads)
            VALUES (1, ?, 'system', 3)
            ''', (DEFAULT_DOWNLOAD_PATH,))
        
        self.conn.commit()
    
    def get_settings(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM settings WHERE id=1")
        row = cursor.fetchone()
        return {
            'download_path': row[1],
            'theme': row[2],
            'max_concurrent_downloads': row[3]
        }
    
    def update_settings(self, download_path=None, theme=None, max_concurrent_downloads=None):
        cursor = self.conn.cursor()
        current = self.get_settings()
        
        if download_path is not None:
            current['download_path'] = download_path
        if theme is not None:
            current['theme'] = theme
        if max_concurrent_downloads is not None:
            current['max_concurrent_downloads'] = max_concurrent_downloads
        
        cursor.execute('''
        UPDATE settings SET 
            download_path=?, 
            theme=?, 
            max_concurrent_downloads=?
        WHERE id=1
        ''', (current['download_path'], current['theme'], current['max_concurrent_downloads']))
        self.conn.commit()
    
    def add_to_history(self, video_id, title, url, file_path, thumbnail_path, format, resolution, file_size):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO download_history 
        (video_id, title, url, file_path, thumbnail_path, format, resolution, download_date, file_size)
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)
        ''', (video_id, title, url, file_path, thumbnail_path, format, resolution, file_size))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_history(self):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT id, video_id, title, url, file_path, thumbnail_path, format, resolution, download_date, file_size 
        FROM download_history 
        ORDER BY download_date DESC
        ''')
        return cursor.fetchall()
    
    def remove_from_history(self, history_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM download_history WHERE id=?", (history_id,))
        self.conn.commit()
    
    def close(self):
        self.conn.close()


class VideoInfoFetcher(QThread):
    """YouTube 동영상 정보를 가져오는 스레드"""
    info_fetched = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, url):
        super().__init__()
        self.url = url
    
    def run(self):
        try:
            yt = YouTube(self.url)
            thumbnail_url = yt.thumbnail_url
            
            # 이용 가능한 스트림 정보 수집
            video_streams = yt.streams.filter(progressive=True).order_by('resolution').desc()
            audio_streams = yt.streams.filter(only_audio=True).order_by('abr').desc()
            
            video_formats = {}
            for stream in video_streams:
                if stream.resolution not in video_formats:
                    video_formats[stream.resolution] = []
                video_formats[stream.resolution].append({
                    'itag': stream.itag,
                    'mime_type': stream.mime_type,
                    'extension': stream.subtype,
                    'fps': stream.fps,
                    'file_size': stream.filesize,
                    'progressive': True
                })
            
            audio_formats = {}
            for stream in audio_streams:
                if stream.abr not in audio_formats:
                    audio_formats[stream.abr] = []
                audio_formats[stream.abr].append({
                    'itag': stream.itag,
                    'mime_type': stream.mime_type,
                    'extension': stream.subtype,
                    'file_size': stream.filesize
                })
            
            info = {
                'id': yt.video_id,
                'title': yt.title,
                'description': yt.description,
                'author': yt.author,
                'length': yt.length,
                'publish_date': str(yt.publish_date) if yt.publish_date else "Unknown",
                'views': yt.views,
                'rating': yt.rating,
                'thumbnail_url': thumbnail_url,
                'video_formats': video_formats,
                'audio_formats': audio_formats
            }
            
            self.info_fetched.emit(info)
        except Exception as e:
            self.error_occurred.emit(str(e))


class VideoDownloader(QThread):
    """동영상 다운로드를 수행하는 스레드"""
    download_progress = pyqtSignal(int, str)
    download_completed = pyqtSignal(dict)
    download_error = pyqtSignal(str)
    
    def __init__(self, url, itag, download_path, filename=None):
        super().__init__()
        self.url = url
        self.itag = itag
        self.download_path = download_path
        self.filename = filename
        self.cancelled = False
    
    def run(self):
        try:
            yt = YouTube(self.url)
            
            # 진행 상황 콜백 함수
            def progress_callback(stream, chunk, bytes_remaining):
                if self.cancelled:
                    raise Exception("Download cancelled")
                total_size = stream.filesize
                bytes_downloaded = total_size - bytes_remaining
                percentage = int((bytes_downloaded / total_size) * 100)
                self.download_progress.emit(percentage, f"{percentage}% - {bytes_downloaded/1000000:.1f}MB/{total_size/1000000:.1f}MB")
            
            yt.register_on_progress_callback(progress_callback)
            
            # 선택한 스트림 가져오기
            stream = yt.streams.get_by_itag(self.itag)
            
            # 파일명 설정 (사용자 지정 또는 기본값)
            output_filename = self.filename if self.filename else stream.default_filename
            
            # 다운로드 수행
            file_path = stream.download(output_path=self.download_path, filename=output_filename)
            
            # 썸네일 다운로드 (나중에 히스토리에 표시)
            from urllib import request
            thumbnail_path = os.path.join(self.download_path, f"{yt.video_id}_thumbnail.jpg")
            request.urlretrieve(yt.thumbnail_url, thumbnail_path)
            
            # 다운로드 완료 시그널 발생
            download_info = {
                'video_id': yt.video_id,
                'title': yt.title,
                'url': self.url,
                'file_path': file_path,
                'thumbnail_path': thumbnail_path,
                'format': stream.subtype,
                'resolution': stream.resolution if hasattr(stream, 'resolution') else stream.abr,
                'file_size': os.path.getsize(file_path)
            }
            
            self.download_completed.emit(download_info)
            
        except Exception as e:
            if not self.cancelled:
                self.download_error.emit(str(e))
    
    def cancel_download(self):
        self.cancelled = True


class DownloadManager:
    """다운로드 작업을 관리하는 클래스"""
    def __init__(self, max_concurrent_downloads=3):
        self.max_concurrent_downloads = max_concurrent_downloads
        self.active_downloads = {}
        self.download_queue = []
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_downloads)
    
    def add_download(self, download_id, downloader, update_callback):
        """다운로드 작업 추가"""
        if len(self.active_downloads) < self.max_concurrent_downloads:
            self.start_download(download_id, downloader, update_callback)
        else:
            self.download_queue.append((download_id, downloader, update_callback))
    
    def start_download(self, download_id, downloader, update_callback):
        """다운로드 작업 시작"""
        self.active_downloads[download_id] = downloader
        update_callback('active')  # UI 업데이트 콜백
        downloader.start()
    
    def remove_download(self, download_id):
        """다운로드 작업 제거"""
        if download_id in self.active_downloads:
            downloader = self.active_downloads.pop(download_id)
            downloader.cancel_download()
            
            # 대기열에서 다음 다운로드 시작
            if self.download_queue:
                next_download = self.download_queue.pop(0)
                self.start_download(*next_download)
    
    def download_completed(self, download_id):
        """다운로드 완료 처리"""
        if download_id in self.active_downloads:
            self.active_downloads.pop(download_id)
            
            # 대기열에서 다음 다운로드 시작
            if self.download_queue:
                next_download = self.download_queue.pop(0)
                self.start_download(*next_download)
    
    def set_max_concurrent_downloads(self, max_downloads):
        """최대 동시 다운로드 수 설정"""
        self.max_concurrent_downloads = max_downloads
        self.executor.shutdown(wait=False)
        self.executor = ThreadPoolExecutor(max_workers=max_downloads)
        
        # 필요한 경우 대기 중인 다운로드 시작
        while len(self.active_downloads) < self.max_concurrent_downloads and self.download_queue:
            next_download = self.download_queue.pop(0)
            self.start_download(*next_download)
    
    def clear_all(self):
        """모든 다운로드 작업 취소"""
        for download_id, downloader in self.active_downloads.items():
            downloader.cancel_download()
        
        self.active_downloads.clear()
        self.download_queue.clear()


class VideoInfoWidget(QWidget):
    """비디오 정보 및 다운로드 옵션을 표시하는 위젯"""
    download_requested = pyqtSignal(str, int, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_info = None
        self.setup_ui()
    
    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        
        # 비디오 정보 헤더
        self.header_layout = QHBoxLayout()
        
        # 썸네일 라벨
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(240, 180)
        self.thumbnail_label.setScaledContents(True)
        self.thumbnail_label.setStyleSheet("background-color: #333333; border-radius: 8px;")
        self.header_layout.addWidget(self.thumbnail_label)
        
        # 제목과 기본 정보
        self.info_layout = QVBoxLayout()
        
        self.title_label = QLabel()
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.info_layout.addWidget(self.title_label)
        
        self.author_label = QLabel()
        self.info_layout.addWidget(self.author_label)
        
        self.stats_layout = QHBoxLayout()
        self.length_label = QLabel()
        self.views_label = QLabel()
        self.date_label = QLabel()
        
        self.stats_layout.addWidget(self.length_label)
        self.stats_layout.addWidget(self.views_label)
        self.stats_layout.addWidget(self.date_label)
        self.info_layout.addLayout(self.stats_layout)
        
        self.header_layout.addLayout(self.info_layout)
        self.layout.addLayout(self.header_layout)
        
        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        self.layout.addWidget(line)
        
        # 다운로드 옵션
        self.options_layout = QVBoxLayout()
        
        # 비디오 포맷 선택
        self.format_layout = QHBoxLayout()
        self.format_label = QLabel("화질 및 포맷:")
        self.format_combo = QComboBox()
        self.format_combo.setFixedHeight(40)
        self.format_layout.addWidget(self.format_label)
        self.format_layout.addWidget(self.format_combo)
        self.options_layout.addLayout(self.format_layout)
        
        # 파일명 입력
        self.filename_layout = QHBoxLayout()
        self.filename_label = QLabel("파일명:")
        self.filename_edit = QLineEdit()
        self.filename_edit.setPlaceholderText("기본 파일명 사용")
        self.filename_layout.addWidget(self.filename_label)
        self.filename_layout.addWidget(self.filename_edit)
        self.options_layout.addLayout(self.filename_layout)
        
        # 다운로드 버튼
        self.download_btn = QPushButton("다운로드")
        self.download_btn.setFixedHeight(40)
        self.download_btn.clicked.connect(self.request_download)
        self.options_layout.addWidget(self.download_btn)
        
        self.layout.addLayout(self.options_layout)
        
        # 비디오 설명
        self.description_label = QLabel("설명:")
        self.layout.addWidget(self.description_label)
        
        self.description_text = QLabel()
        self.description_text.setWordWrap(True)
        self.description_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        self.description_scroll = QScrollArea()
        self.description_scroll.setWidgetResizable(True)
        self.description_scroll.setWidget(self.description_text)
        self.description_scroll.setFixedHeight(120)
        
        self.layout.addWidget(self.description_scroll)
        
        # 초기 상태는 숨김
        self.setVisible(False)
    
    def set_video_info(self, info):
        """비디오 정보 설정"""
        self.video_info = info
        
        # UI 업데이트
        self.title_label.setText(info['title'])
        self.author_label.setText(f"제작자: {info['author']}")
        
        # 시간 포맷 변환
        length_seconds = info['length']
        hours = length_seconds // 3600
        minutes = (length_seconds % 3600) // 60
        seconds = length_seconds % 60
        
        length_str = ""
        if hours > 0:
            length_str = f"{hours}시간 {minutes}분 {seconds}초"
        else:
            length_str = f"{minutes}분 {seconds}초"
        
        self.length_label.setText(f"길이: {length_str}")
        self.views_label.setText(f"조회수: {info['views']:,}")
        self.date_label.setText(f"업로드: {info['publish_date']}")
        
        # 설명 설정
        self.description_text.setText(info['description'])
        
        # 썸네일 가져오기
        from urllib import request
        from PyQt6.QtCore import QByteArray
        try:
            data = request.urlopen(info['thumbnail_url']).read()
            image = QPixmap()
            image.loadFromData(QByteArray(data))
            self.thumbnail_label.setPixmap(image)
        except Exception:
            # 썸네일 로드 실패 시 기본 이미지
            self.thumbnail_label.setText("썸네일 로드 실패")
        
        # 포맷 콤보박스 채우기
        self.format_combo.clear()
        
        # 비디오 포맷 추가
        for resolution in info['video_formats']:
            for format_info in info['video_formats'][resolution]:
                file_size_mb = format_info['file_size'] / (1024 * 1024)
                self.format_combo.addItem(
                    f"비디오 - {resolution} - {format_info['extension']} - {format_info['fps']}fps - {file_size_mb:.1f}MB",
                    format_info['itag']
                )
        
        # 오디오 포맷 추가
        for abr in info['audio_formats']:
            for format_info in info['audio_formats'][abr]:
                file_size_mb = format_info['file_size'] / (1024 * 1024)
                self.format_combo.addItem(
                    f"오디오 - {abr} - {format_info['extension']} - {file_size_mb:.1f}MB",
                    format_info['itag']
                )
        
        # 위젯 표시
        self.setVisible(True)
    
    def clear(self):
        """위젯 초기화"""
        self.video_info = None
        self.title_label.setText("")
        self.author_label.setText("")
        self.length_label.setText("")
        self.views_label.setText("")
        self.date_label.setText("")
        self.description_text.setText("")
        self.thumbnail_label.clear()
        self.format_combo.clear()
        self.filename_edit.clear()
        self.setVisible(False)
    
    def request_download(self):
        """다운로드 요청 처리"""
        if not self.video_info:
            return
        
        # 선택된 itag 가져오기
        selected_index = self.format_combo.currentIndex()
        if selected_index < 0:
            return
        
        itag = self.format_combo.itemData(selected_index)
        
        # 파일명 가져오기
        filename = self.filename_edit.text().strip()
        if not filename:
            filename = None
        
        # 다운로드 요청 시그널 발생
        self.download_requested.emit(self.video_info['id'], itag, filename)


class DownloadHistoryWidget(QWidget):
    """다운로드 히스토리를 표시하는 위젯"""
    open_file_location = pyqtSignal(str)
    remove_history = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        
        # 제목
        self.title_label = QLabel("다운로드 히스토리")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.layout.addWidget(self.title_label)
        
        # 히스토리 목록
        self.history_list = QListWidget()
        self.history_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.history_list.customContextMenuRequested.connect(self.show_context_menu)
        self.layout.addWidget(self.history_list)
    
    def update_history(self, history_items):
        """히스토리 목록 업데이트"""
        self.history_list.clear()
        
        for item in history_items:
            history_id, video_id, title, url, file_path, thumbnail_path, format, resolution, download_date, file_size = item
            
            # 아이템 위젯 생성
            widget = QWidget()
            layout = QHBoxLayout(widget)
            
            # 썸네일 표시
            thumbnail_label = QLabel()
            thumbnail_label.setFixedSize(120, 68)
            if os.path.exists(thumbnail_path):
                thumbnail_pixmap = QPixmap(thumbnail_path)
                thumbnail_label.setPixmap(thumbnail_pixmap.scaled(120, 68, Qt.AspectRatioMode.KeepAspectRatio))
            else:
                thumbnail_label.setText("이미지 없음")
            
            layout.addWidget(thumbnail_label)
            
            # 정보 레이아웃
            info_layout = QVBoxLayout()
            
            title_label = QLabel(title)
            title_label.setStyleSheet("font-weight: bold;")
            info_layout.addWidget(title_label)
            
            # 파일 정보 및 날짜
            file_size_mb = file_size / (1024 * 1024) if file_size else 0
            details_label = QLabel(f"{resolution} - {format} - {file_size_mb:.1f}MB - {download_date}")
            info_layout.addWidget(details_label)
            
            layout.addLayout(info_layout)
            
            # 아이템에 히스토리 ID 저장
            item_widget = QListWidgetItem()
            item_widget.setData(Qt.ItemDataRole.UserRole, history_id)
            item_widget.setSizeHint(widget.sizeHint())
            
            self.history_list.addItem(item_widget)
            self.history_list.setItemWidget(item_widget, widget)
    
    def show_context_menu(self, position):
        """컨텍스트 메뉴 표시"""
        item = self.history_list.itemAt(position)
        if not item:
            return
        
        history_id = item.data(Qt.ItemDataRole.UserRole)
        
        menu = QMenu()
        open_location_action = menu.addAction("파일 위치 열기")
        remove_action = menu.addAction("기록에서 삭제")
        
        action = menu.exec(self.history_list.mapToGlobal(position))
        
        if action == open_location_action:
            widget = self.history_list.itemWidget(item)
            self.open_file_location.emit(os.path.dirname(self.get_file_path(history_id)))
        elif action == remove_action:
            self.remove_history.emit(history_id)
    
    def get_file_path(self, history_id):
        """히스토리 ID로 파일 경로 가져오기"""
        for i in range(self.history_list.count()):
            item = self.history_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == history_id:
                # TODO: 실제 데이터베이스에서 경로 가져오기
                return ""
        return ""


class SettingsWidget(QWidget):
    """설정 위젯"""
    settings_updated = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = {}
        self.setup_ui()
    
    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        
        # 제목
        self.title_label = QLabel("설정")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.layout.addWidget(self.title_label)
        
        # 다운로드 경로 설정
        self.path_layout = QHBoxLayout()
        self.path_label = QLabel("다운로드 경로:")
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        self.path_btn = QPushButton("변경")
        self.path_btn.clicked.connect(self.change_download_path)
        
        self.path_layout.addWidget(self.path_label)
        self.path_layout.addWidget(self.path_edit)
        self.path_layout.addWidget(self.path_btn)
        self.layout.addLayout(self.path_layout)
        
        # 테마 설정
        self.theme_layout = QHBoxLayout()
        self.theme_label = QLabel("테마:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["시스템 설정 따르기", "라이트 모드", "다크 모드"])
        self.theme_combo.currentIndexChanged.connect(self.on_theme_changed)
        
        self.theme_layout.addWidget(self.theme_label)
        self.theme_layout.addWidget(self.theme_combo)
        self.layout.addLayout(self.theme_layout)
        
        # 최대 동시 다운로드 수
        self.concurrent_layout = QHBoxLayout()
        self.concurrent_label = QLabel("최대 동시 다운로드 수:")
        self.concurrent_combo = QComboBox()
        self.concurrent_combo.addItems(["1", "2", "3", "4", "5"])
        self.concurrent_combo.setCurrentIndex(2)  # 기본값 3
        self.concurrent_combo.currentIndexChanged.connect(self.on_concurrent_changed)
        
        self.concurrent_layout.addWidget(self.concurrent_label)
        self.concurrent_layout.addWidget(self.concurrent_combo)
        self.layout.addLayout(self.concurrent_layout)
        
        # 여백 추가
        spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.layout.addItem(spacer)
    
    def set_settings(self, settings):
        """설정 값 설정"""
        self.settings = settings
        self.path_edit.setText(settings['download_path'])
        
        # 테마 설정
        if settings['theme'] == 'system':
            self.theme_combo.setCurrentIndex(0)
        elif settings['theme'] == 'light':
            self.theme_combo.setCurrentIndex(1)
        else:  # 'dark'
            self.theme_combo.setCurrentIndex(2)
        
        # 최대 동시 다운로드 수
        max_downloads = min(5, max(1, settings['max_concurrent_downloads']))
        self.concurrent_combo.setCurrentIndex(max_downloads - 1)
    
    def change_download_path(self):
        """다운로드 경로 변경"""
        directory = QFileDialog.getExistingDirectory(
            self, "다운로드 경로 선택", self.path_edit.text(),
            QFileDialog.Option.ShowDirsOnly
        )
        
        if directory:
            self.path_edit.setText(directory)
            self.settings['download_path'] = directory
            self.settings_updated.emit(self.settings)
    
    def on_theme_changed(self, index):
        """테마 변경 처리"""
        themes = ['system', 'light', 'dark']
        self.settings['theme'] = themes[index]
        self.settings_updated.emit(self.settings)
    
    def on_concurrent_changed(self, index):
        """최대 동시 다운로드 수 변경 처리"""
        self.settings['max_concurrent_downloads'] = index + 1
        self.settings_updated.emit(self.settings)


class ActiveDownloadWidget(QWidget):
    """활성 다운로드를 표시하는 위젯"""
    cancel_download = pyqtSignal(str)
    
    def __init__(self, download_id, title, parent=None):
        super().__init__(parent)
        self.download_id = download_id
        self.title = title
        self.setup_ui()
    
    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        
        # 파일명 및 취소 버튼
        self.header_layout = QHBoxLayout()
        
        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet("font-weight: bold;")
        self.title_label.setWordWrap(True)
        
        self.cancel_btn = QToolButton()
        self.cancel_btn.setText("✕")
        self.cancel_btn.setToolTip("다운로드 취소")
        self.cancel_btn.clicked.connect(self.request_cancel)
        
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addWidget(self.cancel_btn)
        self.layout.addLayout(self.header_layout)
        
        # 진행률 표시
        self.progress_layout = QHBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        self.progress_label = QLabel("0%")
        
        self.progress_layout.addWidget(self.progress_bar)
        self.progress_layout.addWidget(self.progress_label)
        self.layout.addLayout(self.progress_layout)
        
        # 배경 스타일
        self.setStyleSheet("background-color: rgba(0, 0, 0, 0.05); border-radius: 4px;")
    
    def update_progress(self, percentage, text):
        """진행률 업데이트"""
        self.progress_bar.setValue(percentage)
        self.progress_label.setText(text)
    
    def request_cancel(self):
        """다운로드 취소 요청"""
        self.cancel_download.emit(self.download_id)


class MainWindow(QMainWindow):
    """프로그램 메인 윈도우"""
    def __init__(self):
        super().__init__()
        
        # 데이터베이스 초기화
        self.db = Database()
        
        # 설정 불러오기
        self.settings = self.db.get_settings()
        
        # 다운로드 관리자 초기화
        self.download_manager = DownloadManager(
            max_concurrent_downloads=self.settings['max_concurrent_downloads']
        )
        
        # 활성 다운로드 위젯 매핑
        self.active_downloads = {}
        
        self.setup_ui()
        self.setup_tray_icon()
        
        # 테마 적용
        self.apply_theme()
        
        # 히스토리 로드
        self.load_history()
    
    def setup_ui(self):
        """UI 초기화"""
        self.setWindowTitle("YouTube 동영상 다운로더")
        self.setMinimumSize(1000, 700)
        
        # 중앙 위젯 설정
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 메인 레이아웃
        self.main_layout = QHBoxLayout(self.central_widget)
        
        # 스플리터 생성
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_layout.addWidget(self.splitter)
        
        # 왼쪽 패널 (주 기능)
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.left_panel)
        
        # URL 입력 부분
        self.url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("YouTube URL을 입력하세요")
        self.url_input.returnPressed.connect(self.on_fetch_video_info)
        
        self.fetch_btn = QPushButton("정보 가져오기")
        self.fetch_btn.clicked.connect(self.on_fetch_video_info)
        
        self.url_layout.addWidget(self.url_input)
        self.url_layout.addWidget(self.fetch_btn)
        self.left_layout.addLayout(self.url_layout)
        
        # 비디오 정보 및 다운로드 옵션 위젯
        self.video_info_widget = VideoInfoWidget()
        self.video_info_widget.download_requested.connect(self.on_download_requested)
        self.left_layout.addWidget(self.video_info_widget)
        
        # 활성 다운로드 영역
        self.downloads_label = QLabel("활성 다운로드")
        self.downloads_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.left_layout.addWidget(self.downloads_label)
        
        self.active_downloads_container = QWidget()
        self.active_downloads_layout = QVBoxLayout(self.active_downloads_container)
        self.active_downloads_layout.setContentsMargins(0, 0, 0, 0)
        self.active_downloads_layout.setSpacing(10)
        
        self.active_downloads_scroll = QScrollArea()
        self.active_downloads_scroll.setWidgetResizable(True)
        self.active_downloads_scroll.setWidget(self.active_downloads_container)
        
        self.left_layout.addWidget(self.active_downloads_scroll)
        
        # 오른쪽 패널 (히스토리 및 설정)
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        
        # 탭 위젯
        self.tab_widget = QTabWidget()
        
        # 히스토리 탭
        self.history_widget = DownloadHistoryWidget()
        self.history_widget.open_file_location.connect(self.open_file_location)
        self.history_widget.remove_history.connect(self.remove_from_history)
        self.tab_widget.addTab(self.history_widget, "다운로드 기록")
        
        # 설정 탭
        self.settings_widget = SettingsWidget()
        self.settings_widget.set_settings(self.settings)
        self.settings_widget.settings_updated.connect(self.on_settings_updated)
        self.tab_widget.addTab(self.settings_widget, "설정")
        
        self.right_layout.addWidget(self.tab_widget)
        
        # 스플리터에 패널 추가
        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.right_panel)
        
        # 스플리터 크기 설정
        self.splitter.setSizes([700, 300])
    
    def setup_tray_icon(self):
        """시스템 트레이 아이콘 설정"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon.fromTheme("video-display"))
        
        # 트레이 메뉴
        tray_menu = QMenu()
        
        show_action = QAction("표시", self)
        show_action.triggered.connect(self.show)
        
        quit_action = QAction("종료", self)
        quit_action.triggered.connect(self.on_quit)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
    
    def apply_theme(self):
        """테마 적용"""
        style = ""
        
        if self.settings['theme'] == 'system':
            # 시스템 설정에 따라 라이트/다크 모드 확인
            app = QApplication.instance()
            is_dark = app.styleHints().colorScheme() == Qt.ColorScheme.Dark
            style = DARK_MODE if is_dark else LIGHT_MODE
        elif self.settings['theme'] == 'light':
            style = LIGHT_MODE
        else:  # 'dark'
            style = DARK_MODE
        
        self.setStyleSheet(style)
    
    def load_history(self):
        """다운로드 히스토리 로드"""
        history_items = self.db.get_history()
        self.history_widget.update_history(history_items)
    
    def on_fetch_video_info(self):
        """비디오 정보 가져오기"""
        url = self.url_input.text().strip()
        if not url:
            return
        
        # 입력 비활성화
        self.url_input.setEnabled(False)
        self.fetch_btn.setEnabled(False)
        self.fetch_btn.setText("로딩 중...")
        
        # 비디오 정보 가져오기 스레드 시작
        self.info_fetcher = VideoInfoFetcher(url)
        self.info_fetcher.info_fetched.connect(self.on_info_fetched)
        self.info_fetcher.error_occurred.connect(self.on_info_error)
        self.info_fetcher.start()
    
    def on_info_fetched(self, info):
        """비디오 정보 가져오기 완료"""
        # 입력 다시 활성화
        self.url_input.setEnabled(True)
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText("정보 가져오기")
        
        # 정보 위젯 업데이트
        self.video_info_widget.set_video_info(info)
    
    def on_info_error(self, error_msg):
        """비디오 정보 가져오기 오류"""
        # 입력 다시 활성화
        self.url_input.setEnabled(True)
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText("정보 가져오기")
        
        # 오류 메시지 표시
        QMessageBox.critical(self, "오류", f"비디오 정보를 가져오는 중 오류가 발생했습니다:\n{error_msg}")
        
        # 정보 위젯 초기화
        self.video_info_widget.clear()
    
    def on_download_requested(self, video_id, itag, filename):
        """다운로드 요청 처리"""
        # 비디오 URL 가져오기
        url = self.url_input.text().strip()
        
        # 고유 다운로드 ID 생성
        download_id = f"{video_id}_{int(time.time())}"
        
        # 다운로드 위젯 생성
        title = self.video_info_widget.title_label.text()
        download_widget = ActiveDownloadWidget(download_id, title)
        download_widget.cancel_download.connect(self.on_cancel_download)
        
        # 위젯을 활성 다운로드 영역에 추가
        self.active_downloads_layout.addWidget(download_widget)
        self.active_downloads[download_id] = download_widget
        
        # 다운로드 스레드 생성
        downloader = VideoDownloader(url, itag, self.settings['download_path'], filename)
        downloader.download_progress.connect(lambda p, t, wid=download_widget: wid.update_progress(p, t))
        downloader.download_completed.connect(lambda info, did=download_id: self.on_download_completed(info, did))
        downloader.download_error.connect(lambda err, did=download_id: self.on_download_error(err, did))
        
        # 다운로드 관리자에 추가
        self.download_manager.add_download(
            download_id, 
            downloader, 
            lambda status, did=download_id: self.update_download_status(did, status)
        )
    
    def on_cancel_download(self, download_id):
        """다운로드 취소 요청 처리"""
        # 다운로드 관리자에서 제거
        self.download_manager.remove_download(download_id)
        
        # 위젯 제거
        if download_id in self.active_downloads:
            widget = self.active_downloads.pop(download_id)
            self.active_downloads_layout.removeWidget(widget)
            widget.deleteLater()
    
    def on_download_completed(self, info, download_id):
        """다운로드 완료 처리"""
        # 히스토리에 추가
        self.db.add_to_history(
            info['video_id'],
            info['title'],
            info['url'],
            info['file_path'],
            info['thumbnail_path'],
            info['format'],
            info['resolution'],
            info['file_size']
        )
        
        # 다운로드 관리자에서 완료 처리
        self.download_manager.download_completed(download_id)
        
        # 위젯 제거
        if download_id in self.active_downloads:
            widget = self.active_downloads.pop(download_id)
            self.active_downloads_layout.removeWidget(widget)
            widget.deleteLater()
        
        # 히스토리 새로고침
        self.load_history()
    
    def on_download_error(self, error_msg, download_id):
        """다운로드 오류 처리"""
        # 오류 메시지 표시
        QMessageBox.warning(self, "다운로드 오류", f"다운로드 중 오류가 발생했습니다:\n{error_msg}")
        
        # 다운로드 관리자에서 완료 처리
        self.download_manager.download_completed(download_id)
        
        # 위젯 제거
        if download_id in self.active_downloads:
            widget = self.active_downloads.pop(download_id)
            self.active_downloads_layout.removeWidget(widget)
            widget.deleteLater()
    
    def update_download_status(self, download_id, status):
        """다운로드 상태 업데이트"""
        # 필요시 UI 업데이트
        pass
    
    def on_settings_updated(self, settings):
        """설정 업데이트 처리"""
        # 이전 설정과 비교하여 변경된 부분 처리
        if settings['download_path'] != self.settings['download_path']:
            # 다운로드 경로 변경
            self.settings['download_path'] = settings['download_path']
            self.db.update_settings(download_path=settings['download_path'])
        
        if settings['theme'] != self.settings['theme']:
            # 테마 변경
            self.settings['theme'] = settings['theme']
            self.db.update_settings(theme=settings['theme'])
            self.apply_theme()
        
        if settings['max_concurrent_downloads'] != self.settings['max_concurrent_downloads']:
            # 최대 동시 다운로드 수 변경
            self.settings['max_concurrent_downloads'] = settings['max_concurrent_downloads']
            self.db.update_settings(max_concurrent_downloads=settings['max_concurrent_downloads'])
            self.download_manager.set_max_concurrent_downloads(settings['max_concurrent_downloads'])
    
    def open_file_location(self, directory):
        """파일 위치 열기"""
        # OS별 처리
        if os.path.exists(directory):
            QDesktopServices.openUrl(QUrl.fromLocalFile(directory))
    
    def remove_from_history(self, history_id):
        """히스토리에서 항목 제거"""
        self.db.remove_from_history(history_id)
        self.load_history()
    
    def closeEvent(self, event):
        """창 닫기 이벤트 처리"""
        # 다운로드 진행 중인 경우 숨기고 종료하지 않음
        if self.active_downloads:
            self.hide()
            event.ignore()
        else:
            # 완전히 종료
            self.on_quit()
    
    def on_quit(self):
        """프로그램 종료"""
        # 활성 다운로드 모두 취소
        self.download_manager.clear_all()
        
        # 데이터베이스 연결 종료
        self.db.close()
        
        # 애플리케이션 종료
        QApplication.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # 창을 닫아도 앱 종료 안함 (트레이 아이콘)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())