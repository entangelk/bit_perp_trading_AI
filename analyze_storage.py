#!/usr/bin/env python3
"""
MongoDB 저장소 분석 스크립트
- 현재 데이터 사용량 조사
- 각 컬렉션별 증가율 분석
- TTL 인덱스 상태 확인
- 저장소 최적화 제안
"""

import asyncio
import json
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient
from typing import Dict, List, Any
import os
import sys

# 로깅 설정
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StorageAnalyzer:
    def __init__(self):
        self.client = MongoClient("mongodb://mongodb:27017")
        self.db = self.client["bitcoin"]
        
    def get_database_stats(self) -> Dict:
        """데이터베이스 전체 통계"""
        try:
            stats = self.db.command("dbStats")
            return {
                "database_size_mb": round(stats.get("dataSize", 0) / (1024 * 1024), 2),
                "storage_size_mb": round(stats.get("storageSize", 0) / (1024 * 1024), 2),
                "index_size_mb": round(stats.get("indexSize", 0) / (1024 * 1024), 2),
                "total_collections": stats.get("collections", 0),
                "total_objects": stats.get("objects", 0),
                "avg_object_size": round(stats.get("avgObjSize", 0), 2)
            }
        except Exception as e:
            logger.error(f"데이터베이스 통계 조회 실패: {e}")
            return {}
    
    def get_collection_stats(self) -> List[Dict]:
        """각 컬렉션별 상세 통계"""
        collections_info = []
        
        try:
            collection_names = self.db.list_collection_names()
            
            for collection_name in collection_names:
                try:
                    collection = self.db[collection_name]
                    stats = self.db.command("collStats", collection_name)
                    
                    # 문서 수
                    count = collection.count_documents({})
                    
                    # 최근 문서 시간 (created_at 또는 timestamp 필드가 있는 경우)
                    latest_doc = None
                    oldest_doc = None
                    
                    try:
                        # created_at 필드로 시도
                        latest_doc = collection.find_one({}, sort=[("created_at", -1)])
                        oldest_doc = collection.find_one({}, sort=[("created_at", 1)])
                        
                        if not latest_doc:
                            # timestamp 필드로 시도
                            latest_doc = collection.find_one({}, sort=[("timestamp", -1)])
                            oldest_doc = collection.find_one({}, sort=[("timestamp", 1)])
                    except:
                        pass
                    
                    # 인덱스 정보
                    indexes = list(collection.list_indexes())
                    ttl_indexes = []
                    for idx in indexes:
                        if 'expireAfterSeconds' in idx:
                            ttl_indexes.append({
                                'name': idx['name'],
                                'field': list(idx['key'].keys())[0],
                                'ttl_seconds': idx['expireAfterSeconds']
                            })
                    
                    collection_info = {
                        "name": collection_name,
                        "document_count": count,
                        "size_mb": round(stats.get("size", 0) / (1024 * 1024), 2),
                        "storage_size_mb": round(stats.get("storageSize", 0) / (1024 * 1024), 2),
                        "avg_object_size": round(stats.get("avgObjSize", 0), 2),
                        "total_indexes": stats.get("nindexes", 0),
                        "index_size_mb": round(stats.get("totalIndexSize", 0) / (1024 * 1024), 2),
                        "ttl_indexes": ttl_indexes,
                        "latest_document": latest_doc.get('created_at') or latest_doc.get('timestamp') if latest_doc else None,
                        "oldest_document": oldest_doc.get('created_at') or oldest_doc.get('timestamp') if oldest_doc else None
                    }
                    
                    collections_info.append(collection_info)
                    
                except Exception as e:
                    logger.warning(f"컬렉션 {collection_name} 통계 조회 실패: {e}")
                    collections_info.append({
                        "name": collection_name,
                        "error": str(e)
                    })
            
            # 크기순으로 정렬
            collections_info.sort(key=lambda x: x.get("size_mb", 0), reverse=True)
            return collections_info
            
        except Exception as e:
            logger.error(f"컬렉션 목록 조회 실패: {e}")
            return []
    
    def analyze_growth_pattern(self) -> Dict:
        """데이터 증가 패턴 분석"""
        growth_analysis = {}
        
        try:
            # 주요 데이터 컬렉션들의 증가 패턴 분석
            target_collections = [
                "data_cache",       # AI 분석 결과 캐시
                "chart_15m",        # 15분 차트 데이터
                "chart_5m",         # 5분 차트 데이터 (사용 안함)
                "trades",           # 거래 기록
                "positions",        # 포지션 정보
                "logs"              # 로그 데이터
            ]
            
            for collection_name in target_collections:
                if collection_name in self.db.list_collection_names():
                    collection = self.db[collection_name]
                    
                    # 최근 7일간 문서 수 분석
                    now = datetime.now(timezone.utc)
                    daily_counts = []
                    
                    for i in range(7):
                        day_start = now - timedelta(days=i+1)
                        day_end = now - timedelta(days=i)
                        
                        try:
                            day_count = collection.count_documents({
                                "created_at": {
                                    "$gte": day_start,
                                    "$lt": day_end
                                }
                            })
                        except:
                            # created_at이 없으면 timestamp로 시도
                            try:
                                day_count = collection.count_documents({
                                    "timestamp": {
                                        "$gte": day_start.timestamp(),
                                        "$lt": day_end.timestamp()
                                    }
                                })
                            except:
                                day_count = 0
                        
                        daily_counts.append({
                            "date": day_start.strftime("%Y-%m-%d"),
                            "count": day_count
                        })
                    
                    # 일평균 증가량 계산
                    total_docs = sum(day["count"] for day in daily_counts)
                    avg_daily_growth = total_docs / 7 if total_docs > 0 else 0
                    
                    growth_analysis[collection_name] = {
                        "daily_counts": daily_counts,
                        "avg_daily_growth": round(avg_daily_growth, 1),
                        "estimated_monthly_growth": round(avg_daily_growth * 30, 1),
                        "total_last_week": total_docs
                    }
        
        except Exception as e:
            logger.error(f"증가 패턴 분석 실패: {e}")
        
        return growth_analysis
    
    def check_ttl_effectiveness(self) -> Dict:
        """TTL 인덱스 효과 분석"""
        ttl_analysis = {}
        
        try:
            collection_names = self.db.list_collection_names()
            
            for collection_name in collection_names:
                collection = self.db[collection_name]
                indexes = list(collection.list_indexes())
                
                for idx in indexes:
                    if 'expireAfterSeconds' in idx:
                        field_name = list(idx['key'].keys())[0]
                        ttl_seconds = idx['expireAfterSeconds']
                        
                        # TTL 만료 예정 문서 수 확인
                        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=ttl_seconds)
                        
                        try:
                            expired_count = collection.count_documents({
                                field_name: {"$lt": cutoff_time}
                            })
                        except:
                            expired_count = 0
                        
                        total_count = collection.count_documents({})
                        
                        ttl_analysis[f"{collection_name}.{field_name}"] = {
                            "collection": collection_name,
                            "field": field_name,
                            "ttl_hours": round(ttl_seconds / 3600, 1),
                            "total_documents": total_count,
                            "expired_documents": expired_count,
                            "retention_rate": round((total_count - expired_count) / max(1, total_count) * 100, 1)
                        }
        
        except Exception as e:
            logger.error(f"TTL 효과 분석 실패: {e}")
        
        return ttl_analysis
    
    def get_storage_recommendations(self, db_stats: Dict, collections: List[Dict], growth: Dict) -> List[str]:
        """저장소 최적화 제안"""
        recommendations = []
        
        # 1. 전체 데이터베이스 크기 기준
        total_size_mb = db_stats.get("database_size_mb", 0)
        if total_size_mb > 1000:  # 1GB 이상
            recommendations.append(f"🚨 데이터베이스 크기가 {total_size_mb}MB로 큼 - 정리 필요")
        elif total_size_mb > 500:  # 500MB 이상
            recommendations.append(f"⚠️ 데이터베이스 크기 {total_size_mb}MB - 모니터링 필요")
        
        # 2. 큰 컬렉션 확인
        for col in collections[:3]:  # 상위 3개 컬렉션
            if col.get("size_mb", 0) > 100:
                recommendations.append(f"📊 대용량 컬렉션 '{col['name']}': {col['size_mb']}MB - 최적화 검토")
        
        # 3. TTL 인덱스 누락 확인
        cache_collections = ["data_cache", "chart_15m", "chart_5m"]
        for col in collections:
            if col["name"] in cache_collections and not col.get("ttl_indexes"):
                recommendations.append(f"⏰ '{col['name']}' 컬렉션에 TTL 인덱스 추가 권장")
        
        # 4. 급속한 증가 패턴 감지
        for col_name, growth_data in growth.items():
            monthly_growth = growth_data.get("estimated_monthly_growth", 0)
            if monthly_growth > 10000:  # 월 1만개 이상 증가
                recommendations.append(f"📈 '{col_name}' 컬렉션 급증 - 월 {monthly_growth}개 문서 예상")
        
        # 5. 인덱스 크기 확인
        for col in collections:
            if col.get("index_size_mb", 0) > col.get("size_mb", 0) * 0.5:
                recommendations.append(f"🔍 '{col['name']}' 인덱스 크기 과다 - 최적화 필요")
        
        return recommendations
    
    def generate_report(self) -> Dict:
        """종합 저장소 분석 리포트 생성"""
        logger.info("MongoDB 저장소 분석 시작...")
        
        # 데이터 수집
        db_stats = self.get_database_stats()
        collections = self.get_collection_stats()
        growth_patterns = self.analyze_growth_pattern()
        ttl_analysis = self.check_ttl_effectiveness()
        recommendations = self.get_storage_recommendations(db_stats, collections, growth_patterns)
        
        # 리포트 생성
        report = {
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            "database_overview": db_stats,
            "collections_analysis": collections,
            "growth_patterns": growth_patterns,
            "ttl_effectiveness": ttl_analysis,
            "recommendations": recommendations,
            "summary": {
                "total_collections": len(collections),
                "largest_collection": collections[0]["name"] if collections else None,
                "largest_collection_size_mb": collections[0].get("size_mb", 0) if collections else 0,
                "collections_with_ttl": len([c for c in collections if c.get("ttl_indexes")]),
                "high_growth_collections": len([k for k, v in growth_patterns.items() 
                                               if v.get("estimated_monthly_growth", 0) > 5000])
            }
        }
        
        logger.info("MongoDB 저장소 분석 완료")
        return report

