import { useCallback, useEffect, useState } from "react";
import { API, Exam, Sub, api } from "./api";

export default function App() {
  const [exams, setExams] = useState<Exam[]>([]);
  const [exam, setExam] = useState<Exam | null>(null);
  const [subs, setSubs] = useState<Sub[]>([]);
  const [sel, setSel] = useState<number | null>(null);
  const [form, setForm] = useState({ title: "", total_marks: "", marking_scheme: "" });
  const [files, setFiles] = useState<File[]>([]);
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);

  const loadExams = () => api<Exam[]>("/exams").then(setExams);
  const loadSubs = useCallback(() => exam && api<Sub[]>(`/exams/${exam.id}/submissions`).then(setSubs), [exam]);

  useEffect(() => { loadExams(); }, []);
  useEffect(() => { setSel(null); setSubs([]); loadSubs(); }, [exam]);
  useEffect(() => {
    if (!subs.some((s) => s.status === "pending" || s.status === "processing")) return;
    const t = setInterval(loadSubs, 3000);
    return () => clearInterval(t);
  }, [subs, loadSubs]);

  async function createExam() {
    const e = await api<Exam>("/exams", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...form, total_marks: Number(form.total_marks) || 0 }) });
    setForm({ title: "", total_marks: "", marking_scheme: "" });
    await loadExams(); setExam(e);
  }

  async function upload() {
    if (!exam || !files.length) return;
    setBusy(true);
    const fd = new FormData();
    files.forEach((f) => fd.append("files", f));
    if (name) fd.append("student_name", name);
    try { await api(`/exams/${exam.id}/submissions`, { method: "POST", body: fd }); setFiles([]); setName(""); await loadSubs(); }
    finally { setBusy(false); }
  }

  async function override(s: Sub, number: string, awarded: number) {
    const u = await api<Sub>(`/submissions/${s.id}/questions/${encodeURIComponent(number)}`, {
      method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ awarded }) });
    setSubs((xs) => xs.map((x) => (x.id === u.id ? u : x)));
  }

  const cur = subs.find((s) => s.id === sel);

  return (
    <div className="wrap">
      <aside>
        <h3>Exams</h3>
        {exams.map((e) => (
          <div key={e.id} className={"item" + (exam?.id === e.id ? " on" : "")} onClick={() => setExam(e)}>{e.title}</div>
        ))}
        <h3 style={{ marginTop: 20 }}>New exam</h3>
        <input placeholder="Title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
        <input placeholder="Total marks" type="number" value={form.total_marks} onChange={(e) => setForm({ ...form, total_marks: e.target.value })} />
        <textarea rows={8} placeholder={"Marking scheme / answer key\n1. B (1 mark)\n2. Photosynthesis... (3 marks)"}
          value={form.marking_scheme} onChange={(e) => setForm({ ...form, marking_scheme: e.target.value })} />
        <button onClick={createExam} disabled={!form.title || !form.marking_scheme}>Create exam</button>
      </aside>

      <main>
        {!exam ? <p>Select or create an exam.</p> : (
          <>
            <div className="card">
              <h3>{exam.title}: upload scripts</h3>
              <input placeholder="Student name (optional, AI reads it from the paper otherwise)" value={name} onChange={(e) => setName(e.target.value)} />
              <input type="file" accept="image/*" multiple onChange={(e) => setFiles(Array.from(e.target.files ?? []))} />
              <small>{files.length} page(s) selected: one upload = one student's paper, pages in order.</small>
              <button style={{ marginTop: 8 }} onClick={upload} disabled={busy || !files.length}>{busy ? "Uploading…" : "Upload & grade"}</button>
              <a href={`${API}/exams/${exam.id}/export.csv`}><button className="sec" type="button">Export CSV</button></a>
            </div>

            <div className="card">
              <table>
                <thead><tr><th>Student</th><th>Status</th><th>Score</th></tr></thead>
                <tbody>
                  {subs.map((s) => (
                    <tr key={s.id} className="item" style={{ display: "table-row" }} onClick={() => setSel(s.id)}>
                      <td>{s.student_name || `Script #${s.id}`}</td>
                      <td><span className={"badge " + s.status}>{s.status}</span></td>
                      <td>{s.score != null ? `${s.score} / ${s.total}` : "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {cur && (
              <div className="card">
                <h3>{cur.student_name || `Script #${cur.id}`} {cur.score != null && `: ${cur.score}/${cur.total}`}</h3>
                {cur.error && <p style={{ color: "crimson" }}>{cur.error}</p>}
                {cur.status === "failed" && <button onClick={() => api(`/submissions/${cur.id}/regrade`, { method: "POST" }).then(loadSubs)}>Retry</button>}
                <div className="pages">
                  {cur.pages.map((p) => <img key={p.id} src={`${API}/pages/${p.id}/image?annotated=true&v=${cur.updated_at}`} />)}
                </div>
                {cur.questions.length > 0 && (
                  <table style={{ marginTop: 14 }}>
                    <thead><tr><th>Q</th><th>Student answer</th><th>Marks</th><th>Feedback</th></tr></thead>
                    <tbody>
                      {cur.questions.map((q) => (
                        <tr key={q.number}>
                          <td>{q.number}</td><td>{q.student_answer}</td>
                          <td><input type="number" step="0.5" defaultValue={q.awarded} key={q.awarded}
                            onBlur={(e) => Number(e.target.value) !== q.awarded && override(cur, q.number, Number(e.target.value))} /> / {q.max_marks}</td>
                          <td>{q.feedback}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
