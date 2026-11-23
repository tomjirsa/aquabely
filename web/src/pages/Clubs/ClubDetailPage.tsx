import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { apiGet } from "../../api/client";
import type { ClubDetail } from "../../api/types";
import { ClubAverageLine } from "../../charts/ClubAverageLine";
import { fmtNum, fmtText } from "../../lib/format";
import styles from "./ClubsPage.module.css";

const PLACES = [1, 2, 3];

export function ClubDetailPage() {
  const { id } = useParams();
  const [club, setClub] = useState<ClubDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let live = true;
    setClub(null);
    setError(null);
    apiGet<ClubDetail>(`/api/clubs/${id}`)
      .then((r) => live && setClub(r))
      .catch((e: Error) => live && setError(e.message));
    return () => { live = false; };
  }, [id]);

  return (
    <div className={styles.page}>
      <Link to="/clubs" className={styles.back}>Back to clubs</Link>
      {error && <p role="alert" className={styles.error}>{error}</p>}
      {club && (
        <>
          <h1>{fmtText(club.name)}</h1>

          <h2>Medals</h2>
          <div className={styles.medals}>
            {PLACES.map((p) => {
              const count = club.medals.find((m) => m.place === p)?.count ?? 0;
              return (
                <div key={p} className={styles.medal} data-testid={`medal-${p}`}>
                  <span className={styles.medalPlace}>Place {p}</span>
                  <span className={styles.medalCount}>{count}</span>
                </div>
              );
            })}
          </div>

          <h2>Roster</h2>
          {club.roster.length === 0 ? (
            <p className={styles.empty}>No athletes on the roster.</p>
          ) : (
            <div className={styles.scroll}>
              <table className={styles.table}>
                <thead>
                  <tr><th>Name</th><th className={styles.num}>Year of birth</th><th>Country</th></tr>
                </thead>
                <tbody>
                  {club.roster.map((a, i) => (
                    <tr key={`${a.name}|${i}`}>
                      <td>{fmtText(a.name)}</td>
                      <td className={styles.num}>{fmtText(a.year_of_birth)}</td>
                      <td>{fmtText(a.country)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <h2>Average score</h2>
          <ClubAverageLine rows={club.avg_scores} />
          {club.avg_scores.length > 0 && (
            <p className={styles.empty}>
              Latest: {fmtNum(club.avg_scores[club.avg_scores.length - 1].avg_total)}
            </p>
          )}
        </>
      )}
    </div>
  );
}
