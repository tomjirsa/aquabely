import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiGet } from "../../api/client";
import type { ClubSummary } from "../../api/types";
import { fmtText } from "../../lib/format";
import styles from "./ClubsPage.module.css";

export function ClubsPage() {
  const [rows, setRows] = useState<ClubSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let live = true;
    apiGet<ClubSummary[]>("/api/clubs")
      .then((r) => live && setRows(r))
      .catch((e: Error) => live && setError(e.message));
    return () => { live = false; };
  }, []);

  return (
    <div className={styles.page}>
      <h1>Clubs</h1>
      {error && <p role="alert" className={styles.error}>{error}</p>}
      {rows && rows.length === 0 && <p className={styles.empty}>No clubs found.</p>}
      {rows && rows.length > 0 && (
        <ul className={styles.list}>
          {rows.map((c) => (
            <li key={c.id}>
              <Link className={styles.link} to={`/clubs/${c.id}`}>{fmtText(c.name)}</Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
