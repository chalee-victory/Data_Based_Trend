"""
대전도시철도 역별 월별 승하차 데이터 정제 스크립트
====================================================
목적: 원본 CSV를 불러와 형식 오류를 점검하고, 파생변수(이동평균/증감률)를
      생성한 뒤, 통계적 이상치(코로나19 등)를 탐지하여 정제된 CSV로 저장한다.

사용법:
1. 아래 CONFIG 부분의 파일 경로/컬럼명을 실제 다운받은 CSV에 맞게 수정
2. python clean_data.py 실행
3. data/cleaned_daejeon_metro.csv 생성 확인
"""

import pandas as pd
import numpy as np

# ============================================================
# CONFIG — 실제 다운받은 CSV 구조에 맞게 이 부분만 수정하세요
# ============================================================
RAW_FILE_PATH = "data/raw_daejeon_metro_merged.csv"   # merge_data.py 실행 결과 파일
ENCODING = "utf-8-sig"                          # merge_data.py가 utf-8-sig로 저장하므로 이에 맞춤

COL_STATION = "역명"       # 역명 컬럼
COL_YEAR = "년도"          # 연도 컬럼 (없으면 아래 코드에서 자동 처리)
COL_MONTH = "월"           # 월 컬럼
COL_BOARD = "승차인원"      # 승차인원 컬럼
COL_ALIGHT = "하차인원"     # 하차인원 컬럼

TARGET_STATIONS = ["정부청사", "시청", "갈마", "탄방"]   # 둔산 인접 역 (실제 역명 - "역" 자 없음)
COMPARE_STATIONS = ["유성온천", "노은"]                    # 비교 대상 역

OUTPUT_PATH = "data/cleaned_daejeon_metro.csv"

# ============================================================
# 1. 데이터 로드
# ============================================================
def load_data(path, encoding):
    try:
        df = pd.read_csv(path, encoding=encoding)
    except UnicodeDecodeError:
        print(f"[알림] {encoding} 로드 실패, utf-8로 재시도")
        df = pd.read_csv(path, encoding="utf-8")
    print(f"[로드 완료] {len(df)}행, 컬럼: {list(df.columns)}")
    return df


