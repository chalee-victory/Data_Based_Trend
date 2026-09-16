"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Activity, CalendarRange, ChevronDown, Filter, Info, RotateCcw, SlidersHorizontal } from "lucide-react";
import { buildInsights, type InsightRecord } from "../lib/insights";

type RecordItem = {
  station: string; stationCode: number; date: string; boarding: number; alighting: number;
  total: number; ma3: number | null; ma12: number | null; momPct: number | null;
  yoyPct: number | null; residual: number | null; seasonal: number | null; isOutlier: boolean; isDataGap: boolean; periodLabel: string;
};
type DashboardData = { generatedAt: string; source: string; stations: { name: string; code: number }[]; records: RecordItem[] };
type Metric = "total" | "ma3" | "ma12" | "yoyPct" | "residual" | "seasonal";

const DEFAULT_STATIONS = ["중앙로", "월드컵경기장", "판암", "대동", "갑천", "유성온천"];
const COLORS = ["#e4572e", "#2a6f97", "#e3a008", "#4c956c", "#8b5cf6", "#d1495b", "#1d7874", "#6b7280"];
const metricOptions: { value: Metric; label: string; unit: string }[] = [
  { value: "total", label: "원자료", unit: "명" }, { value: "ma3", label: "3개월 평균", unit: "명" },
  { value: "ma12", label: "12개월 평균", unit: "명" }, { value: "yoyPct", label: "YoY 증감률", unit: "%" },
  { value: "residual", label: "시스템 대비 잔차", unit: "%p" }, { value: "seasonal", label: "계절성", unit: "명" },
];

const formatNumber = (value: number | null | undefined) => value == null ? "-" : new Intl.NumberFormat("ko-KR", { maximumFractionDigits: 0 }).format(value);
const formatPercent = (value: number | null | undefined) => value == null ? "-" : `${value > 0 ? "+" : ""}${value.toFixed(1)}%`;
const dateValue = (date: string) => new Date(`${date}-01`).getTime();

