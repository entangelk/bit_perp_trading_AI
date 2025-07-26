# AI 기반 비트코인 자동 트레이딩 시스템

## 🚀 시스템 개요

이 프로젝트는 AI 분석을 기반으로 한 완전 자동화된 비트코인 선물 거래 시스템입니다. 15분 간격으로 다양한 데이터 소스를 AI가 분석하여 거래 결정을 내리며, 웹 인터페이스를 통해 실시간 모니터링이 가능합니다.

### 🎯 주요 특징
- **AI 기반 분석**: 감정, 기술적, 거시경제, 온체인, 기관투자 데이터 종합 분석
- **완전 자동화**: 15분마다 자동 분석 및 거래 실행
- **스마트 캐싱**: AI API 호출량 72.6% 절약 (672회/일 → 184회/일)
- **자동 복구**: 시스템 오류 시 자동 복구 및 재시도
- **실시간 모니터링**: 웹 인터페이스를 통한 상태 추적
- **리스크 관리**: 신뢰도 기반 거래 실행 및 안전 프로토콜

## 📋 시스템 요구사항

### 하드웨어 요구사항
- **CPU**: 2코어 이상
- **메모리**: 4GB RAM 이상
- **저장공간**: 10GB 이상
- **네트워크**: 안정적인 인터넷 연결

### 소프트웨어 요구사항
- **OS**: Linux (Ubuntu 20.04+ 권장)
- **Python**: 3.8 이상
- **MongoDB**: 4.4 이상
- **Docker**: 20.10 이상 (선택사항)

## 🛠 설치 및 설정

### 1. 저장소 클론
```bash
git clone https://github.com/your-repo/bit_perp_trading_AI.git
cd bit_perp_trading_AI
```

### 2. 환경 변수 설정
```bash
# .env 파일 생성
cat > .env << EOF
BYBIT_ACCESS_KEY=your_bybit_api_key
BYBIT_SECRET_KEY=your_bybit_secret_key
COINGECKO_API_KEY=your_coingecko_api_key
GENAI_API_KEY=your_gemini_ai_key
EOF
```

### 3. Python 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. MongoDB 설정
```bash
# Docker를 사용하는 경우
docker run -d --name mongodb -p 27017:27017 mongo:4.4

# 또는 직접 설치
sudo apt update
sudo apt install mongodb
sudo systemctl start mongodb
sudo systemctl enable mongodb
```

### 5. 초기 데이터 설정
```bash
# 초기 차트 데이터 동기화 (필수)
python -c "from docs.get_chart import chart_update; chart_update('15m', 'BTCUSDT')"
```

## 🎮 사용법

### AI 트레이딩 시스템 실행
```bash
# AI 기반 자동 트레이딩 시작
python main_ai_new.py
```

### 웹 모니터링 인터페이스 실행
```bash
# 웹 인터페이스 시작 (포트 8000)
python log_viewer.py
```

웹 브라우저에서 `http://localhost:8000`에 접속하여 모니터링 가능

### 수동 데이터 수집 실행
```bash
# 데이터 스케줄러 단독 실행
python -c "
import asyncio
from docs.investment_ai.data_scheduler import run_scheduled_data_collection
asyncio.run(run_scheduled_data_collection())
"
```

## 📊 웹 인터페이스 기능

### 1. 메인 대시보드 (`http://localhost:8000`)
- **트레이딩 분석 차트**: 15분 간격 가격 차트 및 거래 신호 표시
- **AI 시스템 상태**: 각 분석기별 에러 카운트 및 활성화 상태
- **서버 상태**: 디스크 사용량, 프로세스 상태
- **거래 실행 로그**: 최근 거래 활동 확인

### 2. 거래 로그 (`http://localhost:8000/log/trading`)
- 실시간 거래 로그 확인
- 에러 로그만 필터링 가능
- 라인 수 조정 (50-1000줄)

### 3. 거래 통계 (`http://localhost:8000/trading-stats`)
- 승률 및 손익 통계
- 거래 성과 분석

## ⚙️ 설정 파일

### 트레이딩 설정 (`main_ai_new.py`)
```python
TRADING_CONFIG = {
    'symbol': 'BTCUSDT',        # 거래 대상
    'leverage': 5,              # 레버리지
    'usdt_amount': 0.3,         # 거래 금액
    'set_timevalue': '15m',     # 분석 주기
    'take_profit': 800,         # 목표 수익 (pips)
    'stop_loss': 800            # 손절 (pips)
}
```

### AI 신뢰도 임계값
- **최소 신뢰도**: 60% (이하 시 거래 안함)
- **인간 검토 필요**: AI가 불확실성 감지 시 거래 중단

## 🔧 고급 설정

### 데이터 수집 주기 조정
```python
# docs/investment_ai/data_scheduler.py에서 수정 가능
COLLECTION_INTERVALS = {
    'sentiment': 30,     # 30분마다 감정 분석
    'technical': 15,     # 15분마다 기술적 분석
    'macro': 360,        # 6시간마다 거시경제 분석
    'onchain': 60,       # 1시간마다 온체인 분석
    'institutional': 120 # 2시간마다 기관투자 분석
}
```

