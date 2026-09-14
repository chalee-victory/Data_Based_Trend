# 대전 지하철 22개 역 — 10년간 이용객 변화 트렌드 분석

> Codyssey AI Native Basic Course · 대전코디세이 캠퍼스 · "AI 데이터 분석: 데이터 기반 트렌드 분석" 미션 제출용

## 1. 프로젝트 개요

- **분석 대상**: 대전 도시철도 1호선 22개 역의 월별 승하차 인원 (2015.01 ~ 2026.07, 2025년 데이터는 원본 누락)
- **분석 목적**: 시계열 데이터에서 역별 이용객 증감 패턴을 발견하고, 사양화·부흥 역을 데이터와 실제 지역 뉴스로 대조해 인사이트를 도출한다.
- **진행 상태**: ✅ 완료 — REPORT.md 최종본 + 보너스 과제(인터랙티브 대시보드 배포)까지 완료
- **대시보드 바로가기**: [data-based-trend.vercel.app](https://data-based-trend.vercel.app)

## 2. 폴더 구조

```
Data_Based_Trend/
├── data/
│   ├── raw/                              # 원본 CSV 11개 (연도별 대전교통공사 역별 수송실적)
│   ├── raw_daejeon_metro_merged.csv      # 11개 CSV 병합 + 가로형→세로형 변환 결과
│   └── cleaned_daejeon_metro.csv         # 정제 + 파생변수(이동평균·증감률·잔차) 포함 최종 분석용 데이터
├── py/
│   ├── merge_data.py                     # 원본 CSV 병합 및 구조 변환
│   ├── clean_data.py                     # 형식 오류 수정, 결측치/이상치 탐지·라벨링, 파생변수 생성
│   └── analyze_and_visualize.py          # 시각화 생성 + 요약 통계 출력
├── images/                               # 시각화 결과 이미지 6장 (01~06)
├── dashboard/                             # 보너스 과제: 인터랙티브 대시보드 (Next.js)
│   ├── app/                              # 페이지 및 전역 스타일
│   ├── lib/insights.ts                   # 필터 조건에 따라 동적으로 계산되는 인사이트 로직
│   └── public/data/dashboard_data.json   # 대시보드용 정적 데이터 (cleaned_daejeon_metro.csv 기반)
├── REPORT.md                             # 분석 리포트 (최종 인사이트 + 보너스 과제 정리)
├── PROGRESS.md                           # 작업 진행상황 로그
├── WORK_ORDER.md                         # 미션 작업지시서
├── requirements.txt                      # 의존성 목록 (분석 코드용 — 대시보드 의존성은 dashboard/package.json 참고)
└── README.md                             # 본 파일
```

## 3. 개발 환경

- Python 3.10 이상
- 주요 라이브러리: `pandas`, `numpy`, `matplotlib` (버전은 `requirements.txt` 참고)

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 4. 실행 방법

원본 데이터부터 최종 시각화까지 아래 순서대로 실행한다.

```bash
python py/merge_data.py               # data/raw/*.csv → data/raw_daejeon_metro_merged.csv
python py/clean_data.py               # → data/cleaned_daejeon_metro.csv (정제 + 파생변수)
python py/analyze_and_visualize.py    # → images/*.png 생성 + 요약 통계 콘솔 출력
```

`REPORT.md`에 실린 이미지 중 `04_all_stations_ranking.png`, `05_all_stations_10yr_lines.png`, `06_six_stations_breakdown.png`는 22개 역 전체 비교·6개 급변 역 상세 분석 과정에서 추가 생성한 보조 시각화이며, 동일한 정제 데이터(`data/cleaned_daejeon_metro.csv`)를 기반으로 한다.

## 5. 대시보드 (보너스 과제)

분석 결과를 기간·역·지표 조건을 바꿔가며 탐색할 수 있는 인터랙티브 대시보드를 별도로 구축·배포했다.

- **배포 URL**: https://data-based-trend.vercel.app
- **기술 스택**: Next.js · TypeScript · Tailwind CSS · shadcn/ui · Recharts
- **로컬 실행**:
  ```bash
  cd dashboard
  npm install
  npm run dev   # localhost:3000
  ```

자세한 기능 설명과 체험 시나리오는 [`REPORT.md`의 "9. 보너스 과제" 섹션](./REPORT.md#9-보너스-과제-대시보드-서비스화)을 참고한다.

## 6. 데이터 출처

- **출처**: 대전교통공사 역별 수송실적 (연도별 CSV, 공공 제공 자료)
- **기간**: 2015년 1월 ~ 2026년 7월 (2025년 데이터는 원본 자료에 통째로 누락되어 있음 — 2024년 12월 다음이 2026년 1월로 바로 이어짐)
- **대상**: 대전 도시철도 1호선 전체 22개 역
- **라이선스 주의사항**: 공공기관 제공 통계 자료로, 원본 CSV는 `data/raw/`에 그대로 포함되어 있다. 재배포 시 대전교통공사의 공공데이터 이용 조건을 따른다.

## 7. 분석 리포트

분석 주제, 질문, 데이터 설명, 시각화, 인사이트(5개), 결론/한계점, AI 사용 로그는 [`REPORT.md`](./REPORT.md)에서 확인할 수 있습니다.

핵심 결론만 요약하면:
- 대전 지하철 22개 역 전체는 2015~2024년 약 −11.7% 축소되었으며, 이는 팬데믹 이전부터 시작된 구조적 흐름이다.
- 처음 가설이었던 "둔산 vs 비교지역" 지역 구도는 데이터로 뒷받침되지 않았고, 역별 격차는 지리적 인접성보다 역 반경 내 실제 사건(대단지 입주, 시설 폐업, 교통 인프라 개선 등)으로 더 잘 설명된다.
- 같은 성격의 사건이라도 개발이 단기간에 집중되면 "계단식 급변"으로, 여러 해에 걸쳐 진행되면 "완만한 다년 추세"로 서로 다르게 나타난다.

---
*Codyssey AI Native Basic Course 제출용*
