import { expect, test, type Page } from "@playwright/test";

// Known exception: Google Fonts may fail to load in a sandboxed headless run;
// that surfaces as a console error about a failed resource, which we ignore.
const IGNORED = [/fonts\.googleapis\.com/, /fonts\.gstatic\.com/, /ERR_(NAME_NOT_RESOLVED|INTERNET_DISCONNECTED|CONNECTION)/];

const VIEWPORTS = [
  { name: "1280", width: 1280, height: 800 },
  { name: "390", width: 390, height: 844 },
];

function trackErrors(page: Page): string[] {
  const errors: string[] = [];
  page.on("console", (m) => {
    if (m.type() !== "error") return;
    const text = `${m.text()} ${m.location().url}`;
    if (IGNORED.some((r) => r.test(text))) return;
    errors.push(m.text());
  });
  page.on("pageerror", (e) => errors.push(String(e)));
  return errors;
}

async function finish(page: Page, name: string, vw: { name: string; width: number }, errors: string[]) {
  await page.screenshot({ path: `e2e/screenshots/${name}-${vw.name}.png`, fullPage: true });
  if (vw.width <= 400) {
    const fits = await page.evaluate(
      () => document.documentElement.scrollWidth <= document.documentElement.clientWidth,
    );
    expect(fits, "no horizontal page scroll at 390px").toBe(true);
  }
  expect(errors, "console errors").toEqual([]);
}

for (const vw of VIEWPORTS) {
  test.describe(`viewport ${vw.name}`, () => {
    test.use({ viewport: { width: vw.width, height: vw.height } });

    test("home shows latest competition summary", async ({ page }) => {
      const errors = trackErrors(page);
      await page.goto("/");
      await expect(page.getByRole("heading", { name: "Home" })).toBeVisible();
      await expect(page.getByRole("heading", { name: "Athletes" })).toBeVisible();
      await expect(page.getByRole("heading", { name: "Top scorer" })).toBeVisible();
      await finish(page, "home", vw, errors);
    });

    test("competitions: select competition shows results and figure detail", async ({ page }) => {
      const errors = trackErrors(page);
      await page.goto("/competitions");
      const select = page.getByLabel("Competition", { exact: true });
      await expect(select.locator("option")).toHaveCount(2);
      await select.selectOption({ index: 1 });
      await expect(page.getByRole("heading", { name: "Results" })).toBeVisible();
      await expect(page.getByRole("columnheader", { name: "Total score" })).toBeVisible();
      await expect(page.getByRole("heading", { name: "Figure detail" })).toBeVisible();
      await expect(page.getByRole("cell", { name: "Bea" }).first()).toBeVisible();
      await finish(page, "competitions", vw, errors);
    });

    test("figures shows catalogue table", async ({ page }) => {
      const errors = trackErrors(page);
      await page.goto("/figures");
      await expect(page.getByRole("heading", { name: "Figures" })).toBeVisible();
      await expect(page.locator("table")).toBeVisible();
      await expect(page.locator("tbody tr").first()).toBeVisible();
      await finish(page, "figures", vw, errors);
    });

    test("athletes list, search and profile", async ({ page }) => {
      const errors = trackErrors(page);
      await page.goto("/athletes");
      await expect(page.getByRole("heading", { name: "Athletes" })).toBeVisible();
      await expect(page.locator("table")).toBeVisible();
      await page.getByLabel("Search athletes").fill("Bea");
      await page.getByRole("cell", { name: "Bea" }).click();
      await expect(page.getByRole("heading", { name: /Bea/ })).toBeVisible();
      await expect(page.getByRole("tablist", { name: "Athlete sections" })).toBeVisible();
      await finish(page, "athlete-profile", vw, errors);
    });

    test("clubs list and detail", async ({ page }) => {
      const errors = trackErrors(page);
      await page.goto("/clubs");
      await expect(page.getByRole("heading", { name: "Clubs" })).toBeVisible();
      await page.getByRole("link", { name: /Club L/ }).click();
      await expect(page.getByRole("heading", { name: "Roster" })).toBeVisible();
      await expect(page.getByRole("heading", { name: "Medals" })).toBeVisible();
      await finish(page, "clubs", vw, errors);
    });

    test("import page offers file upload", async ({ page }) => {
      const errors = trackErrors(page);
      await page.goto("/import");
      await expect(page.getByRole("heading", { name: "Import" })).toBeVisible();
      await expect(page.locator('input[type="file"]')).toBeAttached();
      await finish(page, "import", vw, errors);
    });
  });
}