def main():
    """메인 실행 함수"""
    try:
        analyzer = StorageAnalyzer()
        report = analyzer.generate_report()
        
        # 결과 출력
        print("\n" + "="*80)
        print("📊 MONGODB 저장소 분석 리포트")
        print("="*80)
        
        # 데이터베이스 개요
        db_stats = report["database_overview"]
        print(f"\n🗄️  데이터베이스 개요:")
        print(f"   • 전체 크기: {db_stats.get('database_size_mb', 0)}MB")
        print(f"   • 저장 공간: {db_stats.get('storage_size_mb', 0)}MB")
        print(f"   • 인덱스 크기: {db_stats.get('index_size_mb', 0)}MB")
        print(f"   • 총 문서 수: {db_stats.get('total_objects', 0):,}개")
        
        # 주요 컬렉션
        collections = report["collections_analysis"]
        print(f"\n📋 주요 컬렉션 (상위 5개):")
        for i, col in enumerate(collections[:5]):
            if "error" not in col:
                ttl_info = f" (TTL: {len(col.get('ttl_indexes', []))}개)" if col.get('ttl_indexes') else ""
                print(f"   {i+1}. {col['name']}: {col['size_mb']}MB, {col['document_count']:,}개 문서{ttl_info}")
        
        # 증가 패턴
        growth = report["growth_patterns"]
        print(f"\n📈 데이터 증가 패턴 (최근 7일):")
        for col_name, growth_data in growth.items():
            if growth_data.get("avg_daily_growth", 0) > 0:
                print(f"   • {col_name}: 일평균 {growth_data['avg_daily_growth']}개, 월예상 {growth_data['estimated_monthly_growth']}개")
        
        # TTL 인덱스 상태
        ttl_data = report["ttl_effectiveness"]
        if ttl_data:
            print(f"\n⏰ TTL 인덱스 현황:")
            for ttl_name, ttl_info in ttl_data.items():
                print(f"   • {ttl_info['collection']}.{ttl_info['field']}: {ttl_info['ttl_hours']}시간, 보존율 {ttl_info['retention_rate']}%")
        
        # 권장사항
        recommendations = report["recommendations"]
        if recommendations:
            print(f"\n💡 최적화 권장사항:")
            for i, rec in enumerate(recommendations):
                print(f"   {i+1}. {rec}")
        
        # JSON 파일로 저장
        output_file = f"storage_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n💾 상세 리포트가 '{output_file}'에 저장되었습니다.")
        print("="*80)
        
        return report
        
    except Exception as e:
        logger.error(f"저장소 분석 중 오류: {e}")
        return None

if __name__ == "__main__":
    main()