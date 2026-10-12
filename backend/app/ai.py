import base64
import json

import cv2
from openai import OpenAI

from .config import settings
import base64

client = OpenAI(
    base_url="https://api.tokenfactory.us-central1.nebius.com/v1/",
    api_key="v1.CmQKHHN0YXRpY2tleS1lMDB5YXQ2NW1xbWZmdnhucWESIXNlcnZpY2VhY2NvdW50LWUwMHozMnpxbXMzdjI5ZTY4ZTIMCOLJo9YGENmByfABOgwI4My7oQcQgI-XwQNAAloDZTAw.AAAAAAAAAAEICzscR0e0KwyhAPKdxKVee_goOEsD3CuiqRzctH8jqc7T9ln9IvmVgB_vhane2TsbaQcIIqFu91nSJD8TlLsM")


_q = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "number", "student_answer", "awarded", "max_marks",
        "verdict", "confidence", "needs_review",
        "feedback", "page", "x", "y",
    ],
    "properties": {
        "number": {"type": "string", "description": "Question number, e.g. 2a"},
        "student_answer": {"type": "string"},
        "awarded": {"type": "number"},
        "max_marks": {"type": "number"},
        "verdict": {
            "type": "string",
            "enum": ["correct", "partial", "wrong", "blank"],
        },
        "confidence": {
            "type": "number",
            "description": "0 to 1, how sure you are of this mark",
        },
        "needs_review": {
            "type": "boolean",
            "description": "True if handwriting is unclear or the answer is borderline",
        },
        "feedback": {"type": "string", "description": "One short sentence"},
        "page": {"type": "integer", "description": "1-based page index"},
        "x": {"type": "number", "description": "0-1 from left"},
        "y": {"type": "number", "description": "0-1 from top"},
    },
}

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["student_name", "questions"],
    "properties": {
        "student_name": {"type": "string"},
        "questions": {"type": "array", "items": _q},
    },
}


SYSTEM = """
You are an exam marker.

You receive scanned pages of ONE student's paper, in order, together with the marking scheme.

For every question in the marking scheme:

1. Read the student's answer.
2. Award marks using the marking scheme.
3. Partial credit is allowed.
4. Never award more than the maximum marks.
5. Give one short feedback sentence.
6. Return the page number where the answer appears.
7. Return normalized x and y coordinates from 0 to 1.
8. The coordinates should point to the empty margin immediately to the right of the student's answer.
9. If the margin is full, place the coordinates beside the question number.
10. If the student left the question blank, award 0 and place the coordinates where the answer should be.
11. Set verdict to correct (full marks), partial, wrong (0 marks) or blank.
12. Set confidence from 0 to 1. Set needs_review to true if the writing is hard to read or the answer is borderline.
Also identify the student's name if it is written on the paper.

If no name is visible, return an empty string.

Return ONLY the JSON object matching the supplied JSON schema.
"""


def _data_url(path: str) -> str:
    image = cv2.imread(path)

    if image is None:
        raise ValueError(f"Could not read image: {path}")

    ok, buf = cv2.imencode(
        ".jpg",
        image,
        [cv2.IMWRITE_JPEG_QUALITY, 85],
    )

    if not ok:
        raise ValueError(f"Could not encode image: {path}")

    return (
        "data:image/jpeg;base64,"
        + base64.b64encode(buf.tobytes()).decode()
    )


def grade_pages(
    paths: list[str],
    scheme: str,
    total_marks: float,
) -> dict:
    print(f"Grading {len(paths)} pages with total marks {total_marks}")
    content = [
        {
            "type": "text",
            "text": (
                f"MARKING SCHEME (total {total_marks}):\n"
                f"{scheme}"
            ),
        }
    ]

    for i, path in enumerate(paths, 1):
        content.append(
            {
                "type": "text",
                "text": f"Page {i}:",
            }
        )

        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": _data_url(path),
                    "detail": "high",
                },
            }
        )

    resp = client.chat.completions.create(
        model="Qwen/Qwen3.8-27B",
        
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": SYSTEM,
            },
            {
                "role": "user",
                "content": content,
            },
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "grading",
                "strict": True,
                "schema": SCHEMA,
            },
        },
    )

    raw = resp.choices[0].message.content

    print("========== NEBIUS RESPONSE ==========")
    print(raw)
    print("=====================================")

    if not raw:
        raise ValueError("Nebius returned an empty response")

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Nebius returned invalid JSON: {raw[:1000]}"
        ) from e