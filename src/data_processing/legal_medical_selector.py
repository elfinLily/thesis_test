"""
의료/법률 전문 서적 말뭉치 선별기
BaseSelector를 상속받아 의료/법률 데이터 특화 로직 구현

Author: [Your Name]
Date: 2025-09-28
"""

from .base_selector import BaseSelector
from typing import List, Dict, Any
from collections import Counter, defaultdict
import random


class LegalMedicalSelector(BaseSelector):
    """의료/법률 전문 서적 말뭉치 선별기"""
    
    def _get_default_criteria(self) -> Dict[str, Any]:
        """
        의료/법률 데이터 기본 선별 기준 반환
        
        Returns:
            Dict: 선별 기준
        """
        return {
            'target_count': 40,
            'medical_ratio': 0.5,  # 의료 50%
            'legal_ratio': 0.5,    # 법률 50%
            'difficulty_distribution': {'하': 0.2, '중': 0.5, '상': 0.3},
            'min_word_segment': 100,
            'max_word_segment': 1000,
            'require_category': True
        }
    
    def _parse_data(self, raw_data: Dict, filename: str) -> List[Dict]:
        """
        의료/법률 JSON 데이터 파싱
        
        Args:
            raw_data: 원본 JSON 데이터
            filename: 파일명
            
        Returns:
            List[Dict]: 파싱된 문서 데이터 리스트 (여러 개일 수 있음)
        """
        try:
            # 'data' 키가 있는 경우 (여러 문서가 담긴 경우)
            if 'data' in raw_data:
                documents = raw_data['data']
            else:
                documents = [raw_data]
            
            parsed_list = []
            
            for doc in documents:
                # popularity를 난이도 문자열로 변환
                popularity_map = {1: '하', 2: '중', 3: '상'}
                popularity = doc.get('popularity', 2)
                difficulty = popularity_map.get(popularity, '중')
                
                # book_id로 분야 판단 (M=의료, L=법률)
                book_id = doc.get('book_id', '')
                field = '의료' if book_id.startswith('M') else '법률'
                
                parsed = {
                    'filename': filename,
                    'book_id': book_id,
                    'field': field,
                    'category': doc.get('category', ''),
                    'difficulty': difficulty,
                    'popularity': popularity,
                    'keyword': doc.get('keyword', []),
                    'text': doc.get('text', '').strip(),
                    'word_segment': doc.get('word_segment', 0),
                    'publication_ymd': doc.get('publication_ymd', ''),
                    'text_length': len(doc.get('text', '').strip())
                }
                
                if parsed['text']:  # 텍스트가 있는 것만
                    parsed_list.append(parsed)
            
            return parsed_list
            
        except Exception as e:
            print(f"데이터 파싱 실패 ({filename}): {e}")
            return []
    
    def filter_data(self) -> List[Dict]:
        """
        의료/법률 문서 필터링
        
        Returns:
            List[Dict]: 필터링된 문서 리스트
        """
        filtered = []
        
        for doc in self.data_items:
            # 어절 수 필터
            word_count = doc['word_segment']
            if word_count < self.selection_criteria['min_word_segment']:
                continue
            if word_count > self.selection_criteria['max_word_segment']:
                continue
            
            # 텍스트가 있는 것만
            if not doc['text'] or len(doc['text']) < 50:
                continue
            
            # 카테고리 정보가 있는 것만
            if self.selection_criteria['require_category'] and not doc['category']:
                continue
            
            filtered.append(doc)
        
        print(f"필터링 후: {len(filtered)}개 문서 남음")
        return filtered
    
    def stratified_sampling(self, filtered_data: List[Dict]) -> List[Dict]:
        """
        의료/법률 문서 계층적 샘플링
        - 의료/법률 비율 고려
        - 난이도별 분포 고려
        - 카테고리 다양성 고려
        
        Args:
            filtered_data: 필터링된 문서 리스트
            
        Returns:
            List[Dict]: 선별된 문서 리스트
        """
        target_count = self.selection_criteria['target_count']
        medical_count = int(target_count * self.selection_criteria['medical_ratio'])
        legal_count = target_count - medical_count
        
        # 분야별로 분리
        medical_docs = [d for d in filtered_data if d['field'] == '의료']
        legal_docs = [d for d in filtered_data if d['field'] == '법률']
        
        print(f"의료: {len(medical_docs)}개, 법률: {len(legal_docs)}개")
        
        # 각 분야별로 난이도별 샘플링
        selected_medical = self._sample_by_difficulty(medical_docs, medical_count)
        selected_legal = self._sample_by_difficulty(legal_docs, legal_count)
        
        selected_documents = selected_medical + selected_legal
        print(f"최종 선별: {len(selected_documents)}개 문서 (의료 {len(selected_medical)}개 + 법률 {len(selected_legal)}개)")
        
        return selected_documents
    
    def _sample_by_difficulty(self, documents: List[Dict], target_count: int) -> List[Dict]:
        """
        난이도별 비율에 따라 샘플링
        
        Args:
            documents: 샘플링할 문서 리스트
            target_count: 목표 선별 개수
            
        Returns:
            List[Dict]: 선별된 문서 리스트
        """
        difficulty_dist = self.selection_criteria['difficulty_distribution']
        selected = []
        
        # 난이도별로 그룹화
        by_difficulty = defaultdict(list)
        for doc in documents:
            by_difficulty[doc['difficulty']].append(doc)
        
        # 난이도별 목표 개수 계산
        for difficulty, ratio in difficulty_dist.items():
            target_for_difficulty = int(target_count * ratio)
            available = by_difficulty[difficulty]
            
            if len(available) >= target_for_difficulty:
                # 카테고리 다양성을 고려한 샘플링
                sampled = self._diverse_category_sampling(available, target_for_difficulty)
            else:
                sampled = available
            
            selected.extend(sampled)
            print(f"  {difficulty}급: {len(sampled)}개 선별")
        
        return selected
    
    def _diverse_category_sampling(self, documents: List[Dict], target_count: int) -> List[Dict]:
        """
        카테고리 다양성을 고려한 샘플링
        
        Args:
            documents: 샘플링할 문서 리스트
            target_count: 목표 선별 개수
            
        Returns:
            List[Dict]: 선별된 문서 리스트
        """
        # 카테고리별로 그룹화
        by_category = defaultdict(list)
        for doc in documents:
            by_category[doc['category']].append(doc)
        
        categories = list(by_category.keys())
        selected = []
        
        # 각 카테고리에서 순환하며 선택
        category_index = 0
        attempts = 0
        max_attempts = target_count * 10  # 무한루프 방지
        
        while len(selected) < target_count and len(by_category) > 0 and attempts < max_attempts:
            category = categories[category_index % len(categories)]
            
            if by_category[category]:
                # 해당 카테고리에서 하나 선택
                doc = random.choice(by_category[category])
                selected.append(doc)
                by_category[category].remove(doc)
                
                # 해당 카테고리가 비었으면 제거
                if not by_category[category]:
                    categories.remove(category)
            
            category_index += 1
            attempts += 1
        
        return selected
    
    def _convert_to_queries(self, selected_data: List[Dict], domain: str) -> List[Dict]:
        """
        의료/법률 문서를 AI 모델 테스트용 쿼리 형태로 변환
        
        Args:
            selected_data: 선별된 문서 리스트
            domain: 도메인 식별자
            
        Returns:
            List[Dict]: 쿼리 형태 데이터
        """
        queries = []
        
        for i, doc in enumerate(selected_data, 1):
            query = {
                'id': f"{domain}_{i:03d}",
                'source_file': doc['filename'],
                'metadata': {
                    'field': doc['field'],
                    'category': doc['category'],
                    'difficulty': doc['difficulty'],
                    'word_segment': doc['word_segment'],
                    'publication_ymd': doc['publication_ymd'],
                    'keywords': doc['keyword']
                },
                'query_text': doc['text'],
                'book_id': doc['book_id']
            }
            queries.append(query)
        
        return queries
    
    def _create_summary(self, queries: List[Dict]) -> Dict:
        """
        의료/법률 문서 선별 요약 통계 생성
        
        Args:
            queries: 쿼리 형태 데이터
            
        Returns:
            Dict: 요약 통계
        """
        return {
            'total_count': len(queries),
            'selection_criteria': self.selection_criteria,
            'distribution': {
                'by_field': dict(Counter(q['metadata']['field'] for q in queries)),
                'by_difficulty': dict(Counter(q['metadata']['difficulty'] for q in queries)),
                'by_category': dict(Counter(q['metadata']['category'] for q in queries))
            }
        }


# 전역 편의 함수
def select_legal_medical_documents(target_count: int = 40) -> List[Dict]:
    """
    의료/법률 문서 선별 메인 함수
    
    Args:
        target_count: 목표 선별 개수
        
    Returns:
        List[Dict]: 선별된 문서 리스트
    """
    from src.utils.config import get_config
    
    config = get_config()
    
    # Config에서 경로 가져오기
    data_dir = config.get_data_path('legal_data')
    output_dir = config.get_data_path('selected_data', create_if_missing=True)
    
    # 선별기 초기화 및 실행
    selector = LegalMedicalSelector(str(data_dir))
    selector.selection_criteria['target_count'] = target_count
    
    selected = selector.select_data()
    
    # 결과 저장
    selector.save_selected_data(selected, str(output_dir), domain='legal_medical')
    
    return selected