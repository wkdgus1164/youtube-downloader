import os
import sys
import platform
import subprocess

# 필요한 라이브러리 확인 및 설치
def install_requirements():
    print("필요한 라이브러리 설치 중...")
    requirements = [
        "pyqt6",
        "pytube",
        "pyinstaller"
    ]
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    for req in requirements:
        subprocess.check_call([sys.executable, "-m", "pip", "install", req])
    print("라이브러리 설치 완료")

# PyInstaller로 실행 파일 빌드
def build_executable():
    os_type = platform.system()
    print(f"{os_type} 운영체제용 빌드를 시작합니다...")
    
    icon_path = ""
    if os_type == "Windows":
        icon_path = os.path.join("resources", "icon.ico")
    elif os_type == "Darwin":  # macOS
        icon_path = os.path.join("resources", "icon.icns")
    
    # resources 디렉토리가 없으면 생성
    os.makedirs("resources", exist_ok=True)
    
    # 기본 아이콘이 없으면 경고
    if not os.path.exists(icon_path):
        print(f"경고: {icon_path} 아이콘 파일이 없습니다. 기본 아이콘으로 빌드합니다.")
        icon_path = ""
    
    # 빌드 옵션 설정
    cmd = [
        "pyinstaller",
        "--name=YouTubeDownloader",
        "--onefile",
        "--windowed",
    ]
    
    if icon_path:
        cmd.append(f"--icon={icon_path}")
    
    # macOS의 경우 추가 옵션
    if os_type == "Darwin":
        cmd.append("--osx-bundle-identifier=com.youtubedownloader.app")
    
    cmd.append("main.py")
    
    # 빌드 실행
    subprocess.check_call(cmd)
    
    print("빌드 완료!")
    
    # 빌드된 파일 경로 안내
    if os_type == "Windows":
        print("실행 파일 위치: dist/YouTubeDownloader.exe")
    elif os_type == "Darwin":
        print("실행 파일 위치: dist/YouTubeDownloader.app")
    else:
        print("실행 파일 위치: dist/YouTubeDownloader")

if __name__ == "__main__":
    print("YouTube 동영상 다운로더 빌드 스크립트")
    print("====================================")
    
    try:
        install_requirements()
        build_executable()
    except Exception as e:
        print(f"오류 발생: {e}")
        sys.exit(1)