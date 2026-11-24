import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiGet } from "../../api/client";
import type { AthleteSummary } from "../../api/types";
import { fmtNum, fmtText } from "../../lib/format";
import styles from "./AthletesPage.module.css";

export function AthletesPage() {
  const navigate = useNavigate();
  const [q, setQ] = useState("");
  const [rows, setRows] = useState<AthleteSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let live = true;
    setError(null);
    apiGet<AthleteSummary[]>(`/api/athletes?q=${encodeURIComponent(q.trim())}`)
      .then((r) => live && setRows(r))
      .catch((e: Error) => live && setError(e.message));
    return () => { live = false; };
  }, [q]);

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1>Athletes</h1>
        <input
          type="search"
          className={styles.search}
          placeholder="Search name or club"
          aria-label="Search athletes"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
      </header>

      {error && <p role="alert" className={styles.error}>{error}</p>}
      {rows && rows.length === 0 && <p className={styles.empty}>No athletes found.</p>}

      {rows && rows.length > 0 && (
        <div className={styles.scroll}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Athlete</th>
                <th>Club</th>
                <th className={styles.num}>Competitions</th>
                <th className={styles.num}>Best score</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((a) => (
                <tr
                  key={a.id}
                  className={styles.row}
                  tabIndex={0}
                  onClick={() => navigate(`/athletes/${a.id}`)}
                  onKeyDown={(e) => { if (e.key === "Enter") navigate(`/athletes/${a.id}`); }}
                >
                  <td>{fmtText(a.name)}</td>
                  <td>{fmtText(a.club)}</td>
                  <td className={styles.num}>{fmtText(a.competitions)}</td>
                  <td className={styles.num}>{fmtNum(a.best_score)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
