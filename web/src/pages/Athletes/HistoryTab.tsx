import { useEffect, useState } from "react";
import { apiGet } from "../../api/client";
import type { FigureHistory } from "../../api/types";
import { JudgeBarChart } from "../../charts/JudgeBarChart";
import { fmtText } from "../../lib/format";
import styles from "./AthleteProfilePage.module.css";

export function HistoryTab({ athleteId }: { athleteId: number }) {
  const [figures, setFigures] = useState<FigureHistory[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState(0);

  useEffect(() => {
    let live = true;
    setFigures(null);
    setError(null);
    setSelected(0);
    apiGet<FigureHistory[]>(`/api/athletes/${athleteId}/figures`)
      .then((r) => live && setFigures(r))
      .catch((e: Error) => live && setError(e.message));
    return () => { live = false; };
  }, [athleteId]);

  if (error) return <p role="alert" className={styles.error}>{error}</p>;
  if (!figures) return <p className={styles.muted}>Loading...</p>;
  if (figures.length === 0) return <p className={styles.muted}>No figure history for this athlete.</p>;

  const current = figures[Math.min(selected, figures.length - 1)];

  return (
    <div>
      <div className={styles.subTabs} role="tablist" aria-label="Figures">
        {figures.map((f, i) => (
          <button
            key={`${f.figure_name ?? ""}-${i}`}
            type="button"
            role="tab"
            aria-selected={i === selected}
            className={i === selected ? styles.tabActive : styles.tab}
            onClick={() => setSelected(i)}
          >
            {fmtText(f.figure_name) || "Unnamed figure"}
          </button>
        ))}
      </div>
      <JudgeBarChart points={current.points} />
    </div>
  );
}
