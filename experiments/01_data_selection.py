"""
데이터 선별
- 수학 문제 풀이 과정 데이터
- 의료, 법률 전문 서적 말뭉치

"""
import argparse
import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.data_processing import (
    select_math_problems,
    select_legal_medical_documents
)

from src.utils.config import get_config, get_filename
import json


def main():
    """메인 실행 함수 (범용 데이터 선별 스크립트)"""
    
    # 명령줄 인자 파싱
    parser = argparse.ArgumentParser(
        description='AI Hub 데이터 선별 스크립트',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python experiments/01_data_selection.py --dataset math
  python experiments/01_data_selection.py --dataset legal_medical
  python experiments/01_data_selection.py --dataset all
  python experiments/01_data_selection.py --dataset all --count 50
        """
    )
    parser.add_argument(
        '--dataset',
        type=str,
        default='all',
        choices=['math', 'legal_medical', 'all'],
        help='선별할 데이터셋 (기본값: all)'
    )
    parser.add_argument(
        '--count',
        type=int,
        default=40,
        help='데이터셋별 목표 선별 개수 (기본값: 40)'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("실험 1: 데이터 선별")
    print("=" * 60)
    print(f"선별 대상: {args.dataset}")
    print(f"목표 개수: {args.count}개")
    print("=" * 60)
    
    # Config 설정
    config_manager = get_config()
    
    # 수학 데이터 선별
    if args.dataset in ['math', 'all']:
        print("\n" + "=" * 60)
        print("📐 수학 문제 데이터 선별")
        print("=" * 60)
        
        data_dir = config_manager.get_data_path('math_problems')
        
        # 입력 데이터 확인
        if not data_dir.exists():
            print(f"❌ 데이터 디렉토리가 존재하지 않습니다: {data_dir}")
            print("📁 AI Hub에서 다운로드한 JSON 파일들을 다음 경로에 저장해주세요:")
            print(f"   {data_dir}")
        else:
            json_files = list(data_dir.glob("*.json"))
            print(f"📂 입력 데이터 경로: {data_dir}")
            print(f"📄 JSON 파일 개수: {len(json_files)}")
            
            if len(json_files) == 0:
                print("❌ JSON 파일이 없습니다!")
            else:
                try:
                    print(f"\n🚀 선별 시작...")
                    selected_problems = select_math_problems(target_count=args.count)
                    
                    # 결과 확인
                    output_file = config_manager.get_data_path('selected_data') / get_filename('selected_math')
                    summary_file = output_file.with_name(get_filename('selected_math_summary'))
                    
                    if output_file.exists():
                        print(f"\n✅ 수학 데이터 선별 완료!")
                        print(f"📄 선별된 문제: {output_file}")
                        print(f"📊 선별 요약: {summary_file}")
                        
                        # 요약 정보 출력
                        with open(summary_file, 'r', encoding='utf-8') as f:
                            summary = json.load(f)
                        
                        print(f"\n📈 최종 결과:")
                        print(f"   총 개수: {summary['total_count']}개")
                        print(f"   난이도별: {dict(summary['distribution']['by_difficulty'])}")
                        print(f"   유형별: {dict(summary['distribution']['by_type'])}")
                        print(f"   학교별: {dict(summary['distribution']['by_school'])}")
                        
                        # 샘플 미리보기
                        with open(output_file, 'r', encoding='utf-8') as f:
                            problems = json.load(f)
                        
                        print(f"\n👀 선별된 문제 미리보기 (처음 2개):")
                        for i, problem in enumerate(problems[:2], 1):
                            print(f"\n--- 문제 {i} ---")
                            print(f"ID: {problem['id']}")
                            print(f"유형: {problem['metadata']['problem_type']} | "
                                  f"난이도: {problem['metadata']['difficulty']} | "
                                  f"학교: {problem['metadata']['school']} {problem['metadata']['grade']}")
                            print(f"문제: {problem['query_text'][:80]}...")
                    else:
                        print("❌ 선별 파일이 생성되지 않았습니다.")
                        
                except Exception as e:
                    print(f"❌ 수학 데이터 선별 중 오류 발생: {e}")
                    import traceback
                    traceback.print_exc()
    
    # 의료/법률 데이터 선별
    if args.dataset in ['legal_medical', 'all']:
        print("\n" + "=" * 60)
        print("⚖️ 의료/법률 문서 데이터 선별")
        print("=" * 60)
        
        data_dir = config_manager.get_data_path('legal_data')
        
        # 입력 데이터 확인
        if not data_dir.exists():
            print(f"❌ 데이터 디렉토리가 존재하지 않습니다: {data_dir}")
            print("📁 AI Hub에서 다운로드한 JSON 파일들을 다음 경로에 저장해주세요:")
            print(f"   {data_dir}")
        else:
            json_files = list(data_dir.glob("*.json"))
            print(f"📂 입력 데이터 경로: {data_dir}")
            print(f"📄 JSON 파일 개수: {len(json_files)}")
            
            if len(json_files) == 0:
                print("❌ JSON 파일이 없습니다!")
            else:
                try:
                    print(f"\n🚀 선별 시작...")
                    selected_documents = select_legal_medical_documents(target_count=args.count)
                    
                    # 결과 확인
                    output_file = config_manager.get_data_path('selected_data') / get_filename('selected_legal_medical')
                    summary_file = output_file.with_name(get_filename('selected_legal_medical_summary'))
                    
                    if output_file.exists():
                        print(f"\n✅ 의료/법률 데이터 선별 완료!")
                        print(f"📄 선별된 문서: {output_file}")
                        print(f"📊 선별 요약: {summary_file}")
                        
                        # 요약 정보 출력
                        with open(summary_file, 'r', encoding='utf-8') as f:
                            summary = json.load(f)
                        
                        print(f"\n📈 최종 결과:")
                        print(f"   총 개수: {summary['total_count']}개")
                        print(f"   분야별: {dict(summary['distribution']['by_field'])}")
                        print(f"   난이도별: {dict(summary['distribution']['by_difficulty'])}")
                        print(f"   카테고리별 (상위 5개):")
                        category_dist = dict(summary['distribution']['by_category'])
                        top_categories = sorted(category_dist.items(), key=lambda x: x[1], reverse=True)[:5]
                        for cat, count in top_categories:
                            print(f"      {cat}: {count}개")
                        
                        # 샘플 미리보기
                        with open(output_file, 'r', encoding='utf-8') as f:
                            documents = json.load(f)
                        
                        print(f"\n👀 선별된 문서 미리보기 (처음 2개):")
                        for i, doc in enumerate(documents[:2], 1):
                            print(f"\n--- 문서 {i} ---")
                            print(f"ID: {doc['id']}")
                            print(f"분야: {doc['metadata']['field']} | "
                                  f"카테고리: {doc['metadata']['category']} | "
                                  f"난이도: {doc['metadata']['difficulty']}")
                            print(f"내용: {doc['query_text'][:80]}...")
                    else:
                        print("❌ 선별 파일이 생성되지 않았습니다.")
                        
                except Exception as e:
                    print(f"❌ 의료/법률 데이터 선별 중 오류 발생: {e}")
                    import traceback
                    traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✨ 모든 선별 작업 완료!")
    print("=" * 60)

def validate_selection(dataset: str = 'all'):
    """
    선별 결과 검증 함수
    
    Args:
        dataset: 검증할 데이터셋 ('math', 'legal_medical', 'all')
    """
    print("\n🔍 선별 결과 검증 중...")
    
    config_manager = get_config()
    all_passed = True
    
    # 수학 데이터 검증
    if dataset in ['math', 'all']:
        print("\n📐 수학 데이터 검증:")
        output_dir = config_manager.get_data_path('selected_data')
        output_file = output_dir / get_filename('selected_math')
        
        if not output_file.exists():
            print("  ❌ 수학 선별 파일이 없습니다.")
            all_passed = False
        else:
            with open(output_file, 'r', encoding='utf-8') as f:
                problems = json.load(f)
            
            # 검증 항목들
            validation_results = {}
            
            # 1. 개수 확인
            validation_results['count_check'] = len(problems) >= 30
            
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
                len(set(difficulties)) >= 2 and
                len(set(types)) >= 1
            )
            
            # 결과 출력
            print(f"  ✅ 개수 확인: {validation_results['count_check']} ({len(problems)}개)")
            print(f"  ✅ 필드 확인: {validation_results['field_check']}")
            print(f"  ✅ 텍스트 길이: {validation_results['text_length_check']} (평균: {sum(text_lengths)/len(text_lengths):.1f}자)")
            print(f"  ✅ 다양성 확인: {validation_results['diversity_check']}")
            
            if not all(validation_results.values()):
                all_passed = False
    
    # 의료/법률 데이터 검증
    if dataset in ['legal_medical', 'all']:
        print("\n⚖️ 의료/법률 데이터 검증:")
        output_dir = config_manager.get_data_path('selected_data')
        output_file = output_dir / get_filename('selected_legal_medical')
        
        if not output_file.exists():
            print("  ❌ 의료/법률 선별 파일이 없습니다.")
            all_passed = False
        else:
            with open(output_file, 'r', encoding='utf-8') as f:
                documents = json.load(f)
            
            # 검증 항목들
            validation_results = {}
            
            # 1. 개수 확인
            validation_results['count_check'] = len(documents) >= 30
            
            # 2. 필수 필드 확인
            required_fields = ['id', 'query_text', 'metadata']
            field_check = all(
                all(field in doc for field in required_fields) 
                for doc in documents
            )
            validation_results['field_check'] = field_check
            
            # 3. 텍스트 길이 확인
            text_lengths = [len(d['query_text']) for d in documents]
            validation_results['text_length_check'] = all(length > 50 for length in text_lengths)
            
            # 4. 다양성 확인 (분야, 난이도)
            fields = [d['metadata']['field'] for d in documents]
            difficulties = [d['metadata']['difficulty'] for d in documents]
            
            validation_results['diversity_check'] = (
                len(set(fields)) >= 2 and
                len(set(difficulties)) >= 2
            )
            
            # 결과 출력
            print(f"  ✅ 개수 확인: {validation_results['count_check']} ({len(documents)}개)")
            print(f"  ✅ 필드 확인: {validation_results['field_check']}")
            print(f"  ✅ 텍스트 길이: {validation_results['text_length_check']} (평균: {sum(text_lengths)/len(text_lengths):.1f}자)")
            print(f"  ✅ 다양성 확인: {validation_results['diversity_check']}")
            
            if not all(validation_results.values()):
                all_passed = False
    
    print(f"\n🎯 전체 검증 결과: {'✅ 통과' if all_passed else '❌ 실패'}")
    
    return all_passed
if __name__ == "__main__":
    # 메인 실행
    main()
    
    # 검증 실행
    import sys
    dataset_arg = 'all'
    if '--dataset' in sys.argv:
        idx = sys.argv.index('--dataset')
        if idx + 1 < len(sys.argv):
            dataset_arg = sys.argv[idx + 1]
    
    print("\n" + "=" * 60)
    validate_selection(dataset=dataset_arg)
    print("=" * 60)