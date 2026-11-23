import { useEffect, useMemo, useState } from "react";
import { apiGet } from "../../api/client";
import type { CompetitionEntry, FigureDetailRow, ResultRow } from "../../api/types";
import { EMPTY_FILTERS, filterResults, type FilterKey, type Filters } from "../../lib/filters";
import { FigureDetailTable } from "./FigureDetailTable";
import { ResultsTable } from "./ResultsTable";
import styles from "./CompetitionsPage.module.css";

type Level = "L3" | "U12";

function label(c: CompetitionEntry): string {
  const parts = [c.competition];
  if (c.age_group_label) parts.push(c.age_group_label);
  if (c.date) parts.push(c.date);
  return parts.join(" · ");
}

export function CompetitionsPage() {
  const [level, setLevel] = useState<Level>("L3");
  const [competitions, setCompetitions] = useState<CompetitionEntry[] | null>(null);
  const [ccId, setCcId] = useState<number | null>(null);
  const [results, setResults] = useState<ResultRow[]>([]);
  const [detail, setDetail] = useState<FigureDetailRow[]>([]);
  const [loadedCcId, setLoadedCcId] = useState<number | null>(null);
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let live = true;
    setCcId(null);
    setCompetitions(null);
    setError(null);
    apiGet<CompetitionEntry[]>(`/api/competitions?level=${level}`)
      .then((c) => live && setCompetitions(c))
      .catch((e: Error) => live && setError(e.message));
    return () => { live = false; };
  }, [level]);

  useEffect(() => {
    if (ccId === null) return;
    let live = true;
    setError(null);
    Promise.all([
      apiGet<ResultRow[]>(`/api/competitions/${ccId}/results`),
      apiGet<FigureDetailRow[]>(`/api/competitions/${ccId}/figure-detail`),
    ])
      .then(([r, d]) => {
        if (!live) return;
        setResults(r);
        setDetail(d);
        setLoadedCcId(ccId);
      })
      .catch((e: Error) => live && setError(e.message));
    return () => { live = false; };
  }, [ccId]);

  const filteredRows = useMemo(() => filterResults(results, filters), [results, filters]);

  const onFilterChange = (key: FilterKey, value: string) =>
    setFilters((f) => ({ ...f, [key]: value }));

  const onSelect = (value: string) => {
    setResults([]);
    setDetail([]);
    setLoadedCcId(null);
    setFilters(EMPTY_FILTERS);
    setCcId(value === "" ? null : Number(value));
  };

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1>Competition</h1>
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

      <section className={styles.selection}>
        <label htmlFor="competition-select">Competition</label>
        <select
          id="competition-select"
          className={styles.select}
          value={ccId === null ? "" : String(ccId)}
          onChange={(e) => onSelect(e.target.value)}
        >
          <option value="">Select a competition</option>
          {(competitions ?? []).map((c) => (
            <option key={c.competition_category_id} value={c.competition_category_id}>{label(c)}</option>
          ))}
        </select>
      </section>

      {error && <p role="alert" className={styles.error}>{error}</p>}

      {!error && competitions !== null && competitions.length === 0 && (
        <p className={styles.empty}>No {level} competitions yet. Use the Import page to add one.</p>
      )}

      {ccId !== null && loadedCcId === ccId && results.length === 0 && (
        <section>
          <h2>Results</h2>
          <p className={styles.empty}>No results for this competition.</p>
        </section>
      )}

      {ccId !== null && loadedCcId === ccId && results.length > 0 && (
        <>
          <section>
            <h2>Results</h2>
            <ResultsTable
              rows={results}
              filteredRows={filteredRows}
              filters={filters}
              onFilterChange={onFilterChange}
            />
          </section>
          <section>
            <h2>Figure detail</h2>
            <FigureDetailTable detail={detail} athletes={filteredRows} />
          </section>
        </>
      )}
    </div>
  );
}
