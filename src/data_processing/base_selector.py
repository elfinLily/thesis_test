"""
데이터 선별기 추상 베이스 클래스
모든 선별기가 상속받아야 할 공통 인터페이스 및 기본 로직

Author: [Your Name]
Date: 2025-09-28
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict, Counter
import json
import numpy as np
import random


class BaseSelector(ABC):
    """데이터 선별기 추상 베이스 클래스"""
    
    def __init__(self, data_dir: str):
        """
        초기화
        
        Args:
            data_dir (str): 데이터 디렉토리 경로
        """
        self.data_dir = Path(data_dir)
        self.data_items = []
        self.selection_criteria = self._get_default_criteria()
    
    @abstractmethod
    def _get_default_criteria(self) -> Dict[str, Any]:
        """
        기본 선별 기준 반환 (각 서브클래스에서 구현)
        
        Returns:
            Dict: 선별 기준 딕셔너리
        """
        pass
    
    @abstractmethod
    def _parse_data(self, data: Dict, filename: str) -> Dict:
        """
        원본 데이터를 파싱 (각 서브클래스에서 구현)
        
        Args:
            data: 원본 JSON 데이터
            filename: 파일명
            
        Returns:
            Dict: 파싱된 데이터
        """
        pass
    
    def load_all_data(self) -> List[Dict]:
        """
        모든 JSON 파일 로드 (공통 로직)
        
        Returns:
            List[Dict]: 로드된 데이터 리스트
        """
        json_files = list(self.data_dir.glob("*.json"))
        print(f"총 {len(json_files)}개의 JSON 파일 발견")
        
        all_data = []
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                    
                    # 서브클래스의 파싱 메서드 호출
                    parsed = self._parse_data(raw_data, json_file.name)
                    
                    if parsed:
                        if isinstance(parsed, list):
                            all_data.extend(parsed)
                        else:
                            all_data.append(parsed)
                            
            except Exception as e:
                print(f"파일 {json_file} 로드 실패: {e}")
        
        self.data_items = all_data
        print(f"총 {len(all_data)}개 데이터 로드 완료")
        return all_data
    
    @abstractmethod
    def filter_data(self) -> List[Dict]:
        """
        데이터 필터링 (각 서브클래스에서 구현)
        
        Returns:
            List[Dict]: 필터링된 데이터
        """
        pass
    
    @abstractmethod
    def stratified_sampling(self, filtered_data: List[Dict]) -> List[Dict]:
        """
        계층적 샘플링 (각 서브클래스에서 구현)
        
        Args:
            filtered_data: 필터링된 데이터
            
        Returns:
            List[Dict]: 선별된 데이터
        """
        pass
    
    def select_data(self) -> List[Dict]:
        """
        전체 선별 프로세스 (공통 로직)
        
        Returns:
            List[Dict]: 선별된 데이터
        """
        print(f"=== {self.__class__.__name__} 데이터 선별 시작 ===")
        
        # 1. 로드
        if not self.data_items:
            self.load_all_data()
        
        # 2. 필터링
        filtered = self.filter_data()
        
        # 3. 샘플링
        selected = self.stratified_sampling(filtered)
        
        print("=== 선별 완료 ===")
        return selected
    
    def save_selected_data(self, selected_data: List[Dict], output_dir: str, domain: str):
        """
        선별 데이터 저장 (공통 로직)
        
        Args:
            selected_data: 선별된 데이터
            output_dir: 출력 디렉토리
            domain: 도메인 식별자
        """
        from src.utils.config import get_filename
        
        filename = get_filename(f'selected_{domain}')
        summary_filename = get_filename(f'selected_{domain}_summary')
        
        output_path = Path(output_dir) / filename
        summary_path = Path(output_dir) / summary_filename
        
        # 쿼리 형태로 변환
        queries = self._convert_to_queries(selected_data, domain)
        
        # 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(queries, f, ensure_ascii=False, indent=2)
        
        print(f"선별된 {len(queries)}개 데이터를 {output_path}에 저장 완료")
        
        # 요약 저장
        summary = self._create_summary(queries)
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"선별 요약을 {summary_path}에 저장 완료")
    
    @abstractmethod
    def _convert_to_queries(self, selected_data: List[Dict], domain: str) -> List[Dict]:
        """
        선별 데이터를 쿼리 형태로 변환 (각 서브클래스에서 구현)
        
        Args:
            selected_data: 선별된 데이터
            domain: 도메인 식별자
            
        Returns:
            List[Dict]: 쿼리 형태 데이터
        """
        pass
    
    @abstractmethod
    def _create_summary(self, queries: List[Dict]) -> Dict:
        """
        요약 통계 생성 (각 서브클래스에서 구현)
        
        Args:
            queries: 쿼리 형태 데이터
            
        Returns:
            Dict: 요약 통계
        """
        pass