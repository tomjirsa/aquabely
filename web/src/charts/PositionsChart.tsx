import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { AthleteCompetition, OverallRank } from "../api/types";

const FIGURE_COLOURS = ["var(--aq-accent)", "var(--aq-muted)", "var(--aq-text)"];

interface Props {
  ranks: OverallRank[];
  /** Per-competition figure ranks (overall) drawn as dashed lines. */
  figures: AthleteCompetition[];
}

export function PositionsChart({ ranks, figures }: Props) {
  const figureNames: string[] = [];
  const data = ranks.map((r) => {
    const row: Record<string, string | number | null> = { label: r.competition, overall: r.rank_overall };
    const comp = figures.find((c) => c.competition === r.competition && c.date === r.date);
    for (const f of comp?.figures ?? []) {
      const name = f.figure_name ?? "";
      if (!name) continue;
      if (!figureNames.includes(name)) figureNames.push(name);
      row[name] = f.fig_rank_overall;
    }
    return row;
  });

  return (
    <div style={{ width: "100%", height: 280 }} role="img" aria-label="Overall and figure positions per competition">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
          <CartesianGrid stroke="var(--aq-border)" strokeDasharray="3 3" />
          <XAxis dataKey="label" tick={{ fill: "var(--aq-muted)", fontSize: 12 }} />
          <YAxis reversed allowDecimals={false} tick={{ fill: "var(--aq-muted)", fontSize: 12 }} />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="overall" name="Overall" stroke="var(--aq-primary)" strokeWidth={2} connectNulls />
          {figureNames.map((n, i) => (
            <Line
              key={n}
              type="monotone"
              dataKey={n}
              stroke={FIGURE_COLOURS[i % FIGURE_COLOURS.length]}
              strokeDasharray="5 4"
              dot={false}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
