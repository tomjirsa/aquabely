import { useEffect, useState } from "react";
import { apiGet } from "../../api/client";
import type { CatalogueFigure } from "../../api/types";
import { fmtNum, fmtText } from "../../lib/format";
import styles from "./FiguresPage.module.css";

type Level = "L3" | "U12";

export function FiguresPage() {
  const [level, setLevel] = useState<Level>("L3");
  const [rows, setRows] = useState<CatalogueFigure[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let live = true;
    setRows(null);
    setError(null);
    apiGet<CatalogueFigure[]>(`/api/figures?level=${level}`)
      .then((r) => live && setRows(r))
      .catch((e: Error) => live && setError(e.message));
    return () => { live = false; };
  }, [level]);

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1>Figures</h1>
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

      {rows && rows.length === 0 && (
        <p className={styles.empty}>No figures in the catalogue for this level.</p>
      )}

      {rows && rows.length > 0 && (
        <div className={styles.scroll}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Code</th>
                <th>Name</th>
                <th className={styles.num}>Coefficient</th>
                <th>Description</th>
                <th className={styles.num}>Performances</th>
                <th>Competitions</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={`${r.code ?? ""}-${i}`}>
                  <td>{fmtText(r.code)}</td>
                  <td>{fmtText(r.name)}</td>
                  <td className={styles.num}>{fmtNum(r.coefficient)}</td>
                  <td>{fmtText(r.description_cs)}</td>
                  <td className={styles.num}>{r.performances}</td>
                  <td>{fmtText(r.competitions)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
