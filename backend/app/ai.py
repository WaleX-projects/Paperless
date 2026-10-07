import base64
import json
import cv2
from openai import OpenAI
from .config import settings

client = OpenAI(
    base_url=settings.openai_base_url,
    api_key=settings.openai_api_key
    )

_q = {
    "type": "object",
    "additionalProperties": False,
    "required": ["number", "student_answer", "awarded", "max_marks", "feedback", "page", "x", "y"],
    "properties": {
        "number": {"type": "string"},
        "student_answer": {"type": "string"},
        "awarded": {"type": "number"},
        "max_marks": {"type": "number"},
        "feedback": {"type": "string"},
        "page": {"type": "integer", "description": "1-based page index"},
        "x": {"type": "number", "description": "0-1 from left"},
        "y": {"type": "number", "description": "0-1 from top"},
    },
}
SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["student_name", "questions"],
    "properties": {"student_name": {"type": "string"}, "questions": {"type": "array", "items": _q}},
}

SYSTEM = """You are an exam marker. You receive scanned pages of ONE student's paper (in order) and the marking scheme.
For every question in the scheme: read the student's answer, award marks (partial credit allowed, never above max_marks), and give one short feedback sentence.
For each question also return where the mark should be drawn: the page number and normalized coordinates x,y (0-1, origin top-left of THAT page image),
pointing at the empty margin just to the right of the student's answer for that question (or just beside the question number if the margin is full).
If the student left a question blank, award 0 and place the mark where the answer should be. student_name: the name written on the paper, or "" if none."""


def _data_url(path: str) -> str:
    ok, buf = cv2.imencode(".jpg", cv2.imread(path), [cv2.IMWRITE_JPEG_QUALITY, 85])
    return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode()


def grade_pages(paths: list[str], scheme: str, total_marks: float) -> dict:
    content = [{"type": "text", "text": f"MARKING SCHEME (total {total_marks}):\n{scheme}"}]
    for i, p in enumerate(paths, 1):
        content.append({"type": "text", "text": f"Page {i}:"})
        content.append({"type": "image_url", "image_url": {"url": _data_url(p), "detail": "high"}})
    resp = client.chat.completions.create(
        model=settings.openai_model,
        temperature=0,
        messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": content}],
        response_format={"type": "json_schema", "json_schema": {"name": "grading", "strict": True, "schema": SCHEMA}},
    )
    return json.loads(resp.choices[0].message.content)
