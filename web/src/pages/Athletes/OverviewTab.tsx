import { useEffect, useState } from "react";
import { apiGet } from "../../api/client";
import type { AthleteCompetition, AthleteProfile } from "../../api/types";
import { PositionsChart } from "../../charts/PositionsChart";
import { ScoreLine } from "../../charts/ScoreLine";
import { fmtNum, fmtText } from "../../lib/format";
import styles from "./AthleteProfilePage.module.css";

interface Props {
  athleteId: number;
  profile: AthleteProfile;
}

export function OverviewTab({ athleteId, profile }: Props) {
  // Figure ranks for the dashed lines come from the competitions endpoint; the chart still works without them.
  const [comps, setComps] = useState<AthleteCompetition[]>([]);

  useEffect(() => {
    let live = true;
    apiGet<AthleteCompetition[]>(`/api/athletes/${athleteId}/competitions`)
      .then((r) => live && Array.isArray(r) && setComps(r))
      .catch(() => undefined);
    return () => { live = false; };
  }, [athleteId]);

  return (
    <div>
      <section className={styles.section}>
        <h2>Total score</h2>
        <ScoreLine rows={profile.history} />
      </section>
      <section className={styles.section}>
        <h2>Positions</h2>
        <PositionsChart ranks={profile.overall_ranks} figures={comps} />
      </section>
      <section className={styles.section}>
        <h2>History</h2>
        {profile.history.length === 0 ? (
          <p className={styles.muted}>No competitions yet.</p>
        ) : (
          <div className={styles.scroll}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Level</th>
                  <th>Competition</th>
                  <th>Date</th>
                  <th>Age group</th>
                  <th className={styles.num}>Rank</th>
                  <th className={styles.num}>Total score</th>
                  <th className={styles.num}>Field size</th>
                </tr>
              </thead>
              <tbody>
                {profile.history.map((h, i) => (
                  <tr key={`${h.competition}-${h.date ?? ""}-${i}`}>
                    <td>{fmtText(h.level)}</td>
                    <td>{fmtText(h.competition)}</td>
                    <td>{fmtText(h.date)}</td>
                    <td>{fmtText(h.age_group)}</td>
                    <td className={styles.num}>{fmtText(h.rank)}</td>
                    <td className={styles.num}>{fmtNum(h.total_score)}</td>
                    <td className={styles.num}>{fmtText(h.field_size)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
