import cv2
import numpy as np

MAX_SIDE = 2000


def _order(pts: np.ndarray) -> np.ndarray:
    pts = pts.astype("float32")
    s, d = pts.sum(axis=1), np.diff(pts, axis=1).ravel()
    return np.array([pts[s.argmin()], pts[d.argmin()], pts[s.argmax()], pts[d.argmax()]], dtype="float32")  # tl,tr,br,bl


def crop_paper(src: str, dst: str) -> None:
    """Detect the paper's outline, crop the background edges, straighten perspective."""
    img = cv2.imread(src)
    if img is None:
        raise ValueError(f"Cannot read image {src}")
    h, w = img.shape[:2]
    k = 800 / max(h, w)
    small = cv2.resize(img, None, fx=k, fy=k)
    gray = cv2.GaussianBlur(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY), (5, 5), 0)
    edges = cv2.dilate(cv2.Canny(gray, 50, 150), np.ones((3, 3), np.uint8), iterations=2)
    cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    area_min = 0.2 * small.shape[0] * small.shape[1]
    quad = None
    for c in sorted(cnts, key=cv2.contourArea, reverse=True)[:5]:
        if cv2.contourArea(c) < area_min:
            break
        approx = cv2.approxPolyDP(c, 0.02 * cv2.arcLength(c, True), True)
        if len(approx) == 4:
            quad = _order(approx.reshape(4, 2) / k)
            break
    out = img
    if quad is not None:
        tl, tr, br, bl = quad
        W = int(max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl)))
        H = int(max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl)))
        dstq = np.array([[0, 0], [W - 1, 0], [W - 1, H - 1], [0, H - 1]], dtype="float32")
        out = cv2.warpPerspective(img, cv2.getPerspectiveTransform(quad, dstq), (W, H))
    oh, ow = out.shape[:2]
    if max(oh, ow) > MAX_SIDE:
        f = MAX_SIDE / max(oh, ow)
        out = cv2.resize(out, None, fx=f, fy=f, interpolation=cv2.INTER_AREA)
    cv2.imwrite(dst, out, [cv2.IMWRITE_JPEG_QUALITY, 90])


def annotate(src: str, dst: str, marks: list[dict]) -> None:
    """Draw check / X / partial-score at the AI-provided normalized (x, y) coordinates."""
    img = cv2.imread(src)
    h, w = img.shape[:2]
    s = max(14, int(0.022 * w))
    th = max(2, s // 6)
    green, red, orange = (60, 160, 40), (40, 40, 220), (0, 140, 255)
    for m in marks:
        x = int(min(max(float(m["x"]), 0), 1) * w)
        y = int(min(max(float(m["y"]), 0), 1) * h)
        mx = float(m["max_marks"])
        aw = min(float(m["awarded"]), mx) if mx else float(m["awarded"])
        if mx and aw >= mx:
            pts = np.array([(x - s * .6, y), (x - s * .15, y + s * .55), (x + s * .75, y - s * .65)], np.int32)
            cv2.polylines(img, [pts], False, green, th, cv2.LINE_AA)
        elif aw <= 0:
            cv2.line(img, (x - s // 2, y - s // 2), (x + s // 2, y + s // 2), red, th, cv2.LINE_AA)
            cv2.line(img, (x - s // 2, y + s // 2), (x + s // 2, y - s // 2), red, th, cv2.LINE_AA)
        else:
            pts = np.array([(x - s * .6, y), (x - s * .15, y + s * .55), (x + s * .75, y - s * .65)], np.int32)
            cv2.polylines(img, [pts], False, orange, th, cv2.LINE_AA)
        label = f"{aw:g}/{mx:g}"
        cv2.putText(img, label, (x + s, y + s // 3), cv2.FONT_HERSHEY_SIMPLEX, s / 32, red if aw < mx else green, max(1, th // 2), cv2.LINE_AA)
    cv2.imwrite(dst, img, [cv2.IMWRITE_JPEG_QUALITY, 90])
