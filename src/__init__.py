"""
Adaptive LLM Router - 메인 소스 패키지
AI 모델 라우팅 및 성능 비교를 위한 핵심 모듈들

Author: Ju Eun Cho
Date: 2025-09-28
"""

from .utils.config import get_config, get_data_path, get_results_path

__version__ = "0.1.0"
__author__ = "Ju Eun Cho"

# 주요 컴포넌트 임포트
try:
    from .data_processing.selector import MathProblemSelector, select_math_problems
except ImportError:
    pass

try:
    from .utils.config import ConfigManager
except ImportError:
    pass

__all__ = [
    "get_config",
    "get_data_path", 
    "get_results_path",
    "MathProblemSelector",
    "select_math_problems",
    "ConfigManager"
]