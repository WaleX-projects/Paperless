import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { API, Exam, Sub, api } from "./api";

export default function App() {
  const [exams, setExams] = useState<Exam[]>([]);
  const [exam, setExam] = useState<Exam | null>(null);
  const [subs, setSubs] = useState<Sub[]>([]);
  const [sel, setSel] = useState<number | null>(null);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({ title: "", total_marks: "", marking_scheme: "" });
  const [stage, setStage] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const uploadRef = useRef<HTMLInputElement>(null);
  const snapRef = useRef<HTMLInputElement>(null);

  const loadExams = () => api<Exam[]>("/exams").then(setExams);
  const loadSubs = useCallback(() => exam && api<Sub[]>(`/exams/${exam.id}/submissions`).then(setSubs), [exam]);

  useEffect(() => { loadExams(); }, []);
  useEffect(() => { setSel(null); setSubs([]); loadSubs(); }, [exam]);
  useEffect(() => {
    if (!subs.some((s) => s.status === "pending" || s.status === "processing")) return;
    const t = setInterval(loadSubs, 3000);
    return () => clearInterval(t);
  }, [subs, loadSubs]);
  useEffect(() => {
    const h = (e: KeyboardEvent) => { if (e.key === "Escape") { setSel(null); setStage(false); } };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, []);

  const previews = useMemo(() => files.map((f) => URL.createObjectURL(f)), [files]);
  useEffect(() => () => previews.forEach((u) => URL.revokeObjectURL(u)), [previews]);

  async function createExam() {
    const e = await api<Exam>("/exams", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...form, total_marks: Number(form.total_marks) || 0 }) });
    setForm({ title: "", total_marks: "", marking_scheme: "" });
    await loadExams(); setExam(e); setCreating(false);
  }

  function addFiles(e: React.ChangeEvent<HTMLInputElement>) {
    const list = Array.from(e.target.files ?? []);
    e.target.value = "";
    if (!list.length) return;
    setFiles((f) => [...f, ...list]);
    setStage(true);
  }

  function closeStage() { setStage(false); setFiles([]); setName(""); }

  async function upload() {
    if (!exam || !files.length) return;
    setBusy(true);
    const fd = new FormData();
    files.forEach((f) => fd.append("files", f));
    if (name) fd.append("student_name", name);
    try { await api(`/exams/${exam.id}/submissions`, { method: "POST", body: fd }); closeStage(); await loadSubs(); }
    finally { setBusy(false); }
  }

  async function override(s: Sub, number: string, awarded: number) {
    const u = await api<Sub>(`/submissions/${s.id}/questions/${encodeURIComponent(number)}`, {
      method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ awarded }) });
    setSubs((xs) => xs.map((x) => (x.id === u.id ? u : x)));
  }

  const retry = (s: Sub) => api(`/submissions/${s.id}/regrade`, { method: "POST" }).then(loadSubs);
  const cur = subs.find((s) => s.id === sel);
  const pct = (s: Sub) => (s.score != null && s.total ? Math.round((s.score / s.total) * 100) : 0);
  const tone = (p: number) => (p >= 70 ? "good" : p >= 40 ? "mid" : "low");
  const thumb = (s: Sub) => (s.pages[0] ? `${API}/pages/${s.pages[0].id}/image?annotated=true&v=${s.updated_at}` : "");
  const doneCount = subs.filter((s) => s.status === "done").length;

  return (
    <div className="app">
      <input ref={uploadRef} type="file" accept="image/*" multiple hidden onChange={addFiles} />
      <input ref={snapRef} type="file" accept="image/*" capture="environment" hidden onChange={addFiles} />

      <aside className="side">
        <div className="brand"><span className="dot" />Grading System</div>

        {creating ? (
          <div className="create">
            <input autoFocus placeholder="Class name" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
            <input placeholder="Total marks" type="number" value={form.total_marks} onChange={(e) => setForm({ ...form, total_marks: e.target.value })} />
            <textarea rows={7} placeholder={"Marking scheme / answer key\n1. B (1 mark)\n2. Photosynthesis... (3 marks)"}
              value={form.marking_scheme} onChange={(e) => setForm({ ...form, marking_scheme: e.target.value })} />
            <div className="row2">
              <button className="btn ghost" onClick={() => setCreating(false)}>Cancel</button>
              <button className="btn" onClick={createExam} disabled={!form.title || !form.marking_scheme}>Create</button>
            </div>
          </div>
        ) : (
          <button className="btn new" onClick={() => setCreating(true)}>＋ Create a class</button>
        )}

        <div className="label">Classes</div>
        <nav>
          {exams.map((e) => (
            <button key={e.id} className={"nav" + (exam?.id === e.id ? " on" : "")} onClick={() => { setExam(e); setCreating(false); }}>
              {e.title}
            </button>
          ))}
          {!exams.length && <p className="hint">No classes yet</p>}
        </nav>
      </aside>

      <main className="main">
        {!exam ? (
          <div className="empty">
            <div className="empty-ico">✦</div>
            <h2>Welcome</h2>
            <p>Create a class or pick one from the sidebar to start grading scripts.</p>
          </div>
        ) : (
          <>
            <header className="head">
              <div>
                <h1>{exam.title}</h1>
                <p className="sub">{exam.total_marks} marks · {subs.length} script{subs.length === 1 ? "" : "s"} · {doneCount} graded</p>
              </div>
              <a className="btn ghost" href={`${API}/exams/${exam.id}/export.csv`}>Export CSV</a>
            </header>

            <section className="actions">
              <button className="action" onClick={() => uploadRef.current?.click()}>
                <span className="a-ico">⬆</span><b>Upload</b><small>Choose script images from your device</small>
              </button>
              <button className="action" onClick={() => snapRef.current?.click()}>
                <span className="a-ico">📷</span><b>Snap</b><small>Take a photo of each page</small>
              </button>
              <button className="action off" disabled>
                <span className="a-ico">🖨</span><b>Scanner</b><small>Coming soon with the desktop app</small>
              </button>
            </section>

            <section className="grid">
              {subs.map((s) => {
                const loading = s.status === "pending" || s.status === "processing";
                return (
                  <article key={s.id} className={"card " + s.status} onClick={() => s.status === "done" && setSel(s.id)}>
                    <div className={"thumb" + (loading ? " loading" : "")}>
                      {thumb(s) && <img src={thumb(s)} alt="" />}
                      {loading && <span className="chip">{s.status === "pending" ? "Queued" : "Grading…"}</span>}
                      {s.status === "failed" && (
                        <button className="retry" onClick={(e) => { e.stopPropagation(); retry(s); }}>
                          <span>↻</span>Retry
                        </button>
                      )}
                      {s.status === "done" && <span className={"score " + tone(pct(s))}>{pct(s)}%</span>}
                    </div>
                    <div className="meta">
                      <b>{s.student_name || `Script #${s.id}`}</b>
                      <span>{s.status === "done" ? `${s.score} / ${s.total}` : s.status === "failed" ? "Failed" : "…"}</span>
                    </div>
                  </article>
                );
              })}
              {!subs.length && <p className="hint wide">No scripts yet. Upload or snap the first one above.</p>}
            </section>
          </>
        )}
      </main>

      {stage && (
        <div className="overlay" onClick={closeStage}>
          <div className="modal small" onClick={(e) => e.stopPropagation()}>
            <h3>New script</h3>
            <p className="sub">One script = one student. Pages should be in order.</p>
            <input placeholder="Student name (optional, AI reads it from the paper)" value={name} onChange={(e) => setName(e.target.value)} />
            <div className="strip">
              {previews.map((u, i) => (
                <div key={u} className="pg">
                  <img src={u} alt="" /><span className="n">{i + 1}</span>
                  <button className="x" onClick={() => setFiles((f) => f.filter((_, j) => j !== i))}>×</button>
                </div>
              ))}
              <button className="pg add" onClick={() => snapRef.current?.click()}>＋<small>Snap</small></button>
              <button className="pg add" onClick={() => uploadRef.current?.click()}>＋<small>File</small></button>
            </div>
            <div className="row2">
              <button className="btn ghost" onClick={closeStage}>Cancel</button>
              <button className="btn" onClick={upload} disabled={busy || !files.length}>{busy ? "Uploading…" : `Grade ${files.length} page${files.length === 1 ? "" : "s"}`}</button>
            </div>
          </div>
        </div>
      )}

      {cur && (
        <div className="overlay" onClick={() => setSel(null)}>
          <div className="modal big" onClick={(e) => e.stopPropagation()}>
            <button className="close" onClick={() => setSel(null)}>×</button>
            <div className="d-head">
              <div>
                <h2>{cur.student_name || `Script #${cur.id}`}</h2>
                <p className="sub">{exam?.title}</p>
              </div>
              {cur.score != null && (
                <div className={"big-score " + tone(pct(cur))}>
                  <b>{cur.score}<small>/{cur.total}</small></b><span>{pct(cur)}%</span>
                </div>
              )}
            </div>
            {cur.error && <p className="err">{cur.error}</p>}
            <div className="d-body">
              <div className="d-pages">
                {cur.pages.map((p) => <img key={p.id} src={`${API}/pages/${p.id}/image?annotated=true&v=${cur.updated_at}`} alt="" />)}
              </div>
              <div className="d-qs">
                {cur.questions.map((q) => {
                  const st = q.correct ? "ok" : q.awarded > 0 ? "part" : "bad";
                  return (
                    <div key={q.number} className={"q " + st}>
                      <div className="q-top">
                        <span className="q-num">Q{q.number}</span>
                        <span className="q-marks">
                          <input type="number" step="0.5" defaultValue={q.awarded} key={q.awarded}
                            onBlur={(e) => Number(e.target.value) !== q.awarded && override(cur, q.number, Number(e.target.value))} />
                          <span>/ {q.max_marks}</span>
                        </span>
                      </div>
                      <div className="q-ans">{q.student_answer || "—"}</div>
                      {q.feedback && <div className="q-fb">{q.feedback}</div>}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}