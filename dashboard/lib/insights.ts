export type InsightRecord = {
  station: string;
  date: string;
  total: number;
  ma3: number | null;
  residual: number | null;
  periodLabel: string;
};

export type InsightMetric = "total" | "ma3" | "ma12" | "yoyPct" | "residual";
export type InsightItem = { label: string; text: string; tone: "accent" | "positive" | "neutral" | "warning" };

const monthValue = (date: string) => new Date(`${date}-01`).getTime();
const valueFor = (record: InsightRecord, metric: InsightMetric) => {
  const value = record[metric as keyof InsightRecord];
  return typeof value === "number" ? value : null;
};
const average = (values: number[]) => values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null;
const percent = (value: number | null) => value == null || !Number.isFinite(value) ? null : `${value >= 0 ? "+" : ""}${value.toFixed(1)}%`;
const percentPoint = (value: number | null) => value == null || !Number.isFinite(value) ? null : `${value >= 0 ? "+" : ""}${value.toFixed(1)}%p`;

function periodChange(records: InsightRecord[], metric: InsightMetric, excludePandemic = false) {
  const usable = records
    .filter((record) => !excludePandemic || record.periodLabel !== "팬데믹 구간")
    .map((record) => ({ date: record.date, value: valueFor(record, metric) }))
    .filter((record): record is { date: string; value: number } => record.value != null)
    .sort((a, b) => monthValue(a.date) - monthValue(b.date));
  const start = average(usable.slice(0, 3).map((record) => record.value));
  const end = average(usable.slice(-3).map((record) => record.value));
  return start && end ? ((end / start) - 1) * 100 : null;
}

export function findBiggestShift(records: InsightRecord[], metric: "total" | "ma3"): { date: string; pct: number } | null {
  const usable = records
    .map((record) => ({ date: record.date, value: valueFor(record, metric) }))
    .filter((record): record is { date: string; value: number } => record.value != null)
    .sort((a, b) => monthValue(a.date) - monthValue(b.date));
  let best: { date: string; pct: number } | null = null;
  usable.forEach((current) => {
    const time = monthValue(current.date);
    const before = usable.filter((record) => { const difference = (time - monthValue(record.date)) / (1000 * 60 * 60 * 24 * 30.4375); return difference >= 0 && difference <= 6; });
    const after = usable.filter((record) => { const difference = (monthValue(record.date) - time) / (1000 * 60 * 60 * 24 * 30.4375); return difference >= 0 && difference <= 6; });
    const pre = average(before.map((record) => record.value));
    const post = average(after.map((record) => record.value));
    if (pre && post && before.length >= 3 && after.length >= 3) {
      const pct = ((post / pre) - 1) * 100;
      if (!best || Math.abs(pct) > Math.abs(best.pct)) best = { date: current.date, pct };
    }
  });
  return best;
}

export function buildInsights({ records, selectedStations, metric, showPandemic, smallMultiples }: { records: InsightRecord[]; selectedStations: string[]; metric: InsightMetric; showPandemic: boolean; smallMultiples: boolean }): InsightItem[] {
  if (!selectedStations.length) return [{ label: "필터", text: "역을 하나 이상 선택하면 현재 조건의 흐름을 해석해 드립니다.", tone: "warning" }];
  const stationRecords = (station: string, source = records) => source.filter((record) => record.station === station);
  const primaryStation = selectedStations[0];
  const primary = stationRecords(primaryStation);
  const insights: InsightItem[] = [];
  const change = periodChange(primary, metric, false);
  const visibleStart = records.map((record) => record.date).sort()[0];
  const visibleEnd = records.map((record) => record.date).sort().at(-1);

  if (primary.length < 3) {
    insights.push({ label: "데이터 충분성", text: "선택된 구간의 데이터가 3개월 미만이라 변화율의 신뢰도가 낮습니다.", tone: "warning" });
  } else if (selectedStations.length === 1) {
    insights.push({ label: "기간 내 전체 변화", text: `${primaryStation}역은 선택한 기간(${visibleStart ?? "-"}~${visibleEnd ?? "-"}) 동안 총 ${percent(change) ?? "-"} 변화했습니다.`, tone: change != null && change >= 0 ? "positive" : "accent" });
  }

  const shiftSource = selectedStations.flatMap((station) => stationRecords(station));
  const shift = findBiggestShift(shiftSource, metric === "ma3" ? "ma3" : "total");
  if (shift) {
    const shiftDate = shift.date;
    const shiftPct = shift.pct;
    insights.push({ label: "가장 뚜렷한 변화", text: `이 구간에서 가장 뚜렷한 변화는 ${shiftDate.replace("-", "년 ")}월 경으로, 전후 6개월 평균 기준 ${percent(shiftPct)}의 변화가 있었습니다.`, tone: shiftPct >= 0 ? "positive" : "accent" });
  }

  if (selectedStations.length >= 2) {
    const comparison = selectedStations.map((station) => ({ station, change: periodChange(stationRecords(station), metric) })).filter((item): item is { station: string; change: number } => item.change != null).sort((a, b) => b.change - a.change);
    if (comparison.length >= 2) insights.push({ label: "역 간 비교", text: `선택한 ${comparison.length}개 역 중 ${comparison[0].station}이 가장 강하게 성장(${percent(comparison[0].change)})했고, ${comparison.at(-1)?.station}이 가장 크게 감소(${percent(comparison.at(-1)?.change ?? null)})했습니다.`, tone: "neutral" });
  }

  if (metric === "residual" || selectedStations.length === 1) {
    const residual = average(primary.map((record) => record.residual).filter((value): value is number => value != null));
    if (residual != null) insights.push({ label: "시스템 평균 대비", text: `${primaryStation}역은 이 기간 동안 22개 역 평균보다 ${percentPoint(residual)} 더 좋은 흐름을 보였습니다.`, tone: residual >= 0 ? "positive" : "accent" });
  }

  if (selectedStations.length === 1 && showPandemic) {
    const included = periodChange(primary, metric, false);
    const excluded = periodChange(primary, metric, true);
    if (included != null && excluded != null) insights.push({ label: "팬데믹 영향", text: `팬데믹 구간을 포함하면 변화율은 ${percent(included)}지만, 제외하면 ${percent(excluded)}로 달라집니다 — 장기 흐름에 팬데믹 영향이 반영되어 있습니다.`, tone: Math.abs(included - excluded) > 5 ? "warning" : "neutral" });
  }

  if (smallMultiples) insights.push({ label: "축 모드 안내", text: "역별 자체 축으로 보면 공유 축에서 눌려 보이던 역별 변화가 더 잘 드러날 수 있습니다.", tone: "neutral" });
  return insights;
}