export default function Home() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [selected, setSelected] = useState(DEFAULT_STATIONS);
  const [metric, setMetric] = useState<Metric>("total");
  const [showPandemic, setShowPandemic] = useState(true);
  const [smallMultiples, setSmallMultiples] = useState(false);
  const [range, setRange] = useState<[number, number]>([0, 999]);

  useEffect(() => { fetch("/data/dashboard_data.json").then((response) => response.json()).then(setData); }, []);

  const dates = useMemo(() => data ? [...new Set(data.records.map((record) => record.date))].sort() : [], [data]);
  const effectiveRange: [number, number] = [Math.min(range[0], Math.max(0, dates.length - 1)), Math.min(range[1], Math.max(0, dates.length - 1))];
  const filteredDates = dates.slice(effectiveRange[0], effectiveRange[1] + 1);
  const records = useMemo(() => { const filteredSet = new Set(filteredDates); return data?.records.filter((record) => filteredSet.has(record.date)) ?? []; }, [data, filteredDates]);
  const metricInfo = metricOptions.find((option) => option.value === metric) ?? metricOptions[0];

  const chartData = useMemo(() => {
    const byDate = new Map<string, Record<string, number | string | null>>();
    records.forEach((record) => {
      const row = byDate.get(record.date) ?? { date: record.date, timestamp: dateValue(record.date) };
      row[record.station] = record[metric]; byDate.set(record.date, row);
    });
    return [...byDate.values()].sort((a, b) => Number(a.timestamp) - Number(b.timestamp));
  }, [records, metric]);

  const ranking = useMemo(() => {
    if (!data) return [];
    return data.stations.map((station) => {
      const early = data.records.filter((record) => record.station === station.name && ["2015-01", "2015-02", "2015-03", "2015-04", "2015-05", "2015-06", "2015-07", "2015-08", "2015-09", "2015-10", "2015-11", "2015-12", "2016-01", "2016-02", "2016-03", "2016-04", "2016-05", "2016-06", "2016-07", "2016-08", "2016-09", "2016-10", "2016-11", "2016-12"].includes(record.date));
      const late = data.records.filter((record) => record.station === station.name && ["2023", "2024"].some((year) => record.date.startsWith(year)));
      const avg = (items: RecordItem[]) => items.reduce((sum, item) => sum + item.total, 0) / (items.length || 1);
      return { name: station.name, change: ((avg(late) - avg(early)) / avg(early)) * 100 };
    }).sort((a, b) => b.change - a.change);
  }, [data]);

  const totalChange = useMemo(() => { const early = data?.records.filter((r) => r.date.startsWith("2015") || r.date.startsWith("2016")) ?? []; const late = data?.records.filter((r) => r.date.startsWith("2023") || r.date.startsWith("2024")) ?? []; const avg = (items: RecordItem[]) => items.reduce((sum, r) => sum + r.total, 0) / (items.length || 1); return ((avg(late) - avg(early)) / avg(early)) * 100; }, [data]);
  const positiveStations = ranking.filter((station) => station.change > 0).length;
  const latestSelected = records.filter((record) => selected.includes(record.station)).sort((a, b) => b.date.localeCompare(a.date))[0];
  const rangeValues = records.map((record) => record[metric]).filter((value): value is number => typeof value === "number");
  const rangeChange = rangeValues.length ? ((rangeValues[rangeValues.length - 1] - rangeValues[0]) / Math.abs(rangeValues[0] || 1)) * 100 : null;
  const insights = useMemo(() => buildInsights({ records: records as InsightRecord[], selectedStations: selected, metric, showPandemic, smallMultiples }), [records, selected, metric, showPandemic, smallMultiples]);

  const toggleStation = (name: string) => setSelected((current) => current.includes(name) ? current.filter((station) => station !== name) : [...current, name]);
  const reset = () => { setSelected(DEFAULT_STATIONS); setMetric("total"); setShowPandemic(true); setSmallMultiples(false); setRange([0, Math.max(0, dates.length - 1)]); };

  return (
    <main className="dashboard-shell">
      <header className="topbar"><div><div className="eyebrow"><Activity size={14} /> DAEJEON METRO / TREND LAB</div><h1>도시의 이동을 읽는 시간</h1><p>2015년부터 축적된 22개 역의 월별 흐름을 직접 탐색합니다.</p></div><div className="header-meta"><span className="live-dot" /> STATIC DATASET <strong>2015.01 — 2026.07</strong></div></header>
      <section className="summary-grid">
        <Summary label="시스템 전체 변화" value={formatPercent(totalChange)} note="2015–16 평균 → 2023–24 평균" accent="orange" />
        <Summary label="플러스 역" value={`${positiveStations} / ${data?.stations.length ?? 22}`} note="2023–24 평균이 더 높은 역" accent="green" />
        <Summary label="선택 역 최신값" value={formatNumber(latestSelected?.total)} note={latestSelected ? `${latestSelected.station} · ${latestSelected.date}` : "역을 선택하세요"} accent="blue" />
        <Summary label="현재 구간 변화" value={formatPercent(rangeChange)} note={`${filteredDates[0] ?? "-"} → ${filteredDates.at(-1) ?? "-"}`} accent="purple" />
      </section>
      <div className="workspace-grid">
        <aside className="sidebar panel">
          <div className="panel-heading"><div><span className="section-kicker">CONTROL ROOM</span><h2>탐색 조건</h2></div><button className="icon-button" onClick={reset} title="조건 초기화"><RotateCcw size={16} /></button></div>
          <div className="control-block"><div className="control-label"><span>역 선택</span><b>{selected.length}개</b></div><div className="station-list">{data?.stations.map((station) => <label className={`station-option ${selected.includes(station.name) ? "selected" : ""}`} key={station.name}><input type="checkbox" checked={selected.includes(station.name)} onChange={() => toggleStation(station.name)} /><span className="check-mark">{selected.includes(station.name) ? "✓" : ""}</span><span>{station.name}</span><small>{station.code}</small></label>)}</div></div>
          <div className="control-block"><div className="control-label"><span><CalendarRange size={14} /> 기간</span><b>{filteredDates[0] ?? "-"} — {filteredDates.at(-1) ?? "-"}</b></div><div className="range-wrap"><input aria-label="시작 기간" type="range" min="0" max={Math.max(0, dates.length - 1)} value={effectiveRange[0]} onChange={(event) => setRange((current) => [Math.min(Number(event.target.value), current[1]), current[1]])} /><input aria-label="끝 기간" type="range" min="0" max={Math.max(0, dates.length - 1)} value={effectiveRange[1]} onChange={(event) => setRange(([start]) => [start, Math.max(Number(event.target.value), start)])} /></div><div className="range-caption"><span>2015.01</span><span>2026.07</span></div></div>
          <div className="control-block"><div className="control-label"><span><SlidersHorizontal size={14} /> 지표</span></div><div className="metric-list">{metricOptions.map((option) => <label key={option.value} className={`metric-option ${metric === option.value ? "active" : ""}`}><input type="radio" name="metric" checked={metric === option.value} onChange={() => setMetric(option.value)} /><span className="radio-dot" /><span>{option.label}</span></label>)}</div></div>
          <div className="control-block compact-controls"><Toggle label="팬데믹 구간 표시" checked={showPandemic} onChange={setShowPandemic} /><Toggle label="역별 자체 축" checked={smallMultiples} onChange={setSmallMultiples} /></div>
          <div className="sidebar-foot"><Info size={14} /><span>2025년 원본 미수록. 2026년은 7월까지 집계되어 있습니다.</span></div>
        </aside>
        <section className="main-content">
          <div className="panel chart-panel"><div className="panel-heading chart-heading"><div><span className="section-kicker">SIGNAL / {metricInfo.label.toUpperCase()}</span><h2>역별 이용 흐름</h2></div><div className="legend-note"><span className="legend-line" /> {selected.length}개 역 비교 <ChevronDown size={15} /></div></div>{smallMultiples ? <div className="small-multiples">{selected.map((station, index) => <MiniChart key={station} station={station} data={chartData} color={COLORS[index % COLORS.length]} showPandemic={showPandemic} />)}</div> : <div className="chart-wrap"><ResponsiveContainer width="100%" height="100%"><LineChart data={chartData} margin={{ top: 14, right: 18, left: 0, bottom: 10 }}><CartesianGrid strokeDasharray="2 5" stroke="#d7d3ca" vertical={false} />{showPandemic && <ReferenceArea x1={dateValue("2020-02")} x2={dateValue("2022-04")} fill="#8b8174" fillOpacity={0.12} label={{ value: "팬데믹", position: "insideTopLeft", fill: "#8b8174", fontSize: 11 }} />}<XAxis dataKey="timestamp" type="number" scale="time" domain={["dataMin", "dataMax"]} tickFormatter={(value) => new Date(value).getFullYear().toString()} tick={{ fontSize: 11, fill: "#77716b" }} axisLine={false} tickLine={false} /><YAxis tickFormatter={(value) => metricInfo.unit === "명" ? `${Math.round(value / 10000)}만` : `${Math.round(value)}%`} tick={{ fontSize: 11, fill: "#77716b" }} axisLine={false} tickLine={false} width={42} /><Tooltip labelFormatter={(value) => new Date(Number(value)).toLocaleDateString("ko-KR", { year: "numeric", month: "long" })} formatter={(value: unknown, name?: unknown) => { const numericValue = typeof value === "number" ? value : Number(value); return [metricInfo.unit === "명" ? `${formatNumber(numericValue)}명` : `${numericValue.toFixed(1)}${metricInfo.unit}`, String(name ?? "")]; }} contentStyle={{ border: "1px solid #ded8ce", borderRadius: 2, background: "#fffdf8" }} /><Line dataKey={() => undefined} stroke="none" />{selected.map((station, index) => <Line key={station} type="monotone" dataKey={station} name={station} stroke={COLORS[index % COLORS.length]} strokeWidth={2.2} dot={false} connectNulls={false} />)}</LineChart></ResponsiveContainer></div>}</div>
          <InsightPanel insights={insights} />
          <div className="panel ranking-panel"><div className="panel-heading"><div><span className="section-kicker">SYSTEM RANKING</span><h2>역별 구조적 변화</h2></div><span className="hint"><Filter size={14} /> 막대를 누르면 역 선택에 반영됩니다</span></div><div className="ranking-chart"><ResponsiveContainer width="100%" height={Math.max(330, ranking.length * 26)}><BarChart data={ranking} layout="vertical" margin={{ top: 4, right: 24, left: 8, bottom: 4 }}><CartesianGrid strokeDasharray="2 5" horizontal={false} stroke="#e2ddd4" /><XAxis type="number" tickFormatter={(value) => `${value}%`} tick={{ fontSize: 10, fill: "#77716b" }} axisLine={false} tickLine={false} /><YAxis dataKey="name" type="category" width={72} tick={{ fontSize: 11, fill: "#423d38" }} axisLine={false} tickLine={false} /><Tooltip formatter={(value: unknown) => { const numericValue = typeof value === "number" ? value : Number(value); return [`${numericValue.toFixed(1)}%`, "변화율"]; }} cursor={{ fill: "#f4f0e9" }} /><Bar dataKey="change" radius={[0, 2, 2, 0]} barSize={13} onClick={(entry) => toggleStation(String(entry.name))}>{ranking.map((entry) => <Cell key={entry.name} fill={entry.change >= 0 ? "#4c956c" : "#d2674c"} opacity={selected.includes(entry.name) ? 1 : 0.48} />)}</Bar></BarChart></ResponsiveContainer></div></div>
        </section>
      </div>
      <footer className="footer"><span>DATA STORY / 대전 도시철도 역별 수송실적</span><span>Source: 대전교통공사 · Generated {data?.generatedAt ?? "-"}</span></footer>
    </main>
  );
}

