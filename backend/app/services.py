from pathlib import Path
from sqlalchemy.orm.attributes import flag_modified
from .imaging import annotate




def recompute(sub) -> None:
    if not sub.result:
        raise ValueError("Submission has no grading result")

    qs = sub.result.get("questions", [])

    total_awarded = 0.0
    total_possible = 0.0

    for q in qs:
        awarded = float(q.get("awarded", 0))
        max_marks = float(q.get("max_marks", 0))

        awarded = max(
            0.0,
            min(awarded, max_marks),
        )

        q["awarded"] = awarded
        q["max_marks"] = max_marks
        q["correct"] = awarded >= max_marks

        total_awarded += awarded
        total_possible += max_marks

    sub.score = total_awarded
    sub.total = (
        sub.exam.total_marks
        if sub.exam.total_marks
        else total_possible
    )

    flag_modified(sub, "result")





def render(sub) -> None:
    by_page: dict[int, list] = {}

    for q in sub.result["questions"]:
        page = int(q["page"])
        by_page.setdefault(page, []).append(q)

    for p in sub.pages:
        src = Path(p.cropped_path)

        out = src.with_name(
            src.name.replace("crop_", "ann_")
        )

        annotate(
            str(src),
            str(out),
            by_page.get(p.idx + 1, []),
        )

        p.annotated_path = str(out)