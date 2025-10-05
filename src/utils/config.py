"""
설정 관리 유틸리티

Author: Ju Eun Cho
Date: 2025-09-28
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Union
import logging


class ConfigManager:
    """설정 관리자 클래스"""
    
    def __init__(self, project_root: Union[str, Path] = None):
        """
        설정 관리자 초기화
        
        Args:
            project_root: 프로젝트 루트 경로. None이면 자동 탐지
        """
        if project_root is None:
            # 현재 파일 기준으로 프로젝트 루트 자동 탐지
            current_file = Path(__file__)
            self.project_root = current_file.parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        self.config_dir = self.project_root / "config"
        self._paths = None
        self._model_config = None
        self._experiment_config = None
    
    def _load_yaml(self, file_path: Path) -> Dict[str, Any]:
        """
        YAML 파일 로드
        
        Args:
            file_path: YAML 파일 경로
            
        Returns:
            Dict: 로드된 설정 데이터
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logging.warning(f"설정 파일을 찾을 수 없습니다: {file_path}")
            return {}
        except yaml.YAMLError as e:
            logging.error(f"YAML 파싱 오류: {e}")
            return {}
    
    @property
    def paths(self) -> Dict[str, Any]:
        """경로 설정 가져오기 (캐싱)"""
        if self._paths is None:
            paths_file = self.config_dir / "paths.yaml"
            self._paths = self._load_yaml(paths_file)
        return self._paths
    
    @property
    def model_config(self) -> Dict[str, Any]:
        """모델 설정 가져오기 (캐싱)"""
        if self._model_config is None:
            model_file = self.config_dir / "model_config.yaml"
            self._model_config = self._load_yaml(model_file)
        return self._model_config
    
    @property 
    def experiment_config(self) -> Dict[str, Any]:
        """실험 설정 가져오기 (캐싱)"""
        if self._experiment_config is None:
            exp_file = self.config_dir / "experiment_config.yaml"
            self._experiment_config = self._load_yaml(exp_file)
        return self._experiment_config
    
    def get_path(self, key: str, create_if_missing: bool = False) -> Path:
        """
        설정된 경로 가져오기
        
        Args:
            key: 경로 키 (예: 'data_paths.math_problems')
            create_if_missing: 경로가 없으면 생성할지 여부
            
        Returns:
            Path: 절대 경로
        """
        # 중첩된 키 처리 (예: 'data_paths.math_problems')
        keys = key.split('.')
        config_section = keys[0]
        path_key = keys[1] if len(keys) > 1 else None
        
        paths_config = self.paths.get(config_section, {})
        
        if path_key:
            relative_path = paths_config.get(path_key, "")
        else:
            relative_path = paths_config
        
        if not relative_path:
            raise ValueError(f"경로 키를 찾을 수 없습니다: {key}")
        
        # 절대 경로로 변환
        absolute_path = self.project_root / relative_path
        
        # 필요시 디렉토리 생성
        if create_if_missing:
            if absolute_path.suffix:  # 파일인 경우
                absolute_path.parent.mkdir(parents=True, exist_ok=True)
            else:  # 디렉토리인 경우
                absolute_path.mkdir(parents=True, exist_ok=True)
        
        return absolute_path
    
    def get_data_path(self, data_type: str, create_if_missing: bool = False) -> Path:
        """
        데이터 경로 단축 함수
        
        Args:
            data_type: 데이터 타입 (예: 'math_problems', 'selected_math')
            create_if_missing: 경로가 없으면 생성할지 여부
            
        Returns:
            Path: 데이터 파일/디렉토리 경로
        """
        return self.get_path(f"data_paths.{data_type}", create_if_missing)
    
    def get_results_path(self, result_type: str, create_if_missing: bool = True) -> Path:
        """
        결과 경로 단축 함수
        
        Args:
            result_type: 결과 타입 (예: 'figures', 'tables')
            create_if_missing: 경로가 없으면 생성할지 여부
            
        Returns:
            Path: 결과 저장 경로
        """
        return self.get_path(f"results_paths.{result_type}", create_if_missing)
    
    def get_docs_path(self, doc_type: str, create_if_missing: bool = False) -> Path:
        """
        문서 경로 단축 함수
        
        Args:
            doc_type: 문서 타입 (예: 'paper', 'meeting_notes')
            create_if_missing: 경로가 없으면 생성할지 여부
            
        Returns:
            Path: 문서 경로
        """
        return self.get_path(f"docs_paths.{doc_type}", create_if_missing)
    
    def get_filename(self, file_type: str, **kwargs) -> str:
        """
        설정된 파일명 가져오기
        
        Args:
            file_type: 파일 타입 (예: 'selected_math', 'model_responses_template')
            **kwargs: 파일명 템플릿에 사용할 변수들 (예: model='chatgpt', timestamp='20250928')
            
        Returns:
            str: 파일명
        """
        filenames = self.paths.get('filenames', {})
        filename_template = filenames.get(file_type, "")
        
        if not filename_template:
            raise ValueError(f"파일명 타입을 찾을 수 없습니다: {file_type}")
        
        # 템플릿 변수 치환 (예: responses_{model}_{timestamp}.json)
        if kwargs:
            filename = filename_template.format(**kwargs)
        else:
            filename = filename_template
        
        return filename
    
    def update_config(self, config_type: str, new_config: Dict[str, Any]):
        """
        설정 업데이트 및 저장
        
        Args:
            config_type: 설정 타입 ('paths', 'model', 'experiment')
            new_config: 새로운 설정 데이터
        """
        if config_type == 'paths':
            config_file = self.config_dir / "paths.yaml"
            self._paths = new_config
        elif config_type == 'model':
            config_file = self.config_dir / "model_config.yaml"
            self._model_config = new_config
        elif config_type == 'experiment':
            config_file = self.config_dir / "experiment_config.yaml"
            self._experiment_config = new_config
        else:
            raise ValueError(f"지원하지 않는 설정 타입: {config_type}")
        
        # 파일에 저장
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(new_config, f, default_flow_style=False, allow_unicode=True)
    
    def validate_paths(self) -> Dict[str, bool]:
        """
        주요 경로들이 존재하는지 검증
        
        Returns:
            Dict: 경로별 존재 여부
        """
        validation_results = {}
        
        # 주요 경로들 검증
        important_paths = [
            'data_paths.raw_data',
            'data_paths.processed_data', 
            'data_paths.selected_data',
            'results_paths.figures',
            'results_paths.tables'
        ]
        
        for path_key in important_paths:
            try:
                path = self.get_path(path_key)
                validation_results[path_key] = path.exists()
            except ValueError:
                validation_results[path_key] = False
        
        return validation_results


