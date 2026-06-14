"""
리소스 모니터링 시스템 - 메모리 누수 방지 및 자동 정리
장기 가동(2개월 이상)을 위한 안정성 개선 모듈
"""
import psutil
import gc
import logging
from datetime import datetime
from PyQt5.QtCore import QObject, QTimer, pyqtSignal

logger = logging.getLogger(__name__)


class ResourceMonitor(QObject):
    """
    시스템 리소스(메모리, CPU) 모니터링 및 자동 정리
    """
    # 경고 시그널 (메모리 사용량, 경고 레벨: "warning" | "critical")
    memory_warning = pyqtSignal(float, str)

    # 정리 완료 시그널 (해제된 메모리 MB)
    cleanup_completed = pyqtSignal(float)

    # GUI 업데이트 시그널 (메모리 MB, CPU %, 최대 메모리 MB)
    resource_updated = pyqtSignal(float, float, float)

    def __init__(self, parent=None):
        super().__init__(parent)

        # 모니터링 설정
        self.monitor_interval = 60000  # 1분마다 체크
        self.cleanup_interval = 300000  # 5분마다 자동 정리

        # 메모리 임계값 (MB)
        self.memory_warning_threshold = 500  # 500MB 이상 경고
        self.memory_critical_threshold = 800  # 800MB 이상 위험

        # 타이머 설정
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.check_resources)

        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self.auto_cleanup)

        # 통계
        self.max_memory_usage = 0.0
        self.total_cleanups = 0
        self.last_cleanup_time = datetime.now()

        logger.info("[리소스 모니터] 초기화 완료")

    def start(self):
        """모니터링 시작"""
        self.monitor_timer.start(self.monitor_interval)
        self.cleanup_timer.start(self.cleanup_interval)
        logger.info(f"[리소스 모니터] 시작 - 모니터링: {self.monitor_interval/1000}초, 정리: {self.cleanup_interval/1000}초")

    def stop(self):
        """모니터링 중지"""
        self.monitor_timer.stop()
        self.cleanup_timer.stop()
        logger.info("[리소스 모니터] 중지")

    def check_resources(self):
        """리소스 상태 확인"""
        try:
            process = psutil.Process()

            # 메모리 사용량 (MB)
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024

            # 최대 메모리 사용량 갱신
            if memory_mb > self.max_memory_usage:
                self.max_memory_usage = memory_mb

            # CPU 사용률 (%)
            cpu_percent = process.cpu_percent(interval=0.1)

            # GUI 업데이트 시그널 발송 (로그 출력 제거 - GUI에 표시)
            self.resource_updated.emit(memory_mb, cpu_percent, self.max_memory_usage)

            # 경고 체크 (로그 출력 제거 - GUI에서 처리)
            if memory_mb > self.memory_critical_threshold:
                self.memory_warning.emit(memory_mb, "critical")
                # 즉시 정리 수행
                self.auto_cleanup()
            elif memory_mb > self.memory_warning_threshold:
                self.memory_warning.emit(memory_mb, "warning")

        except Exception as e:
            logger.error(f"[리소스 모니터] 리소스 체크 오류: {e}")

    def auto_cleanup(self):
        """자동 메모리 정리"""
        try:
            process = psutil.Process()
            before_memory = process.memory_info().rss / 1024 / 1024

            # Python 가비지 컬렉션 실행
            collected = gc.collect()

            after_memory = process.memory_info().rss / 1024 / 1024
            freed_memory = before_memory - after_memory

            self.total_cleanups += 1
            self.last_cleanup_time = datetime.now()

            logger.info(f"[리소스 모니터] 자동 정리 완료 (#{self.total_cleanups}) - 해제: {freed_memory:.1f}MB | 객체: {collected}개")
            self.cleanup_completed.emit(freed_memory)

        except Exception as e:
            logger.error(f"[리소스 모니터] 자동 정리 오류: {e}")

    def get_stats(self):
        """현재 리소스 통계 반환"""
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            cpu_percent = process.cpu_percent(interval=0.1)

            return {
                "current_memory_mb": memory_mb,
                "max_memory_mb": self.max_memory_usage,
                "cpu_percent": cpu_percent,
                "total_cleanups": self.total_cleanups,
                "last_cleanup": self.last_cleanup_time.strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            logger.error(f"[리소스 모니터] 통계 조회 오류: {e}")
            return None
