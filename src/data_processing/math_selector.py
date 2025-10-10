"""
수학 교과 문제 데이터 선별
"""

from .base_selector import BaseSelector
from typing import List, Dict, Any
from collections import Counter, defaultdict
import random


class MathProblemSelector(BaseSelector):
    """수학 교과 문제 데이터 선별기"""
    
    def _get_default_criteria(self) -> Dict[str, Any]:
        """
        수학 데이터 기본 선별 기준 반환
        
        Returns:
            Dict: 선별 기준
        """
        return {
            'target_count': 40,
            'subjective_ratio': 0.8,  # 주관식 80%
            'difficulty_distribution': {'상': 0.2, '중': 0.5, '하': 0.3},
            'school_filter': ['중학교', '고등학교'],
            'min_text_length': 20,
            'max_text_length': 800,
            'require_explanation': True
        }
    
    def _parse_data(self, data: Dict, filename: str) -> Dict:
        """
        수학 문제 JSON 데이터 파싱
        
        Args:
            data: 원본 JSON 데이터
            filename: 파일명
            
        Returns:
            Dict: 파싱된 수학 문제 데이터
        """
        try:
            # 기본 정보 추출
            raw_info = data.get('raw_data_info', {})
            source_info = data.get('source_data_info', {})
            learning_info = data.get('learning_data_info', [])
            
            # 문제 텍스트 구성
            problem_text = ""
            answer_text = ""
            explanation_text = ""
            
            for info in learning_info:
                class_name = info.get('class_name', '')
                if '문항' in class_name:
                    text_desc = info.get('class_info_list', [{}])[0].get('text_description', '')
                    problem_text += text_desc + "\n"
                elif '정답' in class_name:
                    answer_text = info.get('class_info_list', [{}])[0].get('text_description', '')
                elif '해설' in class_name:
                    explanation_text = info.get('class_info_list', [{}])[0].get('text_description', '')
            
            return {
                'filename': filename,
                'school': raw_info.get('school', ''),
                'grade': raw_info.get('grade', ''),
                'subject': raw_info.get('subject', ''),
                'difficulty': source_info.get('level_of_difficulty', ''),
                'problem_type': source_info.get('types_of_problems', ''),
                'achievement_standard': source_info.get('2015_achievement_standard', []),
                'problem_text': problem_text.strip(),
                'answer_text': answer_text.strip(),
                'explanation_text': explanation_text.strip(),
                'problem_length': len(problem_text.strip()),
                'has_explanation': bool(explanation_text.strip())
            }
        except Exception as e:
            print(f"데이터 파싱 실패 ({filename}): {e}")
            return None
    
    def filter_data(self) -> List[Dict]:
        """
        수학 문제 필터링
        
        Returns:
            List[Dict]: 필터링된 문제 리스트
        """
        filtered = []
        
        for problem in self.data_items:
            # 학교급 필터
            if problem['school'] not in self.selection_criteria['school_filter']:
                continue
            
            # 텍스트 길이 필터
            if problem['problem_length'] < self.selection_criteria['min_text_length']:
                continue
            if problem['problem_length'] > self.selection_criteria['max_text_length']:
                continue
            
            # 해설이 있는 것만
            if self.selection_criteria['require_explanation'] and not problem['has_explanation']:
                continue
            
            # 난이도 정보가 있는 것만
            if not problem['difficulty'] or problem['difficulty'] not in ['상', '중', '하']:
                continue
            
            filtered.append(problem)
        
        print(f"필터링 후: {len(filtered)}개 문제 남음")
        return filtered
    
    def stratified_sampling(self, filtered_data: List[Dict]) -> List[Dict]:
        """
        수학 문제 계층적 샘플링
        - 주관식/객관식 비율 고려
        - 난이도별 분포 고려
        
        Args:
            filtered_data: 필터링된 문제 리스트
            
        Returns:
            List[Dict]: 선별된 문제 리스트
        """
        target_count = self.selection_criteria['target_count']
        subjective_count = int(target_count * self.selection_criteria['subjective_ratio'])
        objective_count = target_count - subjective_count
        
        # 문제 유형별로 분리
        subjective_problems = [p for p in filtered_data if p['problem_type'] == '주관식']
        objective_problems = [p for p in filtered_data if p['problem_type'] == '객관식']
        
        print(f"주관식: {len(subjective_problems)}개, 객관식: {len(objective_problems)}개")
        
        # 주관식 선별
        selected_subjective = self._sample_by_difficulty(
            subjective_problems, subjective_count
        )
        
        # 객관식 선별
        selected_objective = self._sample_by_difficulty(
            objective_problems, objective_count
        )
        
        selected_problems = selected_subjective + selected_objective
        print(f"최종 선별: {len(selected_problems)}개 문제")
        
        return selected_problems
    
    def _sample_by_difficulty(self, problems: List[Dict], target_count: int) -> List[Dict]:
        """
        난이도별 비율에 따라 샘플링
        
        Args:
            problems: 샘플링할 문제 리스트
            target_count: 목표 선별 개수
            
        Returns:
            List[Dict]: 선별된 문제 리스트
        """
        difficulty_dist = self.selection_criteria['difficulty_distribution']
        selected = []
        
        # 난이도별로 그룹화
        by_difficulty = defaultdict(list)
        for problem in problems:
            by_difficulty[problem['difficulty']].append(problem)
        
        # 난이도별 목표 개수 계산
        for difficulty, ratio in difficulty_dist.items():
            target_for_difficulty = int(target_count * ratio)
            available = by_difficulty[difficulty]
            
            if len(available) >= target_for_difficulty:
                # 무작위 선별
                sampled = random.sample(available, target_for_difficulty)
            else:
                # 사용 가능한 모든 문제 선택
                sampled = available
            
            selected.extend(sampled)
            print(f"  {difficulty}급: {len(sampled)}개 선별")
        
        return selected
    
    def _convert_to_queries(self, selected_data: List[Dict], domain: str) -> List[Dict]:
        """
        수학 문제를 AI 모델 테스트용 쿼리 형태로 변환
        
        Args:
            selected_data: 선별된 문제 리스트
            domain: 도메인 식별자
            
        Returns:
            List[Dict]: 쿼리 형태 데이터
        """
        queries = []
        
        for i, problem in enumerate(selected_data, 1):
            query = {
                'id': f"{domain}_{i:03d}",
                'source_file': problem['filename'],
                'metadata': {
                    'school': problem['school'],
                    'grade': problem['grade'],
                    'difficulty': problem['difficulty'],
                    'problem_type': problem['problem_type'],
                    'achievement_standard': problem['achievement_standard']
                },
                'query_text': problem['problem_text'],
                'reference_answer': problem['answer_text'],
                'reference_explanation': problem['explanation_text']
            }
            queries.append(query)
        
        return queries
    
    def _create_summary(self, queries: List[Dict]) -> Dict:
        """
        수학 문제 선별 요약 통계 생성
        
        Args:
            queries: 쿼리 형태 데이터
            
        Returns:
            Dict: 요약 통계
        """
        return {
            'total_count': len(queries),
            'selection_criteria': self.selection_criteria,
            'distribution': {
                'by_difficulty': dict(Counter(q['metadata']['difficulty'] for q in queries)),
                'by_type': dict(Counter(q['metadata']['problem_type'] for q in queries)),
                'by_school': dict(Counter(q['metadata']['school'] for q in queries)),
                'by_grade': dict(Counter(q['metadata']['grade'] for q in queries))
            }
        }


# 전역 편의 함수
def select_math_problems(target_count: int = 40) -> List[Dict]:
    """
    수학 문제 선별 메인 함수
    
    Args:
        target_count: 목표 선별 개수
        
    Returns:
        List[Dict]: 선별된 문제 리스트
    """
    from src.utils.config import get_config
    
    config = get_config()
    
    # Config에서 경로 가져오기
    data_dir = config.get_data_path('math_problems')
    output_dir = config.get_data_path('selected_data', create_if_missing=True)
    
    # 선별기 초기화 및 실행
    selector = MathProblemSelector(str(data_dir))
    selector.selection_criteria['target_count'] = target_count
    
    selected = selector.select_data()
    
    # 결과 저장
    selector.save_selected_data(selected, str(output_dir), domain='math')
    
    return selected