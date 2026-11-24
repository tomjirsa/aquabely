import { useEffect, useState } from "react";
import { apiGet } from "../../api/client";
import type { HomeSummary } from "../../api/types";
import { fmtNum, fmtText } from "../../lib/format";
import styles from "./HomePage.module.css";

type Level = "L3" | "U12";

export function HomePage() {
  const [level, setLevel] = useState<Level>("L3");
  const [summary, setSummary] = useState<HomeSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let live = true;
    setSummary(null);
    setError(null);
    apiGet<HomeSummary>(`/api/home?level=${level}`)
      .then((s) => live && setSummary(s))
      .catch((e: Error) => live && setError(e.message));
    return () => { live = false; };
  }, [level]);

  const latest = summary?.latest_competition ?? null;

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1>Home</h1>
        <div className={styles.levelSwitch} role="group" aria-label="Level">
          {(["L3", "U12"] as Level[]).map((l) => (
            <button
              key={l}
              type="button"
              aria-pressed={level === l}
              className={level === l ? styles.levelActive : styles.levelBtn}
              onClick={() => setLevel(l)}
            >
              {l}
            </button>
          ))}
        </div>
      </header>

      {error && <p role="alert" className={styles.error}>{error}</p>}

      {summary && !latest && (
        <p className={styles.empty}>No {level} competitions yet. Use the Import page to add one.</p>
      )}

      {summary && latest && (
        <div className={styles.cards}>
          <section className={styles.card}>
            <h2>Latest competition</h2>
            <div className={styles.value}>{latest.competition}</div>
            <div className={styles.sub}>
              {[fmtText(latest.age_group_label), fmtText(latest.date)].filter(Boolean).join(" · ")}
            </div>
          </section>
          <section className={styles.card}>
            <h2>Athletes</h2>
            <div className={styles.value}>{summary.athlete_count}</div>
          </section>
          <section className={styles.card}>
            <h2>Top scorer</h2>
            <div className={styles.value}>{fmtText(summary.top_scorer_name)}</div>
            <div className={styles.sub}>{fmtNum(summary.top_scorer_total)}</div>
          </section>
        </div>
      )}
    </div>
  );
}
