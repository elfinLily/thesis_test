"""
수학 교과 문제 데이터 선별 모듈

Author: Ju Eun Cho
Date: 2025-09-28
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict, Counter
import random
import sys

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.utils.config import get_config


class MathProblemSelector:
    """수학 문제 데이터 선별기"""
    
    def __init__(self, data_dir: str):
        """
        초기화
        
        Args:
            data_dir (str): JSON 파일들이 있는 디렉토리 경로
        """
        self.data_dir = Path(data_dir)
        self.problems = []
        self.selection_criteria = {
            'target_count': 40,
            'subjective_ratio': 0.8,  # 주관식 80%
            'difficulty_distribution': {'상': 0.2, '중': 0.5, '하': 0.3},
            'school_filter': ['중학교', '고등학교'],
            'exclude_elementary': True
        }
    
    def load_all_problems(self) -> List[Dict]:
        """
        디렉토리의 모든 JSON 파일을 로드
        
        Returns:
            List[Dict]: 로드된 문제 데이터 리스트
        """
        json_files = list(self.data_dir.glob("*.json"))
        print(f"총 {len(json_files)}개의 JSON 파일 발견")
        
        all_problems = []
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 문제 데이터 구조화
                    problem = self._parse_problem_data(data, json_file.name)
                    if problem:
                        all_problems.append(problem)
            except Exception as e:
                print(f"파일 {json_file} 로드 실패: {e}")
        
        self.problems = all_problems
        print(f"총 {len(all_problems)}개의 문제 로드 완료")
        return all_problems
    
    def _parse_problem_data(self, data: Dict, filename: str) -> Dict:
        """
        JSON 데이터를 구조화된 문제 형태로 파싱
        
        Args:
            data (Dict): 원본 JSON 데이터
            filename (str): 파일명
            
        Returns:
            Dict: 파싱된 문제 데이터
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
    
    def analyze_data_distribution(self) -> Dict:
        """
        데이터 분포 분석
        
        Returns:
            Dict: 분포 분석 결과
        """
        if not self.problems:
            self.load_all_problems()
        
        analysis = {
            'total_count': len(self.problems),
            'by_school': Counter(p['school'] for p in self.problems),
            'by_grade': Counter(p['grade'] for p in self.problems),
            'by_difficulty': Counter(p['difficulty'] for p in self.problems),
            'by_type': Counter(p['problem_type'] for p in self.problems),
            'length_stats': {
                'min': min(p['problem_length'] for p in self.problems),
                'max': max(p['problem_length'] for p in self.problems),
                'avg': np.mean([p['problem_length'] for p in self.problems])
            }
        }
        
        return analysis
    
    def filter_problems(self) -> List[Dict]:
        """
        기본 필터링 적용
        
        Returns:
            List[Dict]: 필터링된 문제 리스트
        """
        filtered = []
        
        for problem in self.problems:
            # 학교급 필터
            if problem['school'] not in self.selection_criteria['school_filter']:
                continue
            
            # 텍스트 길이 필터 (너무 짧거나 긴 것 제외)
            if problem['problem_length'] < 20 or problem['problem_length'] > 800:
                continue
            
            # 해설이 있는 것만
            if not problem['has_explanation']:
                continue
            
            # 난이도 정보가 있는 것만
            if not problem['difficulty'] or problem['difficulty'] not in ['상', '중', '하']:
                continue
            
            filtered.append(problem)
        
        print(f"필터링 후: {len(filtered)}개 문제 남음")
        return filtered
    
    def stratified_sampling(self, filtered_problems: List[Dict]) -> List[Dict]:
        """
        계층적 샘플링으로 문제 선별
        
        Args:
            filtered_problems (List[Dict]): 필터링된 문제 리스트
            
        Returns:
            List[Dict]: 선별된 문제 리스트
        """
        target_count = self.selection_criteria['target_count']
        subjective_count = int(target_count * self.selection_criteria['subjective_ratio'])
        objective_count = target_count - subjective_count
        
        # 문제 유형별로 분리
        subjective_problems = [p for p in filtered_problems if p['problem_type'] == '주관식']
        objective_problems = [p for p in filtered_problems if p['problem_type'] == '객관식']
        
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
            problems (List[Dict]): 샘플링할 문제 리스트
            target_count (int): 목표 선별 개수
            
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
    
    def select_problems(self) -> List[Dict]:
        """
        전체 선별 프로세스 실행
        
        Returns:
            List[Dict]: 최종 선별된 문제 리스트
        """
        print("=== 수학 문제 선별 시작 ===")
        
        # 1. 데이터 로드
        if not self.problems:
            self.load_all_problems()
        
        # 2. 분포 분석
        analysis = self.analyze_data_distribution()
        print(f"\n데이터 분포 분석:")
        print(f"  전체: {analysis['total_count']}개")
        print(f"  학교별: {dict(analysis['by_school'])}")
        print(f"  난이도별: {dict(analysis['by_difficulty'])}")
        print(f"  유형별: {dict(analysis['by_type'])}")
        
        # 3. 필터링
        filtered = self.filter_problems()
        
        # 4. 계층적 샘플링
        selected = self.stratified_sampling(filtered)
        
        print("=== 선별 완료 ===")
        return selected
    
    def save_selected_problems(self, selected_problems: List[Dict], output_dir: str, domain: str = 'math'):
        """
        선별된 문제를 파일로 저장
        
        Args:
            selected_problems (List[Dict]): 선별된 문제 리스트
            output_path (str): 저장할 파일 경로
            domain: 도메인 ('math', 'legal', 'general')
        """
        from src.utils.config import get_filename
        filename = get_filename(f'selected_{domain}')
        summary_filename = get_filename(f'selected_{domain}_summary')

        output_path = Path(output_dir) / filename
        summary_path = Path(output_dir) / summary_filename

        # AI 모델 테스트용 쿼리 형태로 변환
        queries = []
        
        for i, problem in enumerate(selected_problems, 1):
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
        
        # JSON 파일로 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(queries, f, ensure_ascii=False, indent=2)
        
        print(f"선별된 {len(queries)}개 문제를 {output_path}에 저장 완료")
        
        # 요약 통계도 함께 저장
        summary_path = output_path.replace('.json', '_summary.json')
        summary = {
            'total_count': len(queries),
            'selection_criteria': self.selection_criteria,
            'distribution': {
                'by_difficulty': Counter(q['metadata']['difficulty'] for q in queries),
                'by_type': Counter(q['metadata']['problem_type'] for q in queries),
                'by_school': Counter(q['metadata']['school'] for q in queries)
            }
        }
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"선별 요약을 {summary_path}에 저장 완료")


# 전역 함수들
def select_math_problems(target_count: int = 40) -> List[Dict]:
    """
    수학 문제 선별 메인 함수
    
    Args:
        data_dir (str): 원본 데이터 디렉토리
        output_dir (str): 결과 저장 디렉토리
        target_count (int): 목표 선별 개수
        
    Returns:
        List[Dict]: 선별된 문제 리스트
    """

    config = get_config()
    data_dir = config.get_data_path('math_problems')
    output_dir = config.get_data_path('selected_data', create_if_missing=True)

    selector = MathProblemSelector(str(data_dir))
    selector.selection_criteria['target_count'] = target_count
    
    selected = selector.select_problems()
    
    # 결과 저장
    selector.save_selected_problems(selected, str(output_dir), domain='math')
    
    return selected


if __name__ == "__main__":
    selected_problems = select_math_problems()
    print(f"선별 완료: {len(selected_problems)}개 문제")