### 에러 복구 설정
```python
# 자동 복구 간격 (기본: 2시간)
RECOVERY_INTERVAL_HOURS = 2

# 최대 에러 카운트 (기본: 3회)
MAX_ERROR_COUNT = 3
```

## 📈 모니터링 및 알림

### 1. 로그 파일 위치
```
logs/
├── trading_bot.log         # 메인 트레이딩 로그
├── snapshots_daily.json    # 거래 신호 기록
└── data_collection.log     # 데이터 수집 로그
```

### 2. 주요 모니터링 지표
- **AI API 사용량**: 일 250회 한도 대비 현재 사용량
- **분석기 상태**: 각 AI 분석기 에러 카운트 (0-3)
- **거래 성과**: 신뢰도별 승률 및 수익률
- **시스템 리소스**: CPU, 메모리, 디스크 사용량

### 3. 경고 신호
- 🔴 **AI 분석기 비활성화**: 3회 연속 실패 시
- 🟡 **API 한도 근접**: 일 사용량 80% 초과 시
- 🟠 **낮은 신뢰도**: 60% 미만 신뢰도 지속 시

## 🚨 문제 해결

### 자주 발생하는 문제

#### 1. API 키 오류
```bash
# 환경 변수 확인
echo $BYBIT_ACCESS_KEY
echo $BYBIT_SECRET_KEY

# API 키 테스트
python -c "
from docs.making_order import get_position_amount
print(get_position_amount('BTCUSDT'))
"
```

#### 2. MongoDB 연결 오류
```bash
# MongoDB 상태 확인
sudo systemctl status mongodb

# 연결 테스트
python -c "
from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017')
print(client.list_database_names())
"
```

#### 3. 차트 데이터 동기화 문제
```bash
# 차트 데이터 재동기화
python -c "
from docs.get_chart import chart_update
chart_update('15m', 'BTCUSDT')
"
```

#### 4. AI 분석기 복구
```bash
# 수동 복구 실행
python -c "
from docs.investment_ai.data_scheduler import force_recovery_all
force_recovery_all()
print('모든 분석기 복구 완료')
"
```

### 로그 확인 방법
```bash
# 실시간 로그 확인
tail -f trading_bot.log

# 에러 로그만 확인
grep "ERROR\\|CRITICAL" trading_bot.log

# AI 관련 로그 확인
grep "AI" trading_bot.log | tail -20
```

## 🔒 보안 고려사항

### 1. API 키 보안
- `.env` 파일 권한: `chmod 600 .env`
- API 키는 절대 코드에 하드코딩하지 않음
- 정기적인 API 키 순환 권장

### 2. 서버 보안
- 방화벽 설정으로 필요한 포트만 개방
- SSH 키 기반 인증 사용
- 정기적인 시스템 업데이트

### 3. 거래 보안
- 자금 관리: 전체 자금의 일부만 사용
- 손실 한도 설정: 일일/월간 손실 한도
- 모니터링: 비정상적인 거래 패턴 감지

## 📚 추가 리소스

### 개발 문서
- [AI 시스템 아키텍처](docs/ai_architecture.md)
- [API 참조](docs/api_reference.md)
- [개발 로그](next_ai_todo.md)

### 외부 문서
- [Bybit API 문서](https://bybit-exchange.github.io/docs/)
- [CoinGecko API](https://www.coingecko.com/en/api)
- [Google Gemini AI](https://ai.google.dev/)

## 🤝 기여하기

1. 이슈 생성 및 토론
2. 포크 후 브랜치 생성
3. 변경사항 커밋
4. 풀 리퀘스트 제출

## ⚠️ 면책 조고

이 소프트웨어는 교육 및 연구 목적으로 제공됩니다. 실제 거래 시 발생하는 손실에 대해 개발자는 책임지지 않습니다. 실제 자금으로 거래하기 전에 충분한 테스트와 검증을 수행하십시오.

## 📞 지원

- **GitHub Issues**: 버그 신고 및 기능 요청
- **Discussions**: 일반적인 질문 및 토론
- **Wiki**: 상세한 사용 가이드 및 팁

---

## 📜 개발 히스토리

### 2024.10 - 2024.12: 기술적 분석 기반 시스템
- MACD, RSI, 슈퍼트렌드 등 기술적 지표 구현
- TradingView 지표와 동기화
- 다양한 거래 전략 테스트 및 최적화

### 2025.01: AI 시스템 전환
- AI 기반 분석 시스템 도입
- API 호출량 최적화 (72.6% 감소)
- 자동 복구 및 안정성 강화
- 웹 인터페이스 완전 개편

현재 시스템은 완전한 AI 기반 자동 트레이딩 시스템으로 진화하였으며, 지속적인 성능 최적화와 고급 기능 추가가 진행 중입니다.