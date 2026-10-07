export const API = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";
export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(API + path, init);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}
export type Q = { number: string; student_answer: string; correct: boolean; awarded: number; max_marks: number; feedback: string; page: number };
export type Sub = { id: number; student_name: string | null; status: string; score: number | null; total: number | null; error: string | null; pages: { id: number }[]; questions: Q[]; updated_at: string };
export type Exam = { id: number; title: string; total_marks: number; marking_scheme: string };
