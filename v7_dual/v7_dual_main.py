import sys
import os
import time
import subprocess
import logging
from datetime import datetime
from pathlib import Path

# --watchdog-daemon 모드: GUI에서 생성된 데몬 (현재 실행 중인 GUI PID 감시)
if "--watchdog-daemon" in sys.argv:
    import psutil
    import json

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler('watchdog.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    wd_logger = logging.getLogger("watchdog-daemon")

    def run_watchdog_daemon():
        """GUI에서 생성된 와치독 데몬 - 지정된 PID를 감시하고 크래시 시 재시작"""
        try:
            idx = sys.argv.index("--watchdog-daemon")
            gui_pid = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            wd_logger.error("[Watchdog Daemon] PID가 지정되지 않았습니다.")
            return

        is_frozen = getattr(sys, 'frozen', False)
        config_file = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "api_config.json")

        wd_logger.info(f"[Watchdog Daemon] 시작 - 감시 PID: {gui_pid}")
        wd_logger.info(f"  - Config: {config_file}")

        # GUI PID 감시
        while True:
            try:
                p = psutil.Process(gui_pid)
                if not p.is_running():
                    break
                time.sleep(3)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break

        wd_logger.warning(f"[Watchdog Daemon] GUI 프로세스 종료 감지 (PID: {gui_pid})")

        # config에서 watchdog 상태 확인
        try:
            with open(config_file, "r") as f:
                config = json.load(f)
            app_settings = config.get("app_settings", {})
            watchdog_enabled = app_settings.get("watchdog_enabled", False)
            clean_shutdown = app_settings.get("watchdog_clean_shutdown", False)
        except:
            watchdog_enabled = False
            clean_shutdown = False

        if not watchdog_enabled:
            wd_logger.info("[Watchdog Daemon] watchdog 비활성 - 데몬 종료")
            return

        if clean_shutdown:
            wd_logger.info("[Watchdog Daemon] 정상 종료 감지 (clean_shutdown) - 데몬 종료")
            return

        # 크래시로 판단 → 재시작
        wd_logger.warning("[Watchdog Daemon] 비정상 종료 감지 - 5초 후 재시작...")
        time.sleep(5)

        if is_frozen:
            cmd = [sys.executable, "--auto-restore"]
        else:
            script_path = os.path.abspath(sys.argv[0])
            cmd = [sys.executable, script_path, "--auto-restore"]

        working_dir = Path(sys.executable).resolve().parent if is_frozen else Path(sys.argv[0]).resolve().parent
        wd_logger.info(f"[Watchdog Daemon] 재시작 명령: {' '.join(cmd)}")

        subprocess.Popen(cmd, cwd=working_dir)
        wd_logger.info("[Watchdog Daemon] 재시작 완료 - 데몬 종료")

    run_watchdog_daemon()
    sys.exit(0)

