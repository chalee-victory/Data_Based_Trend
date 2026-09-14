# 대전 지하철 트렌드 대시보드 — 개발 스펙 (Claude Code용)

미션 보너스 과제: "분석 결과를 간단한 웹 대시보드로 구성해 기간/조건을 바꿔보며 탐색 가능하게 만든다"를 충족하기 위한 스펙입니다. 이 문서를 Claude Code에 그대로 붙여넣고 시작하시면 됩니다.

## 0. 데이터

이 문서와 함께 받은 `dashboard_data.json`을 프로젝트의 `public/data/dashboard_data.json`에 넣고 시작합니다. (2,794개 레코드, 약 730KB — `data/cleaned_daejeon_metro.csv`에서 이미 계산된 지표를 그대로 포함해 export한 것)

```ts
type Record = {
  station: string;       // 역명 (예: "판암")
  stationCode: number;   // 역번호 (1101~1122, 동→서 순서)
  date: string;          // "YYYY-MM"
  boarding: number;      // 승차인원
  alighting: number;     // 하차인원
  total: number;         // 승하차 합계
  ma3: number | null;    // 3개월 이동평균
  ma12: number | null;   // 12개월 이동평균
  momPct: number | null; // 전월대비 증감률
  yoyPct: number | null; // 전년동월대비 증감률
  residual: number | null; // 시스템 공통추세 대비 잔차(%p) — 역 고유 변동
  isOutlier: boolean;    // 이상치 여부(팬데믹 시기 집중)
  isDataGap: boolean;    // 결측 여부(2020.06~12)
  periodLabel: string;   // "일반 구간" | "팬데믹 구간"
};

type DashboardData = {
  generatedAt: string;
  source: string;
  stations: { name: string; code: number }[]; // 22개 역, 역번호순(동→서)
  records: Record[];
};
```

주의: 2025년 전체가 원본 데이터에 없어서 `date`가 "2024-12" 다음 바로 "2026-01"로 이어집니다. 시간축 차트를 그릴 때 이 공백을 실제 시간 간격만큼 띄워서 그려야 합니다(月 단위 카테고리 축이 아니라 실제 date 객체 기반 축 사용 권장).

## 1. 목적 및 원칙

REPORT.md의 결론(시스템 전체 구조적 축소, 지역 구도보다 역 개별 사건이 더 강한 설명 변수, 계단식 급변 vs 완만한 추세의 구분)을 사용자가 직접 필터를 바꿔가며 체험할 수 있게 하는 게 목적입니다. 새로운 분석을 추가하는 게 아니라, **이미 REPORT.md에 있는 결론을 인터랙티브하게 재현**하는 데 집중합니다.

## 2. 화면 구성 (1페이지 대시보드)

### 상단: 요약 카드 4개
- 22개 역 합산 2015→2024 변화율 (−11.7%)
- 22개 역 중 플러스 역 수 (3/22)
- 선택된 역의 현재 표시 지표 최신값
- 선택된 기간 내 최대/최소 변화율

### 좌측 사이드바: 필터
- **역 선택**: 다중 선택 (기본값: 급변 6개 역 — 중앙로·월드컵경기장·판암·대동·갑천·유성온천 미리 체크)
- **기간 슬라이더**: 2015-01 ~ 2026-07 범위, 드래그로 구간 좁히기
- **지표 선택**: 라디오 버튼 — 원자료 / 3개월 이동평균 / 12개월 이동평균 / YoY 증감률 / 시스템 대비 잔차
- **팬데믹 구간 표시 토글**: on/off (회색 음영 표시)
- **축 모드 토글**: "공유 축"(역간 비교) / "역별 자체 축"(small multiples) — 대화에서 이 차이가 결론을 바꿨던 경험을 그대로 반영

### 메인: 선그래프 (Recharts LineChart)
- 선택된 역들을 각각 다른 색으로 표시
- 팬데믹 구간(2020-01~2022-06) 배경 음영(ReferenceArea)
- 축 모드가 "역별 자체 축"이면 Grid로 역마다 작은 차트 분리 렌더링

### 하단: 22개 역 전체 순위 막대그래프
- 2015-16 평균 대비 2023-24 평균 변화율 기준 가로 막대, 내림차순
- 클릭하면 해당 역이 위 필터의 "역 선택"에 추가/제거되는 인터랙션

## 3. 기술 스택

기존 `googlesheet-dashboard-starterkit`과 통일감을 유지하되, 이 프로젝트는 정적 데이터라 인증·API 연동이 필요 없으므로 그 부분은 뺍니다.

- Next.js 16 (App Router), TypeScript 5, React 19
- Tailwind CSS v4, shadcn/ui (Slider, Checkbox, RadioGroup, Card, Toggle 컴포넌트 활용)
- Recharts 3 (LineChart, BarChart, ReferenceArea)
- Lucide React (아이콘)
- 데이터는 `public/data/dashboard_data.json` 정적 파일 fetch — Google Sheets API/NextAuth 불필요

## 4. 배포

- Vercel에 배포 (Next.js 정적 데이터 프로젝트라 별도 서버 설정 불필요)
- 배포 후 URL을 미션 제출 시 "① 배포 URL 1개 제출"로 활용
- GitHub 저장소(`Data_Based_Trend`)와는 별도 저장소로 만들거나, 같은 저장소 내 `dashboard/` 서브폴더 + 별도 Vercel 프로젝트로 연결 (모노레포 방식) — 편하신 쪽으로 선택

## 5. 완료 기준 (제출 체크리스트)

- [ ] 역 다중 선택 필터가 실제로 그래프에 반영됨
- [ ] 기간 슬라이더로 구간을 좁히면 그래프가 갱신됨
- [ ] 5가지 지표(원자료/3개월/12개월/YoY/잔차) 전환이 작동함
- [ ] 팬데믹 구간 음영 토글이 작동함
- [ ] "공유 축 vs 역별 자체 축" 전환이 작동함 (대화에서 발견했던 "12개월 이동평균이 실제 변화를 가렸던 문제"를 사용자가 직접 재현해볼 수 있어야 함)
- [ ] 22개 역 순위 막대그래프에서 역 클릭 시 필터 연동
- [ ] Vercel 배포 URL 확보
