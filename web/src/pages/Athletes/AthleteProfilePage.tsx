import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { apiGet } from "../../api/client";
import type { AthleteProfile } from "../../api/types";
import { fmtNum } from "../../lib/format";
import { CompetitionsTab } from "./CompetitionsTab";
import { HistoryTab } from "./HistoryTab";
import { OverviewTab } from "./OverviewTab";
import styles from "./AthleteProfilePage.module.css";

type Tab = "overview" | "competitions" | "history";
const TABS: { id: Tab; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "competitions", label: "Competitions" },
  { id: "history", label: "History" },
];

function orNa(v: string | number | null | undefined): string {
  return v === null || v === undefined || v === "" ? "n/a" : String(v);
}

export function AthleteProfilePage() {
  const { id } = useParams();
  const athleteId = Number(id);
  const [profile, setProfile] = useState<AthleteProfile | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("overview");

  useEffect(() => {
    let live = true;
    setProfile(null);
    setError(null);
    apiGet<AthleteProfile>(`/api/athletes/${athleteId}`)
      .then((p) => live && setProfile(p))
      .catch((e: Error) => live && setError(e.message));
    return () => { live = false; };
  }, [athleteId]);

  if (error) return <div className={styles.page}><p role="alert" className={styles.error}>{error}</p></div>;
  if (!profile) return <div className={styles.page}><p className={styles.muted}>Loading...</p></div>;

  const best = profile.best_score === null ? "n/a" : fmtNum(profile.best_score);
  const avg = profile.avg_score === null ? "n/a" : fmtNum(profile.avg_score);

  return (
    <div className={styles.page}>
      <h1 className={styles.title}>{profile.name}</h1>
      <div className={styles.cards}>
        <div className={styles.card}><span className={styles.cardLabel}>Club</span><span className={styles.cardValue}>{orNa(profile.club)}</span></div>
        <div className={styles.card}><span className={styles.cardLabel}>Born</span><span className={styles.cardValue}>{orNa(profile.year_of_birth)}</span></div>
        <div className={styles.card}><span className={styles.cardLabel}>Competitions</span><span className={styles.cardValue}>{orNa(profile.competitions)}</span></div>
        <div className={styles.card}><span className={styles.cardLabel}>Best / average</span><span className={styles.cardValue}>{`${best} / ${avg}`}</span></div>
      </div>

      <div className={styles.tabs} role="tablist" aria-label="Athlete sections">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={tab === t.id}
            className={tab === t.id ? styles.tabActive : styles.tab}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "overview" && <OverviewTab athleteId={athleteId} profile={profile} />}
      {tab === "competitions" && <CompetitionsTab athleteId={athleteId} />}
      {tab === "history" && <HistoryTab athleteId={athleteId} />}
    </div>
  );
}
