"""
대시보드용 계절성(Seasonal) 지표 생성 스크립트
====================================================
목적: cleaned_daejeon_metro.csv의 22개 역 각각에 STL(Seasonal-Trend
      decomposition using Loess) 분해를 적용해 계절 성분을 추출하고,
      dashboard/public/data/dashboard_data.json의 각 레코드에
      "seasonal" 필드로 병합한다.
      (대시보드 "계절성" 지표 옵션의 데이터 소스)

배경: 원자료 = 추세 + 계절성 + 잔차(STL 잔차)로 분해했을 때, "계절성"만
      따로 뽑아 "이 역은 몇 월이 평년보다 높고 낮은지"를 보여주기 위함.
      (REPORT.md 4절의 "시계열 분석 기법" 중 이동평균/YoY/시스템 대비
       잔차에 더해, 대시보드 전용으로 추가한 네 번째 기법)

주의: 2025년 1~12월은 원본 데이터에 통째로 누락되어 있다. STL은 결측이
      있으면 계산이 안 되므로, STL 계산용으로만 선형 보간(interpolate)
      해서 채우고, 보간된 2025년 구간의 seasonal 값은 실제 관측이 아니므로
      최종 결과에서 제외한다(대시보드에는 null로 남음).

사용법:
1. python py/clean_data.py 를 먼저 실행해 data/cleaned_daejeon_metro.csv 준비
2. dashboard/public/data/dashboard_data.json 이 이미 존재해야 함
   (STEP: 대시보드 초기 세팅 시 1회 생성된 파일)
3. python py/generate_dashboard_seasonal.py 실행
4. dashboard/public/data/dashboard_data.json 의 각 레코드에 seasonal 필드 추가됨 확인
"""

import json

import pandas as pd
from statsmodels.tsa.seasonal import STL

# ============================================================
# CONFIG
# ============================================================
CLEANED_DATA_PATH = "data/cleaned_daejeon_metro.csv"
DASHBOARD_DATA_PATH = "dashboard/public/data/dashboard_data.json"
STL_PERIOD = 12  # 월별 데이터, 연 단위 계절성


# ============================================================
# 1. 역별 STL 계절 성분 계산
# ============================================================
def compute_seasonal_by_station(cleaned_csv_path: str) -> dict:
    """역별로 STL을 적용해 {(역명, 'YYYY-MM'): 계절성값} 딕셔너리를 반환한다.
    보간으로 채운 2025년 구간은 결과에서 제외한다(실제 관측이 아니므로)."""
    df = pd.read_csv(cleaned_csv_path)
    df["date"] = pd.to_datetime(df["date"])

    seasonal_map = {}
    for station, group in df.groupby("역명"):
        series = group.set_index("date")["total_users"].sort_index()
        series.index = pd.DatetimeIndex(series.index).to_period("M").to_timestamp()
        real_dates = set(series.index)  # 실제 관측된 월(2025년 제외)만 기록

        series_full = series.asfreq("MS").interpolate(method="time")
        stl_result = STL(series_full, period=STL_PERIOD, robust=True).fit()

        for date, value in stl_result.seasonal.items():
            if date in real_dates:
                seasonal_map[(station, date.strftime("%Y-%m"))] = round(float(value), 1)

    print(f"[계산 완료] (역, 월) 쌍 {len(seasonal_map)}개")
    return seasonal_map


# ============================================================
# 2. dashboard_data.json에 seasonal 필드 병합
# ============================================================
def merge_into_dashboard_json(seasonal_map: dict, dashboard_json_path: str) -> None:
    with open(dashboard_json_path, encoding="utf-8") as f:
        data = json.load(f)

    missing = 0
    for record in data["records"]:
        key = (record["station"], record["date"])
        record["seasonal"] = seasonal_map.get(key)
        if record["seasonal"] is None:
            missing += 1

    with open(dashboard_json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    print(f"[병합 완료] 레코드 총 {len(data['records'])}개, seasonal 미매칭 {missing}개(2025년 결측 구간)")
    print(f"[저장 완료] {dashboard_json_path}")


if __name__ == "__main__":
    seasonal_lookup = compute_seasonal_by_station(CLEANED_DATA_PATH)
    merge_into_dashboard_json(seasonal_lookup, DASHBOARD_DATA_PATH)
