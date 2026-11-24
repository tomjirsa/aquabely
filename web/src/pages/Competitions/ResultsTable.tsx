import type { ResultRow } from "../../api/types";
import { adaptiveRanks, isFiltered, type FilterKey, type Filters } from "../../lib/filters";
import { fmtNum, fmtText } from "../../lib/format";
import { FilterRow } from "./FilterRow";
import { RankPill } from "./RankPill";
import styles from "./CompetitionsPage.module.css";

interface Props {
  rows: ResultRow[];
  filteredRows: ResultRow[];
  filters: Filters;
  onFilterChange: (key: FilterKey, value: string) => void;
}

export function ResultsTable({ rows, filteredRows, filters, onFilterChange }: Props) {
  const filtered = isFiltered(filters);
  if (rows.length === 0) {
    return <p className={styles.empty}>No results for this competition.</p>;
  }
  return (
    <>
      <p className={styles.caption}>Showing {filteredRows.length} of {rows.length} results</p>
      <div className={styles.scroll}>
        <table className={styles.table}>
          <thead>
            <FilterRow filters={filters} onChange={onFilterChange} />
            <tr>
              <th>Rank</th><th>Name</th><th>Born</th><th>Club</th><th>Country</th>
              <th className={styles.num}>Total score</th>
              <th className={styles.num}>Penalty</th>
              <th className={styles.num}>Points behind</th>
            </tr>
          </thead>
          <tbody>
            {filteredRows.length === 0 && (
              <tr>
                <td colSpan={8} className={styles.emptyCell}>No results match these filters.</td>
              </tr>
            )}
            {adaptiveRanks(filteredRows).map(({ row, position }, i) => (
              <tr key={`${row.name}-${i}`}>
                <td><RankPill position={position} official={row.rank} filtered={filtered} /></td>
                <td>{row.name}</td>
                <td>{fmtText(row.year_of_birth)}</td>
                <td>{fmtText(row.club)}</td>
                <td>{fmtText(row.country)}</td>
                <td className={styles.num}>{fmtNum(row.total_score)}</td>
                <td className={styles.num}>{fmtNum(row.penalty)}</td>
                <td className={styles.num}>{fmtNum(row.points_behind)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
