import { Route, Routes } from "react-router-dom";
import { Shell } from "./components/Shell";
import { HomePage } from "./pages/Home/HomePage";
import { CompetitionsPage } from "./pages/Competitions/CompetitionsPage";
import { FiguresPage } from "./pages/Figures/FiguresPage";
import { AthletesPage } from "./pages/Athletes/AthletesPage";
import { AthleteProfilePage } from "./pages/Athletes/AthleteProfilePage";
import { ClubsPage } from "./pages/ClubsPage";
import { ClubDetailPage } from "./pages/ClubDetailPage";
import { ImportPage } from "./pages/ImportPage";

export function App() {
  return (
    <Routes>
      <Route element={<Shell />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/competitions" element={<CompetitionsPage />} />
        <Route path="/figures" element={<FiguresPage />} />
        <Route path="/athletes" element={<AthletesPage />} />
        <Route path="/athletes/:id" element={<AthleteProfilePage />} />
        <Route path="/clubs" element={<ClubsPage />} />
        <Route path="/clubs/:id" element={<ClubDetailPage />} />
        <Route path="/import" element={<ImportPage />} />
      </Route>
    </Routes>
  );
}