function Summary({ label, value, note, accent }: { label: string; value: string; note: string; accent: string }) { return <article className={`summary-card ${accent}`}><span>{label}</span><strong>{value}</strong><small>{note}</small></article>; }
function Toggle({ label, checked, onChange }: { label: string; checked: boolean; onChange: (value: boolean) => void }) { return <label className="toggle-row"><span>{label}</span><input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} /><i className="toggle-track"><em /></i></label>; }
function InsightPanel({ insights }: { insights: { label: string; text: string; tone: string }[] }) { return <section className="insight-panel"><div className="insight-header"><div><span className="section-kicker">READING THE SIGNAL</span><h2>현재 조건에서 보이는 이야기</h2></div><span className="insight-live">LIVE INSIGHT</span></div><div className="insight-grid">{insights.map((insight, index) => <article className={`insight-card ${insight.tone}`} key={`${insight.label}-${index}`}><span className="insight-index">0{index + 1}</span><div><b>{insight.label}</b><p>{insight.text}</p></div></article>)}</div></section>; }
function MiniChart({ station, data, color, showPandemic }: { station: string; data: Record<string, number | string | null>[]; color: string; showPandemic: boolean }) { return <article className="mini-chart"><div className="mini-heading"><span style={{ backgroundColor: color }} />{station}</div><div className="mini-chart-body"><ResponsiveContainer width="100%" height="100%"><LineChart data={data} margin={{ top: 3, right: 8, left: 0, bottom: 0 }}><CartesianGrid strokeDasharray="2 5" stroke="#e2ddd4" vertical={false} />{showPandemic && <ReferenceArea x1={dateValue("2020-02")} x2={dateValue("2022-04")} fill="#8b8174" fillOpacity={0.1} />}<XAxis dataKey="timestamp" type="number" scale="time" domain={["dataMin", "dataMax"]} hide /><YAxis hide /><Line dataKey={station} stroke={color} strokeWidth={2} dot={false} connectNulls={false} /></LineChart></ResponsiveContainer></div></article>; }
