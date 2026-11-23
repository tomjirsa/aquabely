import type { FigureDetailRow, ResultRow } from "../../api/types";
import { figureKey, fmtNum, fmtText } from "../../lib/format";
import styles from "./CompetitionsPage.module.css";

interface Props {
  detail: FigureDetailRow[];
  athletes: ResultRow[];
}

export function FigureDetailTable({ detail, athletes }: Props) {
  const byAthlete = new Map<string, FigureDetailRow[]>();
  for (const d of detail) {
    const list = byAthlete.get(figureKey(d.athlete, d.rank));
    if (list) list.push(d);
    else byAthlete.set(figureKey(d.athlete, d.rank), [d]);
  }
  let judgeCount = 0;
  for (const d of detail) {
    d.judges.forEach((j, i) => {
      if (j !== null && j !== undefined) judgeCount = Math.max(judgeCount, i + 1);
    });
  }
  judgeCount = Math.min(judgeCount, 7);
  const cols = Array.from({ length: judgeCount }, (_, i) => i);

  return (
    <>
      <div className={styles.scroll}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Athlete</th><th>Figure</th>
              {cols.map((i) => <th key={i} className={styles.num}>J{i + 1}</th>)}
              <th className={styles.num}>Average</th>
              <th className={styles.num}>Result</th>
            </tr>
          </thead>
          <tbody>
            {athletes.map((a, ai) => {
              const rows = byAthlete.get(figureKey(a.name, a.rank)) ?? [];
              return rows.map((r, ri) => (
                <tr key={`${a.name}-${ai}-${ri}`} className={ri === 0 ? styles.groupStart : undefined}>
                  {ri === 0 && <td rowSpan={rows.length} className={styles.athlete}>{a.name}</td>}
                  <td>{fmtText(r.figure_name)}</td>
                  {cols.map((i) => (
                    <td key={i} className={styles.num}>
                      {r.dropped[i] ? <s className={styles.dropped}>{fmtNum(r.judges[i])}</s> : fmtNum(r.judges[i])}
                    </td>
                  ))}
                  <td className={styles.num}>{fmtNum(r.average)}</td>
                  <td className={styles.num}>{fmtNum(r.figure_score)}</td>
                </tr>
              ));
            })}
          </tbody>
        </table>
      </div>
      <p className={styles.footnote}>
        Struck-through marks are the highest and lowest, dropped from the average. Result = average × difficulty.
      </p>
    </>
  );
}
