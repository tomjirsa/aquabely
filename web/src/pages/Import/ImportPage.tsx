import { useState } from "react";
import { ApiError, apiPost, apiPostForm } from "../../api/client";
import type { ImportPreview, ImportRequest, ImportResult } from "../../api/types";
import styles from "./ImportPage.module.css";

const MAX_BYTES = 50 * 1024 * 1024;
const TOO_LARGE = "File exceeds 50 MB";

interface Item {
  key: number;
  name: string;
  file?: File;
  preview?: ImportPreview;
  formatId: string;
  busy: boolean;
  /** Token of the latest preview request; older responses are ignored. */
  previewToken: number;
  /** The latest preview request failed, so the shown preview is out of date. */
  previewFailed: boolean;
  outcome?: { ok: boolean; text: string };
}

let nextKey = 0;
let nextToken = 0;

function previewForm(file: File, formatId?: string): FormData {
  const form = new FormData();
  form.append("file", file);
  if (formatId) form.append("format_id", formatId);
  return form;
}

function importError(e: unknown): string {
  if (e instanceof ApiError) {
    if (e.status === 409) return "Already imported.";
    if (e.status === 422) {
      const errs = (e.body as { errors?: unknown } | undefined)?.errors;
      if (Array.isArray(errs) && errs.length) return errs.map(String).join("; ");
    }
    return e.message;
  }
  return "Import failed.";
}

export function ImportPage() {
  const [items, setItems] = useState<Item[]>([]);

  const patch = (key: number, p: Partial<Item>) =>
    setItems((cur) => cur.map((i) => (i.key === key ? { ...i, ...p } : i)));

  // Apply a preview result only if it answers the item's latest request.
  const patchIfLatest = (key: number, token: number, p: Partial<Item>) =>
    setItems((cur) =>
      cur.map((i) => (i.key === key && i.previewToken === token ? { ...i, ...p } : i)),
    );

  async function runPreview(key: number, file: File, formatId?: string) {
    const token = nextToken++;
    patch(key, { busy: true, previewToken: token, previewFailed: false, outcome: undefined });
    try {
      const preview = await apiPostForm<ImportPreview>(
        "/api/imports/preview",
        previewForm(file, formatId),
      );
      patchIfLatest(key, token, {
        preview,
        formatId: formatId ?? preview.format_id ?? "",
        busy: false,
      });
    } catch (e) {
      patchIfLatest(key, token, {
        busy: false,
        previewFailed: true,
        outcome: { ok: false, text: e instanceof Error ? e.message : "Preview failed." },
      });
    }
  }

  function chooseFormat(item: Item, formatId: string) {
    patch(item.key, { formatId, outcome: undefined });
    // Re-parse and re-validate the stored upload with the chosen format.
    if (formatId !== "" && item.file) void runPreview(item.key, item.file, formatId);
  }

  async function addFile(file: File) {
    const key = nextKey++;
    if (file.size > MAX_BYTES) {
      setItems((cur) => [
        ...cur,
        {
          key, name: file.name, formatId: "", busy: false, previewToken: -1, previewFailed: false,
          outcome: { ok: false, text: TOO_LARGE },
        },
      ]);
      return;
    }
    setItems((cur) => [
      ...cur,
      { key, name: file.name, file, formatId: "", busy: true, previewToken: -1, previewFailed: false },
    ]);
    await runPreview(key, file);
  }

  async function runImport(item: Item) {
    if (!item.preview) return;
    const body: ImportRequest = {
      sha256: item.preview.sha256,
      filename: item.preview.filename,
      format_id: item.formatId,
    };
    patch(item.key, { busy: true, outcome: undefined });
    try {
      const res = await apiPost<ImportResult>("/api/imports", body);
      const lvl = res.level ? ` (${res.level})` : "";
      patch(item.key, { busy: false, outcome: { ok: true, text: `Imported ${res.athlete_count} athletes${lvl}.` } });
    } catch (e) {
      patch(item.key, { busy: false, outcome: { ok: false, text: importError(e) } });
    }
  }

  return (
    <div className={styles.page}>
      <h1>Import</h1>
      <label className={styles.picker}>
        Choose PDF files
        <input
          type="file"
          accept="application/pdf,.pdf"
          multiple
          onChange={(e) => {
            Array.from(e.target.files ?? []).forEach((f) => void addFile(f));
            e.target.value = "";
          }}
        />
      </label>
      {items.map((item) => {
        const p = item.preview;
        // When the user picked a format by hand, detection failures no longer block;
        // every other preview error still does.
        const blocking = p
          ? item.formatId !== "" && p.format_id === null
            ? p.errors.filter((e) => !e.startsWith("Could not detect the format"))
            : p.errors
          : [];
        const canImport =
          !!p &&
          blocking.length === 0 &&
          item.formatId !== "" &&
          !item.busy &&
          !item.previewFailed &&
          !item.outcome?.ok;
        const parsed = !!p && (p.level !== null || p.competition !== null);
        return (
          <section key={item.key} className={styles.card}>
            <h2>{item.name}</h2>
            {item.busy && !p && <p className={styles.muted}>Reading...</p>}
            {p && (
              <>
                <dl className={styles.facts}>
                  <dt>Format</dt>
                  <dd>
                    <select
                      aria-label="Format"
                      value={item.formatId}
                      disabled={item.busy}
                      onChange={(e) => chooseFormat(item, e.target.value)}
                    >
                      {item.formatId === "" && <option value="">Choose format</option>}
                      {p.available_formats.map((f) => (
                        <option key={f} value={f}>
                          {f}
                        </option>
                      ))}
                    </select>
                    {item.busy && <span className={styles.muted}> Checking...</span>}
                  </dd>
                  {p.level && (
                    <>
                      <dt>Level</dt>
                      <dd>{p.level}</dd>
                    </>
                  )}
                  {p.competition && (
                    <>
                      <dt>Competition</dt>
                      <dd>{p.competition}</dd>
                    </>
                  )}
                  {parsed && (
                    <>
                      <dt>Athletes</dt>
                      <dd>{p.athlete_count}</dd>
                    </>
                  )}
                </dl>
                {p.errors.length > 0 && (
                  <ul className={styles.errors}>
                    {p.errors.map((m, i) => (
                      <li key={i}>{m}</li>
                    ))}
                  </ul>
                )}
                {p.warnings.length > 0 && (
                  <details className={styles.warnings}>
                    <summary>Warnings ({p.warnings.length})</summary>
                    <ul>
                      {p.warnings.map((m, i) => (
                        <li key={i}>{m}</li>
                      ))}
                    </ul>
                  </details>
                )}
                <button
                  type="button"
                  className={styles.button}
                  disabled={!canImport}
                  onClick={() => void runImport(item)}
                >
                  Import
                </button>
              </>
            )}
            {item.outcome && (
              <p role="status" className={item.outcome.ok ? styles.ok : styles.error}>
                {item.outcome.text}
              </p>
            )}
          </section>
        );
      })}
    </div>
  );
}
