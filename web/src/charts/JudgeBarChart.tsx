import { Bar, CartesianGrid, Cell, ComposedChart, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { FigurePoint } from "../api/types";
import { fmtNum } from "../lib/format";

/** Competitions on x, one bar per judge (dropped marks hollow), trimmed average as a marker. */
export function JudgeBarChart({ points }: { points: FigurePoint[] }) {
  const judgeCount = points.reduce((m, p) => Math.max(m, p.judges.length), 0);
  const data = points.map((p) => {
    const row: Record<string, string | number | null> = { label: p.competition, average: p.average };
    p.judges.forEach((j, i) => { row[`j${i}`] = j; });
    return row;
  });
  const judgeIdx = Array.from({ length: judgeCount }, (_, i) => i);

  return (
    <div style={{ width: "100%", height: 300 }} role="img" aria-label="Judge marks per competition">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
          <CartesianGrid stroke="var(--aq-border)" strokeDasharray="3 3" />
          <XAxis dataKey="label" tick={{ fill: "var(--aq-muted)", fontSize: 12 }} />
          <YAxis domain={[0, 10]} tick={{ fill: "var(--aq-muted)", fontSize: 12 }} />
          <Tooltip formatter={(v) => fmtNum(typeof v === "number" ? v : null, 1)} />
          <Legend />
          {judgeIdx.map((i) => (
            <Bar key={i} dataKey={`j${i}`} name={`Judge ${i + 1}`} fill="var(--aq-primary)" stroke="var(--aq-primary)" strokeWidth={1.5}>
              {points.map((p, k) => (
                <Cell
                  key={k}
                  fill={p.dropped[i] ? "transparent" : "var(--aq-primary)"}
                  stroke="var(--aq-primary)"
                />
              ))}
            </Bar>
          ))}
          <Line
            dataKey="average"
            name="Trimmed average"
            stroke="none"
            isAnimationActive={false}
            dot={{ r: 5, fill: "var(--aq-accent)", stroke: "var(--aq-bg)", strokeWidth: 1.5 }}
            activeDot={{ r: 6 }}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
