import { NavLink, Outlet } from "react-router-dom";
import styles from "./Shell.module.css";

const NAV = [
  { to: "/", label: "Home", end: true },
  { to: "/competitions", label: "Competitions" },
  { to: "/figures", label: "Figures" },
  { to: "/athletes", label: "Athletes" },
  { to: "/clubs", label: "Clubs" },
];

export function Shell() {
  return (
    <div className={styles.shell}>
      <nav className={styles.nav} aria-label="Main">
        <div className={styles.brand}>Aquabely</div>
        {NAV.map((n) => (
          <NavLink
            key={n.to}
            to={n.to}
            end={n.end}
            className={({ isActive }) => `${styles.link} ${isActive ? styles.active : ""}`}
          >
            {n.label}
          </NavLink>
        ))}
      </nav>
      <main className={styles.main}>
        <Outlet />
      </main>
    </div>
  );
}
