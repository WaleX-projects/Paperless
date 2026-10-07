from pathlib import Path
from sqlalchemy.orm.attributes import flag_modified
from .imaging import annotate


def recompute(sub) -> None:
    qs = sub.result["questions"]
    for q in qs:
        q["awarded"] = max(0.0, min(float(q["awarded"]), float(q["max_marks"])))
        q["correct"] = q["awarded"] >= q["max_marks"]
    sub.score = sum(q["awarded"] for q in qs)
    sub.total = sub.exam.total_marks or sum(q["max_marks"] for q in qs)
    flag_modified(sub, "result")


def render(sub) -> None:
    by_page: dict[int, list] = {}
    for q in sub.result["questions"]:
        by_page.setdefault(int(q["page"]), []).append(q)
    for p in sub.pages:
        src = Path(p.cropped_path)
        out = src.with_name(src.name.replace("crop_", "ann_"))
        annotate(str(src), str(out), by_page.get(p.idx + 1, []))
        p.annotated_path = str(out)