# 글로벌 config 인스턴스
_global_config = None

def get_config() -> ConfigManager:
    """
    글로벌 config 인스턴스 가져오기
    
    Returns:
        ConfigManager: 설정 관리자 인스턴스
    """
    global _global_config
    if _global_config is None:
        _global_config = ConfigManager()
    return _global_config


# 편의 함수들
def get_data_path(data_type: str, create_if_missing: bool = False) -> Path:
    """데이터 경로 가져오기"""
    return get_config().get_data_path(data_type, create_if_missing)

def get_results_path(result_type: str, create_if_missing: bool = True) -> Path:
    """결과 경로 가져오기"""
    return get_config().get_results_path(result_type, create_if_missing)

def get_docs_path(doc_type: str, create_if_missing: bool = False) -> Path:
    """문서 경로 가져오기"""
    return get_config().get_docs_path(doc_type, create_if_missing)

def get_filename(file_type: str, **kwargs) -> str:
    """파일명 가져오기"""
    return get_config().get_filename(file_type, **kwargs)

if __name__ == "__main__":
    # 테스트 코드
    config = get_config()
    
    print("=== 경로 설정 테스트 ===")
    print(f"프로젝트 루트: {config.project_root}")
    print(f"수학 데이터 경로: {config.get_data_path('math_problems')}")
    print(f"결과 저장 경로: {config.get_results_path('figures')}")
    
    # 경로 검증
    validation = config.validate_paths()
    print(f"\n경로 검증 결과:")
    for path, exists in validation.items():
        status = "✅" if exists else "❌"
        print(f"  {status} {path}")