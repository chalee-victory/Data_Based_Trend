"""
둔산 인접 역 vs 비교 지역 역 — 시계열 시각화 스크립트
========================================================
목적: 정제된 데이터를 바탕으로 과제 필수 시각화 3개를 생성한다.
      1) 12개월 이동평균 추이 비교 (둔산 인접 vs 비교 지역)
      2) 연도별 총 이용객 합계 비교 (막대그래프)
      3) 전년 동월 대비 증감률(YoY) 분포 비교 (박스플롯)

사용법: python analyze_and_visualize.py
결과: images/01_trend_ma12.png, images/02_yearly_total.png, images/03_yoy_boxplot.png
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

INPUT_PATH = "data/cleaned_daejeon_metro.csv"
IMG_DIR = "images"

TARGET_STATIONS = ["정부청사", "시청", "갈마", "탄방"]      # 둔산 인접 역
COMPARE_STATIONS = ["유성온천", "노은"]                     # 비교 대상 역 (신흥지역)

os.makedirs(IMG_DIR, exist_ok=True)

# ------------------------------------------------------------
# 한글 폰트 설정 (Windows: 맑은 고딕 / 없으면 시스템 기본)
# ------------------------------------------------------------
def set_korean_font():
    candidates = ["Malgun Gothic", "AppleGothic", "NanumGothic"]
    available = {f.name for f in fm.fontManager.ttflist}
    for c in candidates:
        if c in available:
            plt.rcParams["font.family"] = c
            return
    print("[알림] 한글 폰트를 찾지 못했습니다. 그래프의 한글이 깨질 수 있습니다. "
          "나눔고딕 등 한글 폰트 설치를 권장합니다.")

set_korean_font()
plt.rcParams["axes.unicode_minus"] = False


def load_data():
    df = pd.read_csv(INPUT_PATH, parse_dates=["date"])
    return df


# ------------------------------------------------------------
# 시각화 1 — 12개월 이동평균 추이 (둔산 인접 vs 비교 지역, 그룹 평균)
# ------------------------------------------------------------
def plot_trend_ma12(df):
    target_df = df[df["역명"].isin(TARGET_STATIONS)].groupby("date")["ma_12m"].mean()
    compare_df = df[df["역명"].isin(COMPARE_STATIONS)].groupby("date")["ma_12m"].mean()

    fig, ax = plt.subplots(figsize=(11, 6))
    ax.plot(target_df.index, target_df.values, label="둔산 인접 역 평균 (정부청사·시청·갈마·탄방)",
            color="#c0392b", linewidth=2)
    ax.plot(compare_df.index, compare_df.values, label="비교 지역 역 평균 (유성온천·노은)",
            color="#2980b9", linewidth=2)

    # 팬데믹 구간 음영 표시
    pandemic = df[df["period_label"] == "팬데믹 구간"]
    if not pandemic.empty:
        ax.axvspan(pandemic["date"].min(), pandemic["date"].max(),
                   color="gray", alpha=0.15, label="팬데믹 구간(참고용)")

    ax.set_title("둔산 인접 역 vs 비교 지역 역 — 12개월 이동평균 이용객 추이", fontsize=14, pad=12)
    ax.set_xlabel("연월")
    ax.set_ylabel("월평균 이용객수(12개월 이동평균, 명)")
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG_DIR, "01_trend_ma12.png"), dpi=150)
    plt.close(fig)
    print("[저장] images/01_trend_ma12.png")


# ------------------------------------------------------------
# 시각화 2 — 연도별 총 이용객 합계 비교 (막대그래프)
#            * 데이터가 불완전한 연도(2020, 2026 등)는 별도 표시
# ------------------------------------------------------------
def plot_yearly_total(df):
    yearly = (
        df.assign(group=df["역명"].apply(
            lambda s: "둔산 인접" if s in TARGET_STATIONS else ("비교 지역" if s in COMPARE_STATIONS else None)
        ))
        .dropna(subset=["group"])
        .groupby(["년도", "group"])["total_users"]
        .sum()
        .unstack()
    )
    # 완전하지 않은 연도(12개월 미만) 식별
    months_per_year = df.groupby("년도")["월"].nunique()
    incomplete_years = months_per_year[months_per_year < 12].index.tolist()

    fig, ax = plt.subplots(figsize=(11, 6))
    yearly.plot(kind="bar", ax=ax, color=["#c0392b", "#2980b9"])

    for i, year in enumerate(yearly.index):
        if year in incomplete_years:
            ax.text(i, yearly.loc[year].max() * 1.02, "자료 불완전",
                    ha="center", fontsize=8, color="gray", rotation=0)

    ax.set_title("연도별 총 이용객 합계 비교 (둔산 인접 vs 비교 지역)", fontsize=14, pad=12)
    ax.set_xlabel("연도")
    ax.set_ylabel("연간 총 이용객수(승차+하차, 명)")
    ax.legend(title="")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG_DIR, "02_yearly_total.png"), dpi=150)
    plt.close(fig)
    print("[저장] images/02_yearly_total.png")


# ------------------------------------------------------------
# 시각화 3 — 전년 동월 대비 증감률(YoY) 분포 비교 (박스플롯)
#            * 팬데믹 구간은 왜곡이 크므로 제외하고 비교
# ------------------------------------------------------------
def plot_yoy_boxplot(df):
    plot_df = df[
        (df["period_label"] != "팬데믹 구간")
        & (~df["is_data_gap"])
        & (df["yoy_change_pct"].notna())
        & (df["역명"].isin(TARGET_STATIONS + COMPARE_STATIONS))
    ].copy()
    plot_df["group"] = plot_df["역명"].apply(
        lambda s: "둔산 인접" if s in TARGET_STATIONS else "비교 지역"
    )

    fig, ax = plt.subplots(figsize=(8, 6))
    plot_df.boxplot(column="yoy_change_pct", by="group", ax=ax,
                     patch_artist=True,
                     boxprops=dict(facecolor="#f0e6e6"))
    ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_title("전년 동월 대비 증감률(YoY) 분포 — 팬데믹 구간 제외", fontsize=13)
    plt.suptitle("")  # pandas 기본 그룹 타이틀 제거
    ax.set_xlabel("")
    ax.set_ylabel("YoY 증감률(%)")
    fig.tight_layout()
    fig.savefig(os.path.join(IMG_DIR, "03_yoy_boxplot.png"), dpi=150)
    plt.close(fig)
    print("[저장] images/03_yoy_boxplot.png")


if __name__ == "__main__":
    df = load_data()
    print(f"[로드 완료] {len(df)}행")

    plot_trend_ma12(df)
    plot_yearly_total(df)
    plot_yoy_boxplot(df)

    print("\n[요약 통계 — 리포트 작성 참고용]")
    for group_name, stations in [("둔산 인접", TARGET_STATIONS), ("비교 지역", COMPARE_STATIONS)]:
        sub = df[df["역명"].isin(stations) & (~df["is_data_gap"])]
        first_year = sub["년도"].min()
        last_year = sub["년도"].max()
        first_val = sub[sub["년도"] == first_year]["total_users"].mean()
        last_val = sub[sub["년도"] == last_year]["total_users"].mean()
        change_pct = (last_val - first_val) / first_val * 100
        print(f"  {group_name}: {first_year}년 평균 {first_val:,.0f}명 -> "
              f"{last_year}년 평균 {last_val:,.0f}명 ({change_pct:+.1f}%)")
