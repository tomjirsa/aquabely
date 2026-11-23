import styles from "./RankPill.module.css";

interface Props {
  position: number;
  official: number | null;
  filtered: boolean;
}

function tone(position: number): string {
  if (position === 1) return styles.gold;
  if (position === 2) return styles.silver;
  if (position === 3) return styles.bronze;
  return styles.plain;
}

export function RankPill({ position, official, filtered }: Props) {
  if (!filtered) {
    return (
      <span className={styles.pill}>
        <span data-testid="rank-position" className={`${styles.half} ${styles.solo} ${tone(position)}`}>
          {position}
        </span>
      </span>
    );
  }
  return (
    <span className={styles.pill}>
      <span data-testid="rank-position" className={`${styles.half} ${styles.left} ${tone(position)}`}>
        {position}
      </span>
      <span data-testid="rank-official" className={`${styles.half} ${styles.right}`}>
        {official ?? "-"}
      </span>
    </span>
  );
}
