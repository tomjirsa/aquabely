import { defineConfig } from "@playwright/test";
import { tmpdir } from "node:os";
import { join } from "node:path";

// Temporary database and inbox, never the user's real ones.
const dir = join(tmpdir(), "aquabely-e2e");
const db = join(dir, "e2e.db");
const inbox = join(dir, "inbox");
const env = { ...process.env, AQUABELY_DB: db, AQUABELY_INBOX: inbox, AQUABELY_API_URL: "http://localhost:8765" } as Record<string, string>;

export default defineConfig({
  testDir: "e2e",
  fullyParallel: false,
  workers: 1,
  reporter: [["list"]],
  outputDir: "test-results",
  use: { baseURL: "http://localhost:4173" },
  webServer: [
    {
      // seed the temp database, then serve the API from it
      command: `python scripts/seed_e2e.py "${db}" && python -m uvicorn api.main:app --port 8765`,
      cwd: "..",
      url: "http://localhost:8765/api/health",
      reuseExistingServer: false,
      env,
      timeout: 60_000,
    },
    {
      // vite preview proxies /api to the API (server.proxy is inherited); AQUABELY_API_URL points it at 8765, since 8000 may be in use
      command: "npx vite build && npx vite preview --port 4173 --strictPort",
      url: "http://localhost:4173",
      reuseExistingServer: false,
      env,
      timeout: 120_000,
    },
  ],
});
