"""
실험 1: 수학 문제 데이터 선별
AI Hub 수학 교과 문제 풀이과정 데이터에서 논문용 쿼리 선별

Author: Ju Eun Cho
Date: 2025-09-28
"""

import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.data_processing.selector import MathProblemSelector, select_math_problems
from src.utils.config import get_config
import json


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("실험 1: 수학 문제 데이터 선별")
    print("=" * 60)
    
    # Config에서 경로 가져오기
    config_manager = get_config()
    data_dir = config_manager.get_data_path('math_problems')
    output_dir = config_manager.get_data_path('selected_data', create_if_missing=True)
    
    # 입력 데이터 확인
    if not data_dir.exists():
        print(f"❌ 데이터 디렉토리가 존재하지 않습니다: {data_dir}")
        print("📁 AI Hub에서 다운로드한 JSON 파일들을 다음 경로에 저장해주세요:")
        print(f"   {data_dir}")
        return
    
    json_files = list(data_dir.glob("*.json"))
    print(f"📂 입력 데이터 경로: {data_dir}")
    print(f"📄 JSON 파일 개수: {len(json_files)}")
    
    if len(json_files) == 0:
        print("❌ JSON 파일이 없습니다!")
        return
    
    # 선별 설정
    config = {
        'target_count': 40,
        'subjective_ratio': 0.8,  # 주관식 80%
        'objective_ratio': 0.2,   # 객관식 20%
        'difficulty_distribution': {
            '상': 0.2,  # 고난이도 20%
            '중': 0.5,  # 중난이도 50%
            '하': 0.3   # 저난이도 30%
        }
    }
    
    print(f"\n📋 선별 설정:")
    print(f"   목표 개수: {config['target_count']}개")
    print(f"   주관식 비율: {config['subjective_ratio']*100}%")
    print(f"   객관식 비율: {config['objective_ratio']*100}%")
    print(f"   난이도 분포: {config['difficulty_distribution']}")
    
    try:
        # 선별 실행 (Config 기반 경로 자동 사용)
        print(f"\n🚀 선별 시작...")
        select_math_problems(target_count=config['target_count'])
        
        # 결과 확인
        output_file = config_manager.get_data_path('selected_math')
        summary_file = output_file.with_name('selected_math_problems_summary.json')
        
        if output_file.exists():
            print(f"\n✅ 선별 완료!")
            print(f"📄 선별된 문제: {output_file}")
            print(f"📊 선별 요약: {summary_file}")
            
            # 요약 정보 출력
            with open(summary_file, 'r', encoding='utf-8') as f:
                summary = json.load(f)
            
            print(f"\n📈 최종 결과:")
            print(f"   총 개수: {summary['total_count']}개")
            print(f"   난이도별 분포: {dict(summary['distribution']['by_difficulty'])}")
            print(f"   유형별 분포: {dict(summary['distribution']['by_type'])}")
            print(f"   학교별 분포: {dict(summary['distribution']['by_school'])}")
            
            # 샘플 문제 미리보기
            with open(output_file, 'r', encoding='utf-8') as f:
                problems = json.load(f)
            
            print(f"\n👀 선별된 문제 미리보기 (처음 3개):")
            for i, problem in enumerate(problems[:3], 1):
                print(f"\n--- 문제 {i} ---")
                print(f"ID: {problem['id']}")
                print(f"유형: {problem['metadata']['problem_type']} "
                      f"| 난이도: {problem['metadata']['difficulty']} "
                      f"| 학교: {problem['metadata']['school']} {problem['metadata']['grade']}")
                print(f"문제: {problem['query_text'][:100]}...")
                
        else:
            print("❌ 선별 파일이 생성되지 않았습니다.")
            
    except Exception as e:
        print(f"❌ 선별 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


def validate_selection():
    """선별 결과 검증 함수"""
    print("\n🔍 선별 결과 검증 중...")

    from src.utils.config import get_filename
    
    config_manager = get_config()
    output_dir = config_manager.get_data_path('selected_data')
    output_file = output_dir / get_filename('selected_math')
    
    if not output_file.exists():
        print("❌ 선별 파일이 없습니다. 먼저 선별을 실행하세요.")
        return False
    
    with open(output_file, 'r', encoding='utf-8') as f:
        problems = json.load(f)
    
    # 검증 항목들
    validation_results = {}
    
    # 1. 개수 확인
    validation_results['count_check'] = len(problems) >= 30  # 최소 30개
    
    # 2. 필수 필드 확인
    required_fields = ['id', 'query_text', 'metadata']
    field_check = all(
        all(field in problem for field in required_fields) 
        for problem in problems
    )
    validation_results['field_check'] = field_check
    
    # 3. 텍스트 길이 확인
    text_lengths = [len(p['query_text']) for p in problems]
    validation_results['text_length_check'] = all(length > 20 for length in text_lengths)
    
    # 4. 다양성 확인
    difficulties = [p['metadata']['difficulty'] for p in problems]
    types = [p['metadata']['problem_type'] for p in problems]
    
    validation_results['diversity_check'] = (
        len(set(difficulties)) >= 2 and  # 최소 2개 난이도
        len(set(types)) >= 1              # 최소 1개 유형
    )
    
    # 결과 출력
    print(f"✅ 개수 확인: {validation_results['count_check']} ({len(problems)}개)")
    print(f"✅ 필드 확인: {validation_results['field_check']}")
    print(f"✅ 텍스트 길이: {validation_results['text_length_check']} (평균: {sum(text_lengths)/len(text_lengths):.1f}자)")
    print(f"✅ 다양성 확인: {validation_results['diversity_check']}")
    
    all_passed = all(validation_results.values())
    print(f"\n🎯 전체 검증 결과: {'통과' if all_passed else '실패'}")
    
    return all_passed


if __name__ == "__main__":
    # 메인 실행
    main()
    
    # 검증 실행
    print("\n" + "=" * 60)
    validate_selection()
    print("=" * 60)