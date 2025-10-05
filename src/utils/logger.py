"""
로깅 시스템

주요 기능:
- 콘솔 및 파일 로깅
- 다크모드 친화적 색상 출력
- API 호출 로깅
- 성능 측정 로깅
- 에러 트래킹

Author: Ju Eun Cho
Date: 2025-09-28
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import json
from functools import wraps
import time


# 다크모드 친화적 색상 코드 (ANSI)
class LogColors:
    """로그 색상 정의 (다크모드 최적화)"""
    RESET = '\033[0m'
    
    # 기본 색상 (다크모드에서 잘 보이는 밝은 색)
    DEBUG = '\033[96m'      # 밝은 청록색
    INFO = '\033[92m'       # 밝은 초록색
    WARNING = '\033[93m'    # 밝은 노란색
    ERROR = '\033[91m'      # 밝은 빨간색
    CRITICAL = '\033[95m'   # 밝은 마젠타
    
    # 강조 색상
    TIMESTAMP = '\033[90m'  # 회색
    MODULE = '\033[94m'     # 밝은 파란색
    SUCCESS = '\033[92m'    # 밝은 초록색
    
    # 스타일
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class ColoredFormatter(logging.Formatter):
    """
    다크모드 친화적 색상 포매터
    각 로그 레벨에 따라 다른 색상 적용
    """
    
    FORMATS = {
        logging.DEBUG: f"{LogColors.DEBUG}%(levelname)s{LogColors.RESET} - "
                      f"{LogColors.TIMESTAMP}%(asctime)s{LogColors.RESET} - "
                      f"{LogColors.MODULE}%(name)s{LogColors.RESET} - %(message)s",
        
        logging.INFO: f"{LogColors.INFO}%(levelname)s{LogColors.RESET} - "
                     f"{LogColors.TIMESTAMP}%(asctime)s{LogColors.RESET} - "
                     f"{LogColors.MODULE}%(name)s{LogColors.RESET} - %(message)s",
        
        logging.WARNING: f"{LogColors.WARNING}%(levelname)s{LogColors.RESET} - "
                        f"{LogColors.TIMESTAMP}%(asctime)s{LogColors.RESET} - "
                        f"{LogColors.MODULE}%(name)s{LogColors.RESET} - %(message)s",
        
        logging.ERROR: f"{LogColors.ERROR}%(levelname)s{LogColors.RESET} - "
                      f"{LogColors.TIMESTAMP}%(asctime)s{LogColors.RESET} - "
                      f"{LogColors.MODULE}%(name)s{LogColors.RESET} - %(message)s",
        
        logging.CRITICAL: f"{LogColors.CRITICAL}%(levelname)s{LogColors.RESET} - "
                         f"{LogColors.TIMESTAMP}%(asctime)s{LogColors.RESET} - "
                         f"{LogColors.MODULE}%(name)s{LogColors.RESET} - %(message)s",
    }
    
    def format(self, record):
        """
        로그 레벨에 따라 포맷 적용
        
        Args:
            record: 로그 레코드
            
        Returns:
            str: 포맷된 로그 메시지
        """
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)


class ProjectLogger:
    """프로젝트 로거 관리 클래스"""
    
    _loggers: Dict[str, logging.Logger] = {}
    _initialized = False
    
    @classmethod
    def setup_logger(
        cls,
        name: str = "adaptive-llm-router",
        level: str = "INFO",
        log_to_file: bool = True,
        log_to_console: bool = True,
        log_dir: Optional[Path] = None
    ) -> logging.Logger:
        """
        로거 초기화 및 설정
        
        Args:
            name: 로거 이름
            level: 로그 레벨 ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
            log_to_file: 파일로 로그 저장 여부
            log_to_console: 콘솔에 로그 출력 여부
            log_dir: 로그 파일 저장 디렉토리
            
        Returns:
            logging.Logger: 설정된 로거 인스턴스
        """
        # 이미 설정된 로거가 있으면 반환
        if name in cls._loggers:
            return cls._loggers[name]
        
        # 로거 생성
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))
        
        # 기존 핸들러 제거 (중복 방지)
        logger.handlers.clear()
        
        # 콘솔 핸들러 추가
        if log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.DEBUG)
            console_handler.setFormatter(ColoredFormatter())
            logger.addHandler(console_handler)
        
        # 파일 핸들러 추가
        if log_to_file:
            if log_dir is None:
                # Config에서 로그 디렉토리 가져오기
                try:
                    from .config import get_config
                    config = get_config()
                    log_dir = config.project_root / "logs"
                except:
                    log_dir = Path("logs")
            
            # 로그 디렉토리 생성
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # 메인 로그 파일
            date_str = datetime.now().strftime("%Y%m%d")
            main_log_file = log_dir / f"main_{date_str}.log"
            
            file_handler = logging.FileHandler(main_log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(levelname)s - %(asctime)s - %(name)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
            # 에러 로그 파일 (ERROR 이상만)
            error_log_file = log_dir / f"error_{date_str}.log"
            error_handler = logging.FileHandler(error_log_file, encoding='utf-8')
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(file_formatter)
            logger.addHandler(error_handler)
        
        # 로거 캐싱
        cls._loggers[name] = logger
        cls._initialized = True
        
        logger.info(f"Logger '{name}' 초기화 완료 (Level: {level})")
        
        return logger
    
    @classmethod
    def get_logger(cls, name: str = "adaptive-llm-router") -> logging.Logger:
        """
        로거 인스턴스 가져오기
        초기화되지 않았으면 자동으로 초기화
        
        Args:
            name: 로거 이름
            
        Returns:
            logging.Logger: 로거 인스턴스
        """
        if name not in cls._loggers:
            return cls.setup_logger(name)
        return cls._loggers[name]


def setup_logger(
    name: str = "adaptive-llm-router",
    level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True,
    log_dir: Optional[Path] = None
) -> logging.Logger:
    """
    로거 초기화 전역 함수
    
    Args:
        name: 로거 이름
        level: 로그 레벨
        log_to_file: 파일 로깅 여부
        log_to_console: 콘솔 로깅 여부
        log_dir: 로그 디렉토리
        
    Returns:
        logging.Logger: 설정된 로거
    """
    return ProjectLogger.setup_logger(name, level, log_to_file, log_to_console, log_dir)


def get_logger(name: str = "adaptive-llm-router") -> logging.Logger:
    """
    로거 가져오기 전역 함수
    
    Args:
        name: 로거 이름
        
    Returns:
        logging.Logger: 로거 인스턴스
    """
    return ProjectLogger.get_logger(name)


def log_api_call(
    model_name: str,
    query: str,
    response: str,
    latency: float,
    cost: float,
    success: bool = True,
    error: Optional[str] = None
):
    """
    API 호출 로깅
    
    Args:
        model_name: 모델 이름 (chatgpt, claude, etc)
        query: 입력 쿼리
        response: 응답 텍스트
        latency: 응답 시간 (초)
        cost: API 비용 (USD)
        success: 성공 여부
        error: 에러 메시지 (실패 시)
    """
    logger = get_logger()
    
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'model': model_name,
        'query_length': len(query),
        'response_length': len(response) if response else 0,
        'latency': latency,
        'cost': cost,
        'success': success
    }
    
    if success:
        logger.info(
            f"API Call Success - {model_name} | "
            f"Latency: {latency:.2f}s | Cost: ${cost:.4f}"
        )
    else:
        log_data['error'] = error
        logger.error(
            f"API Call Failed - {model_name} | Error: {error}"
        )
    
    # 상세 로그를 별도 파일에 저장 (선택사항)
    try:
        from .config import get_config
        config = get_config()
        log_dir = config.project_root / "logs" / "api_calls"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        date_str = datetime.now().strftime("%Y%m%d")
        api_log_file = log_dir / f"api_calls_{date_str}.jsonl"
        
        with open(api_log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
    except Exception as e:
        logger.warning(f"API 로그 저장 실패: {e}")


def log_performance(
    operation: str,
    duration: float,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    성능 측정 로깅
    
    Args:
        operation: 작업 이름
        duration: 소요 시간 (초)
        metadata: 추가 메타데이터
    """
    logger = get_logger()
    
    log_msg = f"Performance - {operation} | Duration: {duration:.3f}s"
    
    if metadata:
        log_msg += f" | {metadata}"
    
    logger.info(log_msg)


