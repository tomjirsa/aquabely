import type { ResultRow } from "../../api/types";
import { adaptiveRanks, isFiltered, type FilterKey, type Filters } from "../../lib/filters";
import { FilterRow } from "./FilterRow";
import { RankPill } from "./RankPill";
import styles from "./CompetitionsPage.module.css";

interface Props {
  rows: ResultRow[];
  filteredRows: ResultRow[];
  filters: Filters;
  onFilterChange: (key: FilterKey, value: string) => void;
}

const fmt = (v: number | null) => (v === null || v === undefined ? "-" : String(v));

export function ResultsTable({ rows, filteredRows, filters, onFilterChange }: Props) {
  const filtered = isFiltered(filters);
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
            {adaptiveRanks(filteredRows).map(({ row, position }, i) => (
              <tr key={`${row.name}-${i}`}>
                <td><RankPill position={position} official={row.rank} filtered={filtered} /></td>
                <td>{row.name}</td>
                <td>{fmt(row.year_of_birth)}</td>
                <td>{row.club ?? "-"}</td>
                <td>{row.country ?? "-"}</td>
                <td className={styles.num}>{fmt(row.total_score)}</td>
                <td className={styles.num}>{fmt(row.penalty)}</td>
                <td className={styles.num}>{fmt(row.points_behind)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
