import { useEffect, useState } from "react";
import { apiGet } from "../../api/client";
import type { AthleteCompetition } from "../../api/types";
import { fmtNum, fmtText } from "../../lib/format";
import {
  overallOrByYear,
  rankLabel,
  rankTone,
  usesByYearFallback,
  type RankMode,
} from "../../lib/athleteRanking";
import styles from "./AthleteProfilePage.module.css";

const TONE_CLASS = {
  better: styles.toneBetter,
  worse: styles.toneWorse,
  equal: styles.toneEqual,
  none: "",
} as const;

export function CompetitionsTab({ athleteId }: { athleteId: number }) {
  const [comps, setComps] = useState<AthleteCompetition[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<RankMode>("overall");
  const [selected, setSelected] = useState(0);

  useEffect(() => {
    let live = true;
    setComps(null);
    setError(null);
    setSelected(0);
    apiGet<AthleteCompetition[]>(`/api/athletes/${athleteId}/competitions`)
      .then((r) => live && setComps(r))
      .catch((e: Error) => live && setError(e.message));
    return () => { live = false; };
  }, [athleteId]);

  if (error) return <p role="alert" className={styles.error}>{error}</p>;
  if (!comps) return <p className={styles.muted}>Loading...</p>;
  if (comps.length === 0) return <p className={styles.muted}>No competitions yet.</p>;

  const comp = comps[Math.min(selected, comps.length - 1)];
  const { rank, size } = overallOrByYear(comp, mode);
  const fallback = usesByYearFallback(comp, mode);
  const rankLine = `Rank ${mode === "by-year" && !fallback ? "by year" : "overall"}: ${rankLabel(rank, size)}`;

  return (
    <div>
      <div className={styles.modeSwitch} role="group" aria-label="Rank mode">
        {(["overall", "by-year"] as RankMode[]).map((m) => (
          <button
            key={m}
            type="button"
            aria-pressed={mode === m}
            className={mode === m ? styles.modeActive : styles.modeBtn}
            onClick={() => setMode(m)}
          >
            {m === "overall" ? "Overall" : "By year"}
          </button>
        ))}
      </div>

      <div className={styles.subTabs} role="tablist" aria-label="Competitions">
        {comps.map((c, i) => (
          <button
            key={`${c.competition}-${c.date ?? ""}-${i}`}
            type="button"
            role="tab"
            aria-selected={i === selected}
            className={i === selected ? styles.tabActive : styles.tab}
            onClick={() => setSelected(i)}
          >
            {c.competition}
          </button>
        ))}
      </div>

      <p className={styles.rankLine}>{rankLine}</p>
      {fallback && <p className={styles.note}>Overall (no by-year rank)</p>}

      {comp.figures.length === 0 ? (
        <p className={styles.muted}>No figure results for this competition.</p>
      ) : (
        <div className={styles.scroll}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Figure</th>
                <th className={styles.num}>Coefficient</th>
                <th>Judge marks</th>
                <th className={styles.num}>Average</th>
                <th className={styles.num}>Score</th>
                <th className={styles.num}>Rank</th>
              </tr>
            </thead>
            <tbody>
              {comp.figures.map((f, i) => {
                const fr = overallOrByYear(
                  {
                    rank_overall: f.fig_rank_overall,
                    field_size: f.fig_field_size,
                    rank_by_year: f.fig_rank_by_year,
                    field_size_by_year: f.fig_field_size_by_year,
                  },
                  mode,
                );
                return (
                  <tr key={`${f.figure_name ?? ""}-${i}`}>
                    <td>{fmtText(f.figure_name)}</td>
                    <td className={styles.num}>{fmtNum(f.coefficient)}</td>
                    <td className={styles.marks}>
                      {f.judges.map((j, k) => (
                        <span key={k} className={styles.mark}>
                          {f.dropped[k] ? <s>{fmtNum(j, 1)}</s> : fmtNum(j, 1)}
                        </span>
                      ))}
                    </td>
                    <td className={styles.num}>{fmtNum(f.average)}</td>
                    <td className={styles.num}>{fmtNum(f.figure_score)}</td>
                    <td className={styles.num}>
                      <span className={`${styles.rankCell} ${TONE_CLASS[rankTone(fr.rank, rank)]}`}>
                        {fr.rank === null ? "" : rankLabel(fr.rank, fr.size)}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
