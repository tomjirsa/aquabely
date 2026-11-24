import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { AthleteHistoryRow } from "../api/types";
import { fmtNum } from "../lib/format";

export function ScoreLine({ rows }: { rows: AthleteHistoryRow[] }) {
  const data = rows.map((r) => ({ label: r.competition, score: r.total_score }));
  return (
    <div style={{ width: "100%", height: 260 }} role="img" aria-label="Total score per competition">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
          <CartesianGrid stroke="var(--aq-border)" strokeDasharray="3 3" />
          <XAxis dataKey="label" tick={{ fill: "var(--aq-muted)", fontSize: 12 }} />
          <YAxis tick={{ fill: "var(--aq-muted)", fontSize: 12 }} />
          <Tooltip formatter={(v) => fmtNum(typeof v === "number" ? v : null)} />
          <Line type="monotone" dataKey="score" name="Total score" stroke="var(--aq-primary)" strokeWidth={2} connectNulls />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