# --watchdog 모드: GUI 없이 프로세스 감시만 수행 (독립 실행용)
if "--watchdog" in sys.argv:
    import psutil

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler('watchdog.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    wd_logger = logging.getLogger("watchdog")

    def run_as_watchdog():
        """와치독 모드 - 자기 자신을 GUI 모드로 실행하고 감시"""
        max_restarts = 10
        restart_delay = 5
        total_restarts = 0
        restart_history = []
        is_frozen = getattr(sys, 'frozen', False)

        wd_logger.info("[Watchdog] 와치독 모드 시작")
        wd_logger.info(f"  - 실행 파일: {sys.executable}")
        wd_logger.info(f"  - 패키징 여부: {'exe' if is_frozen else 'script'}")
        wd_logger.info(f"  - 최대 재시작: {max_restarts}회/시간")

        is_restart = False

        while True:
            try:
                # GUI 프로세스 시작 명령 구성
                if is_frozen:
                    # PyInstaller exe: sys.executable이 exe 자체
                    cmd = [sys.executable]
                else:
                    # Python 스크립트: python.exe + 스크립트 경로
                    script_path = os.path.abspath(sys.argv[0])
                    cmd = [sys.executable, script_path]

                # --watchdog 제외한 나머지 인자 전달
                for arg in sys.argv[1:]:
                    if arg != "--watchdog":
                        cmd.append(arg)

                # 재시작 시 --auto-restore 추가
                if is_restart and "--auto-restore" not in cmd:
                    cmd.append("--auto-restore")

                wd_logger.info(f"[Watchdog] 프로그램 시작{' (재시작)' if is_restart else ''}: {' '.join(cmd)}")

                # 프로세스 시작
                working_dir = Path(sys.argv[0]).resolve().parent if not is_frozen else Path(sys.executable).resolve().parent
                process = subprocess.Popen(cmd, cwd=working_dir)
                pid = process.pid
                wd_logger.info(f"[Watchdog] 프로세스 시작 완료 (PID: {pid})")

                # 프로세스 감시
                while True:
                    if process.poll() is not None:
                        break
                    try:
                        p = psutil.Process(pid)
                        if not p.is_running():
                            break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        break
                    time.sleep(5)

                # 종료 감지
                exit_code = process.poll()
                wd_logger.warning(f"[Watchdog] 프로세스 종료 감지 (종료 코드: {exit_code})")

                # 정상 종료
                if exit_code == 0:
                    wd_logger.info("[Watchdog] 정상 종료 감지 - 감시자 종료")
                    break

                # 크래시 처리
                now = datetime.now()
                restart_history.append(now)

                # 1시간 이내 재시작 횟수 계산
                one_hour_ago = now.timestamp() - 3600
                recent = [r for r in restart_history if r.timestamp() > one_hour_ago]

                wd_logger.warning(f"[Watchdog] 크래시 감지 - 최근 1시간 재시작: {len(recent)}회/{max_restarts}회")

                if len(recent) >= max_restarts:
                    wd_logger.error(f"[Watchdog] 최대 재시작 횟수 초과 ({max_restarts}회/시간) - 감시자 종료")
                    break

                wd_logger.info(f"[Watchdog] {restart_delay}초 후 재시작...")
                time.sleep(restart_delay)

                total_restarts += 1
                is_restart = True
                wd_logger.info(f"[Watchdog] 재시작 #{total_restarts}")

            except KeyboardInterrupt:
                wd_logger.info("[Watchdog] 사용자 중단 (Ctrl+C)")
                try:
                    process.terminate()
                    process.wait(timeout=10)
                except:
                    try:
                        process.kill()
                    except:
                        pass
                break

            except Exception as e:
                wd_logger.error(f"[Watchdog] 예외 발생: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(restart_delay)

    run_as_watchdog()
    sys.exit(0)

# --- 이하 일반 GUI 모드 ---
from PyQt5.QtWidgets import QApplication, QStyleFactory
from PyQt5.QtCore import QObject, pyqtSignal

from v7_dual_gui import AutoTraderGUI

# 커스텀 로그 핸들러 (GUI로 로그를 전송)
class QtLogHandler(logging.Handler, QObject):
    log_signal = pyqtSignal(str)

    def __init__(self):
        logging.Handler.__init__(self)
        QObject.__init__(self)
        self._is_active = True

    def emit(self, record):
        if not self._is_active:
            return
        try:
            msg = self.format(record)
            self.log_signal.emit(msg)
        except (RuntimeError, AttributeError):
            # Qt 객체가 이미 삭제된 경우 무시
            self._is_active = False

    def close(self):
        """핸들러 종료 시 안전하게 정리"""
        self._is_active = False
        try:
            super().close()
        except:
            pass

# print 함수를 오버라이드하여 로그와 GUI로 전송
class PrintLogger:
    def __init__(self, log_handler):
        self.log_handler = log_handler
        self.terminal = sys.stdout  # PyInstaller console=False일 경우 None일 수 있음
        self._is_active = True

    def write(self, message):
        if message.strip():  # 빈 메시지는 무시
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            formatted_msg = f"[{timestamp}] {message}"
            # 터미널이 있을 때만 출력 (console=False일 경우 None)
            if self.terminal is not None:
                try:
                    self.terminal.write(formatted_msg)
                except:
                    pass
            if self.log_handler and self._is_active:
                try:
                    self.log_handler.log_signal.emit(formatted_msg.rstrip())
                except (RuntimeError, AttributeError):
                    # Qt 객체가 이미 삭제된 경우 무시
                    self._is_active = False
        else:
            if self.terminal is not None:
                try:
                    self.terminal.write(message)
                except:
                    pass

    def flush(self):
        if self.terminal is not None:
            try:
                self.terminal.flush()
            except:
                pass

    def deactivate(self):
        """로그 핸들러 비활성화"""
        self._is_active = False
        self.log_handler = None

# 종료 시 정리 함수
def cleanup_logging(original_stdout, print_logger, log_handler):
    """프로그램 종료 전 로깅 시스템 정리"""
    try:
        # PrintLogger 비활성화
        if print_logger:
            print_logger.deactivate()

        # sys.stdout 복원
        sys.stdout = original_stdout

        # logging 핸들러 완전 제거 (atexit.shutdown 전에)
        root_logger = logging.getLogger()

        # 전달받은 log_handler 우선 제거
        if log_handler:
            log_handler._is_active = False
            try:
                log_handler.log_signal.disconnect()
            except:
                pass
            try:
                if log_handler in root_logger.handlers:
                    root_logger.removeHandler(log_handler)
            except:
                pass
            try:
                log_handler.close()
            except:
                pass

        # 남아있는 모든 QtLogHandler 찾아서 제거
        handlers_to_remove = []
        for handler in root_logger.handlers[:]:  # 복사본으로 순회
            if isinstance(handler, QtLogHandler):
                handlers_to_remove.append(handler)

        # 추가 핸들러 비활성화 및 제거
        for handler in handlers_to_remove:
            handler._is_active = False
            try:
                handler.log_signal.disconnect()
            except:
                pass
            try:
                root_logger.removeHandler(handler)
            except:
                pass
            try:
                handler.close()
            except:
                pass

        # logging.shutdown에서 접근하지 못하도록 완전히 제거
        logging._handlers.clear()
        logging._handlerList.clear()

    except Exception as e:
        # 원본 stdout으로 에러 출력 (로깅 시스템을 사용하지 않음)
        try:
            original_stdout.write(f"Cleanup error: {e}\n")
            original_stdout.flush()
        except:
            pass

def is_admin():
    """관리자 권한으로 실행 중인지 확인"""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

if __name__ == '__main__':
    try:
        import requests
        import websockets
        import pyqtgraph # 참고: pyqtgraph는 이제 차트에 필요없지만, 혹시 모를 다른 용도를 위해 남겨둘 수 있습니다.
        from PyQt5 import QtWebEngineWidgets # ◀◀◀ [추가]
    except ImportError as e:
        print(f"오류: 필요한 라이브러리가 설치되지 않았습니다. ({e})")
        print("터미널에서 'pip install PyQt5 pyqtgraph requests websockets PyQtWebEngine'를 실행하세요.")
        sys.exit(1)

    print("프로그램 시작...")

    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))

    # 관리자 권한 확인 및 안내 (와치독 재시작 시 스킵)
    if not is_admin() and "--auto-restore" not in sys.argv:
        from PyQt5.QtWidgets import QMessageBox
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("관리자 권한 필요")
        msg.setText("시간 동기화 기능을 사용하려면 관리자 권한이 필요합니다.")
        msg.setInformativeText(
            "프로그램을 관리자 권한으로 실행하면 Bybit 서버와 PC 시간이 자동으로 동기화됩니다.\n\n"
            "관리자 권한 없이도 프로그램은 정상 작동하지만, 시간 차이가 크면 수동 동기화가 필요할 수 있습니다.\n\n"
            "관리자 권한으로 실행하시겠습니까?"
        )
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.Yes)

        result = msg.exec_()

        if result == QMessageBox.Yes:
            # 관리자 권한으로 재시작
            try:
                import ctypes
                import sys

                # 현재 스크립트 경로
                script = os.path.abspath(sys.argv[0])
                params = ' '.join([script] + sys.argv[1:])

                # 관리자 권한으로 재실행
                ctypes.windll.shell32.ShellExecuteW(
                    None,
                    "runas",  # 관리자 권한 요청
                    sys.executable,  # python.exe
                    params,  # 스크립트 경로와 인자
                    None,
                    1  # SW_SHOWNORMAL
                )

                # 현재 프로세스 종료
                sys.exit(0)

            except Exception as e:
                print(f"관리자 권한으로 재시작 실패: {e}")
                print("수동으로 관리자 권한으로 실행해주세요.")
        else:
            print("[알림] 일반 권한으로 실행합니다. 시간 동기화는 수동으로 수행해야 할 수 있습니다.")

    # 와치독 재시작 시 --auto-restore 인자 감지
    auto_restore = "--auto-restore" in sys.argv

    # GUI 인스턴스 생성
    window = AutoTraderGUI(auto_restore=auto_restore)

    # 로그 핸들러 설정
    log_handler = QtLogHandler()
    log_handler.log_signal.connect(window.append_log)

    # print 함수 오버라이드 (원본 stdout 저장)
    original_stdout = sys.stdout
    print_logger = PrintLogger(log_handler)
    sys.stdout = print_logger

    # 종료 시 정리 함수 연결 (closeEvent 이후 실행되도록)
    def on_app_quit():
        """앱 종료 시 정리 작업"""
        # 로깅 시스템 정리 (closeEvent에서 print 사용 후 실행되어야 함)
        cleanup_logging(original_stdout, print_logger, log_handler)

    app.aboutToQuit.connect(on_app_quit)

    window.show()

    sys.exit(app.exec_())