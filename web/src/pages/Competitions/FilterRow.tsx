import type { FilterKey, Filters } from "../../lib/filters";
import styles from "./CompetitionsPage.module.css";

interface Props {
  filters: Filters;
  onChange: (key: FilterKey, value: string) => void;
}

const CELLS: { key: FilterKey | null; label: string; placeholder: string }[] = [
  { key: null, label: "", placeholder: "" },
  { key: "name", label: "Name", placeholder: "Filter" },
  { key: "born", label: "Born", placeholder: "Year" },
  { key: "club", label: "Club", placeholder: "Filter" },
  { key: "country", label: "Country", placeholder: "Filter" },
  { key: "score", label: "Total score", placeholder: "Min - max" },
  { key: "penalty", label: "Penalty", placeholder: "Min - max" },
  { key: "behind", label: "Points behind", placeholder: "Min - max" },
];

export function FilterRow({ filters, onChange }: Props) {
  return (
    <tr className={styles.filterRow}>
      {CELLS.map((c, i) => (
        <td key={i}>
          {c.key && (
            <input
              className={styles.filterInput}
              aria-label={`Filter ${c.label}`}
              placeholder={c.placeholder}
              value={filters[c.key]}
              onChange={(e) => onChange(c.key as FilterKey, e.target.value)}
            />
          )}
        </td>
      ))}
    </tr>
  );
}