# ============================================================
# 2. 형식 오류 점검 및 수정
# ============================================================
def check_and_fix_format(df):
    issues = []

    # 2-1. 콤마 포함 숫자 문자열 처리 (예: "12,345" -> 12345)
    # 주의: pandas 버전에 따라 문자열 컬럼이 object가 아니라 string(StringDtype)으로
    #      읽힐 수 있으므로, dtype == object 대신 is_numeric_dtype으로 판단한다.
    for col in [COL_BOARD, COL_ALIGHT]:
        if not pd.api.types.is_numeric_dtype(df[col]):
            issues.append(f"{col}: 비숫자 타입({df[col].dtype}) 발견 -> 콤마 제거 후 숫자 변환")
            df[col] = (
                df[col].astype(str).str.replace(",", "", regex=False).str.strip()
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 2-2. 합계/소계/전체 등 요약행 제거
    summary_keywords = ["합계", "소계", "전체", "총계"]
    mask_summary = df[COL_STATION].astype(str).str.contains(
        "|".join(summary_keywords), na=False
    )
    if mask_summary.sum() > 0:
        issues.append(f"요약행 {mask_summary.sum()}건 발견 -> 제거")
        df = df[~mask_summary].copy()

    # 2-3. 역명 공백/표기 통일 (앞뒤 공백 제거)
    before_unique = df[COL_STATION].nunique()
    df[COL_STATION] = df[COL_STATION].astype(str).str.strip()
    after_unique = df[COL_STATION].nunique()
    if before_unique != after_unique:
        issues.append(f"역명 공백 정리로 고유값 {before_unique}->{after_unique}개 통합")

    # 2-4. 연월 컬럼을 datetime으로 변환
    if COL_YEAR in df.columns and COL_MONTH in df.columns:
        df["date"] = pd.to_datetime(
            df[COL_YEAR].astype(str) + "-" + df[COL_MONTH].astype(str).str.zfill(2) + "-01"
        )
    else:
        raise ValueError("연/월 컬럼명을 CONFIG에서 다시 확인하세요.")

    print("\n[형식 점검 결과]")
    if issues:
        for i in issues:
            print(" -", i)
    else:
        print(" - 특이사항 없음 (원본 형식이 이미 정상)")

    return df


# ============================================================
# 3. 결측치 점검
# ============================================================
def check_missing(df):
    missing = df[[COL_BOARD, COL_ALIGHT]].isna().sum()
    print("\n[결측치 점검 — 값 자체가 NaN인 경우]")
    print(missing)

    # 연도별로 실제 존재하는 월(1~12)을 확인하여, 특정 연도에 통째로 빠진 달이 있는지 점검
    # (컬럼 자체가 원본에 없던 경우, 병합 후 해당 연-월 행이 아예 생성되지 않으므로
    #  이 방식으로만 정확히 잡아낼 수 있음)
    print("\n[연도별 데이터 커버리지 점검 — 통째로 빠진 달 확인]")
    full_months = set(range(1, 13))
    gap_report = {}
    for year, group in df.groupby("년도"):
        present_months = set(group["월"].unique())
        missing_months = sorted(full_months - present_months)
        status = "정상(12개월 전체)" if not missing_months else f"결측 {missing_months}"
        print(f"  {year}년: {status}")
        if missing_months:
            gap_report[year] = missing_months

    if gap_report:
        print(f"\n -> 결측 연도 발견: {gap_report}")
        print("    이런 다개월 연속 결측은 선형보간으로 메우기엔 구간이 너무 길어 왜곡 위험이 큼.")
        print("    -> 보간하지 않고 '자료 없음' 구간으로 명시적으로 라벨링할 것을 권장.")
        df["is_data_gap"] = df.apply(
            lambda r: r["월"] in gap_report.get(r["년도"], []), axis=1
        )
    else:
        df["is_data_gap"] = False

    return df


# ============================================================
# 4. 파생변수 생성 (정제의 핵심 — 원본엔 없던 분석용 컬럼 추가)
# ============================================================
def add_derived_columns(df):
    df = df.sort_values([COL_STATION, "date"]).reset_index(drop=True)

    # 총 이용객수
    df["total_users"] = df[COL_BOARD] + df[COL_ALIGHT]

    # 전월 대비 증감률 (MoM)
    df["mom_change_pct"] = df.groupby(COL_STATION)["total_users"].pct_change() * 100

    # 전년 동월 대비 증감률 (YoY) — 계절성 통제
    df["yoy_change_pct"] = df.groupby(COL_STATION)["total_users"].pct_change(12) * 100

    # 3개월 이동평균 (단기 흐름)
    df["ma_3m"] = df.groupby(COL_STATION)["total_users"].transform(
        lambda x: x.rolling(3, min_periods=1).mean()
    )

    # 12개월 이동평균 (장기 추세, 계절성 제거)
    df["ma_12m"] = df.groupby(COL_STATION)["total_users"].transform(
        lambda x: x.rolling(12, min_periods=1).mean()
    )

    print("\n[파생변수 생성 완료] total_users, mom_change_pct, yoy_change_pct, ma_3m, ma_12m")
    return df


# ============================================================
# 5. 통계적 이상치 탐지 (12개월 이동평균 대비 ±2표준편차)
# ============================================================
def detect_outliers(df):
    # 주의: groupby().apply()로 전체 그룹을 반환하면 pandas 버전에 따라
    #      그룹 기준 컬럼(역명)이 결과에서 빠지는 경우가 있어, transform으로 처리한다.
    grouped = df.groupby(COL_STATION)["total_users"]
    rolling_mean = grouped.transform(lambda x: x.rolling(12, min_periods=3).mean())
    rolling_std = grouped.transform(lambda x: x.rolling(12, min_periods=3).std())
    df["is_outlier"] = (df["total_users"] > rolling_mean + 2 * rolling_std) | (
        df["total_users"] < rolling_mean - 2 * rolling_std
    )

    outlier_count = df["is_outlier"].sum()
    print(f"\n[이상치 탐지] 총 {outlier_count}건 발견 (±2표준편차 기준)")
    if outlier_count > 0:
        print(df[df["is_outlier"]][[COL_STATION, "date", "total_users"]].to_string(index=False))
        print("\n-> 위 시점들이 실제 사건(코로나19, 공사 등)과 겹치는지 직접 확인 후")
        print("   리포트의 'AI 사용 로그 > 검증 방법'에 확인 과정을 기록하세요.")

    # 코로나19 기간(2020-02 ~ 2022-04) 별도 라벨링 — 필요시 기간 수정
    covid_start, covid_end = pd.Timestamp("2020-02-01"), pd.Timestamp("2022-04-30")
    df["period_label"] = np.where(
        (df["date"] >= covid_start) & (df["date"] <= covid_end), "팬데믹 구간", "일반 구간"
    )

    return df


# ============================================================
# 실행
# ============================================================
if __name__ == "__main__":
    df = load_data(RAW_FILE_PATH, ENCODING)
    df = check_and_fix_format(df)
    df = check_missing(df)
    df = add_derived_columns(df)
    df = detect_outliers(df)

    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    print(f"\n[완료] 정제된 데이터 저장: {OUTPUT_PATH}")
    print(f"최종 행수: {len(df)}, 컬럼: {list(df.columns)}")