def log_experiment(
    experiment_id: str,
    config: Dict[str, Any],
    results: Dict[str, Any]
):
    """
    실험 결과 로깅
    
    Args:
        experiment_id: 실험 ID
        config: 실험 설정
        results: 실험 결과
    """
    logger = get_logger()
    
    logger.info(f"Experiment {experiment_id} - Started")
    logger.info(f"Config: {json.dumps(config, ensure_ascii=False, indent=2)}")
    logger.info(f"Results: {json.dumps(results, ensure_ascii=False, indent=2)}")
    
    # 실험 로그 파일 저장
    try:
        from .config import get_config
        config_manager = get_config()
        log_dir = config_manager.project_root / "logs" / "experiments"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        exp_log_file = log_dir / f"experiment_{experiment_id}_{timestamp}.json"
        
        exp_data = {
            'experiment_id': experiment_id,
            'timestamp': datetime.now().isoformat(),
            'config': config,
            'results': results
        }
        
        with open(exp_log_file, 'w', encoding='utf-8') as f:
            json.dump(exp_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Experiment log saved: {exp_log_file}")
    except Exception as e:
        logger.warning(f"실험 로그 저장 실패: {e}")


def timer_decorator(func):
    """
    함수 실행 시간 측정 데코레이터
    
    Args:
        func: 측정할 함수
        
    Returns:
        wrapped function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger()
        start_time = time.time()
        
        logger.debug(f"Function '{func.__name__}' started")
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            logger.info(
                f"Function '{func.__name__}' completed in {duration:.3f}s"
            )
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Function '{func.__name__}' failed after {duration:.3f}s: {e}"
            )
            raise
    
    return wrapper


# 편의 함수들
def log_info(message: str, **kwargs):
    """INFO 레벨 로그"""
    get_logger().info(message, **kwargs)


def log_warning(message: str, **kwargs):
    """WARNING 레벨 로그"""
    get_logger().warning(message, **kwargs)


def log_error(message: str, **kwargs):
    """ERROR 레벨 로그"""
    get_logger().error(message, **kwargs)


def log_debug(message: str, **kwargs):
    """DEBUG 레벨 로그"""
    get_logger().debug(message, **kwargs)


def log_success(message: str):
    """성공 메시지 (초록색 강조)"""
    logger = get_logger()
    logger.info(f"{LogColors.SUCCESS}✓ {message}{LogColors.RESET}")


def log_separator(char: str = "=", length: int = 60):
    """구분선 출력"""
    logger = get_logger()
    logger.info(char * length)


if __name__ == "__main__":
    # 테스트 코드
    print("=== Logger 테스트 ===\n")
    
    # 로거 초기화
    logger = setup_logger(level="DEBUG")
    
    # 다양한 로그 레벨 테스트
    logger.debug("디버그 메시지 - 다크모드에서 잘 보이는 밝은 청록색")
    logger.info("정보 메시지 - 밝은 초록색")
    logger.warning("경고 메시지 - 밝은 노란색")
    logger.error("에러 메시지 - 밝은 빨간색")
    logger.critical("치명적 오류 - 밝은 마젠타")
    
    log_separator()
    
    # 특수 로그 함수 테스트
    log_success("성공적으로 완료되었습니다!")
    
    log_separator()
    
    # API 호출 로그 테스트
    log_api_call(
        model_name="chatgpt",
        query="테스트 질문",
        response="테스트 응답",
        latency=1.23,
        cost=0.0045,
        success=True
    )
    
    # 성능 로그 테스트
    log_performance(
        operation="데이터 선별",
        duration=5.67,
        metadata={'selected_count': 40}
    )
    
    # 데코레이터 테스트
    @timer_decorator
    def test_function():
        time.sleep(0.5)
        return "완료"
    
    result = test_function()
    
    print("\n=== 테스트 완료 ===")