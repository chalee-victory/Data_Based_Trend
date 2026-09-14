"""
대전교통공사_역별 수송실적 — 연도별 CSV 병합 + 세로형(long) 변환 스크립트
================================================================================
원본 구조 (연도별 파일, 가로형/wide):
  연도, 역번호, 역명, 1월 승차, 1월 하차, 2월 승차, 2월 하차, ..., 12월 승차, 12월 하차

목표 구조 (병합 후, 세로형/long — clean_data.py에서 바로 쓸 수 있는 형태):
  역명, 년도, 월, 승차인원, 하차인원

사용법:
1. data/raw/ 폴더에 연도별 원본 CSV 11개를 모두 넣기
   (예: 대전교통공사_역별 수송실적_20151231.csv, ... _20241231.csv)
2. python merge_data.py 실행
3. data/raw_daejeon_metro_merged.csv 생성 확인
   -> 이 파일을 clean_data.py의 RAW_FILE_PATH로 지정해서 다음 단계 진행
"""

import pandas as pd
import glob
import os
import re

RAW_DIR = "data/raw"
OUTPUT_PATH = "data/raw_daejeon_metro_merged.csv"
ENCODING = "cp949"   # 한국 공공기관 엑셀 CSV는 대부분 CP949(EUC-KR). 안되면 "utf-8"로 변경

COL_YEAR = "연도"
COL_STATION_NO = "역번호"
COL_STATION = "역명"

# "1월 승차", "1월 하차", ... "12월 승차", "12월 하차" 패턴 매칭
# 공백 유무(예: "1월승차" vs "1월 승차")에 모두 대응하도록 \s*로 처리
MONTH_COL_PATTERN = re.compile(r"^(\d{1,2})\s*월\s*(승차|하차)$")


def load_one_file(path):
    try:
        df = pd.read_csv(path, encoding=ENCODING)
    except UnicodeDecodeError:
        print(f"  [알림] {ENCODING} 실패, utf-8로 재시도: {os.path.basename(path)}")
        df = pd.read_csv(path, encoding="utf-8")
    return df


def wide_to_long(df, source_file):
    """가로형(월별 승차/하차가 컬럼) -> 세로형(역명/년도/월/승차인원/하차인원) 변환"""
    df = df.rename(columns=lambda c: c.strip())

    if COL_STATION not in df.columns:
        raise ValueError(
            f"[오류] {source_file}: '{COL_STATION}' 컬럼을 찾을 수 없습니다. "
            f"실제 컬럼: {list(df.columns)}"
        )

    if COL_YEAR not in df.columns:
        year_match = re.search(r"(\d{4})\d{4}\.csv$", source_file)
        if not year_match:
            raise ValueError(
                f"[오류] {source_file}: '{COL_YEAR}' 컬럼이 없고 파일명에서 연도를 찾을 수 없습니다."
            )
        df[COL_YEAR] = int(year_match.group(1))
        print(f"  [알림] {source_file}: 파일명에서 연도 {year_match.group(1)} 보완")
    year_values = df[COL_YEAR].astype(str).str.extract(r"(\d{4})", expand=False)
    if year_values.isna().any():
        raise ValueError(f"[오류] {source_file}: 연도 값을 해석할 수 없는 행이 있습니다.")
    df[COL_YEAR] = year_values.astype(int)

    has_station_no = COL_STATION_NO in df.columns
    id_cols = [COL_YEAR, COL_STATION] + ([COL_STATION_NO] if has_station_no else [])

    # 월별 승차/하차 컬럼만 추출 (컬럼명 앞뒤 공백 제거 후 매칭)
    month_cols = [c for c in df.columns if MONTH_COL_PATTERN.match(c)]
    if not month_cols:
        raise ValueError(f"[오류] {source_file}: 월별 승차/하차 컬럼을 찾지 못했습니다.")

    long_df = df.melt(
        id_vars=id_cols, value_vars=month_cols, var_name="raw_col", value_name="인원"
    )

    # "1월 승차" -> 월=1, 구분=승차
    parsed = long_df["raw_col"].str.extract(MONTH_COL_PATTERN)
    long_df["월"] = parsed[0].astype(int)
    long_df["구분"] = parsed[1]

    # 승차/하차를 다시 컬럼으로 피벗 -> (역명, 년도, 월)당 한 행으로 정리
    pivot_index = [COL_YEAR, COL_STATION, "월"] + ([COL_STATION_NO] if has_station_no else [])
    pivot = long_df.pivot_table(
        index=pivot_index, columns="구분", values="인원", aggfunc="first"
    ).reset_index()
    pivot.columns.name = None  # pivot 후 남는 컬럼 인덱스 이름 제거

    pivot = pivot.rename(
        columns={COL_YEAR: "년도", COL_STATION: "역명", "승차": "승차인원", "하차": "하차인원"}
    )
    pivot["_source_file"] = source_file
    return pivot


def merge_all():
    files = sorted(glob.glob(os.path.join(RAW_DIR, "*.csv")))
    if not files:
        print(f"[오류] {RAW_DIR} 폴더에 CSV 파일이 없습니다.")
        return None

    print(f"[발견된 파일 {len(files)}개]")
    all_long = []
    for f in files:
        name = os.path.basename(f)
        df = load_one_file(f)
        print(f" - {name}: 원본 {len(df)}행, 컬럼 {list(df.columns)}")
        long_df = wide_to_long(df, name)
        all_long.append(long_df)

    merged = pd.concat(all_long, ignore_index=True)

    before = len(merged)
    merged = merged.drop_duplicates(subset=["역명", "년도", "월"])
    after = len(merged)
    if before != after:
        print(f"\n[중복 제거] {before - after}건의 중복 (역명/년도/월) 제거됨")

    return merged


if __name__ == "__main__":
    merged = merge_all()
    if merged is not None:
        merged = merged.sort_values(["역명", "년도", "월"]).reset_index(drop=True)
        merged.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
        print(f"\n[병합 완료] 총 {len(merged)}행 -> {OUTPUT_PATH}")
        print(f"최종 컬럼: {list(merged.columns)}")
        print(f"연도 범위: {merged['년도'].min()} ~ {merged['년도'].max()}")
        print(f"역 개수: {merged['역명'].nunique()}개")
        print("\n[미리보기]")
        print(merged.head(10).to_string(index=False))
