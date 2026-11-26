"""Ảnh chia sẻ 1200×630 cho từng hồ sơ: logo hoặc ảnh đại diện + tên + loại, địa phương.
Dùng khi dựng trang; nếu thiếu Pillow thì bỏ qua (trang dùng ảnh mặc định)."""
import os
try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:  # Pillow chưa cài
    Image = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_B = os.path.join(ROOT, "web", "fonts", "BeVietnamPro-Bold.ttf")
FONT_R = os.path.join(ROOT, "web", "fonts", "BeVietnamPro-Regular.ttf")
PAPER, INK, INK2, SEA, SUN = (241, 244, 242), (16, 42, 44), (74, 95, 97), (11, 110, 105), (233, 168, 0)

def _wrap(draw, text, font, width, max_lines):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= width: cur = t
        else:
            if cur: lines.append(cur)
            cur = w
        if len(lines) == max_lines: break
    if cur and len(lines) < max_lines: lines.append(cur)
    if len(lines) == max_lines and " ".join(lines) != text:
        while draw.textlength(lines[-1] + "…", font=font) > width and lines[-1]: lines[-1] = lines[-1][:-1]
        lines[-1] += "…"
    return lines

def make_card(img_path, name, subtitle, out_path, round_img=False, site="innovation.invietnam.vn"):
    if Image is None or not os.path.exists(img_path): return False
    W, H = 1200, 630
    im = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(im)
    d.rectangle((0, H - 14, W, H), fill=SEA)
    # khung ảnh
    box = 300
    x0, y0 = 80, (H - box) // 2 - 10
    d.rounded_rectangle((x0, y0, x0 + box, y0 + box), radius=box // 2 if round_img else 36, fill=(255, 255, 255), outline=(213, 222, 218), width=3)
    src = Image.open(img_path).convert("RGBA")
    if round_img:
        s = min(src.size); src = src.crop(((src.width - s) // 2, (src.height - s) // 2, (src.width - s) // 2 + s, (src.height - s) // 2 + s)).resize((box - 12, box - 12), Image.LANCZOS)
        mask = Image.new("L", src.size, 0); ImageDraw.Draw(mask).ellipse((0, 0, src.width, src.height), fill=255)
        im.paste(src.convert("RGB"), (x0 + 6, y0 + 6), mask)
    else:
        inner = box - 60
        bb = src.getbbox()
        if bb: src = src.crop(bb)
        # bỏ viền trắng quanh logo (ảnh không trong suốt)
        bg = Image.new("RGBA", src.size, (255, 255, 255, 255))
        diff = Image.eval(Image.alpha_composite(bg, src).convert("L"), lambda v: 255 if v < 245 else 0).getbbox()
        if diff and (diff[2] - diff[0]) > 8 and (diff[3] - diff[1]) > 8: src = src.crop(diff)
        k = min(inner / src.width, inner / src.height)
        src = src.resize((max(1, int(src.width * k)), max(1, int(src.height * k))), Image.LANCZOS)
        im.paste(src, (x0 + (box - src.width) // 2, y0 + (box - src.height) // 2), src)
    # chữ
    fb = ImageFont.truetype(FONT_B, 64); fs = ImageFont.truetype(FONT_R, 34); fm = ImageFont.truetype(FONT_B, 28)
    tx, tw = x0 + box + 60, W - (x0 + box + 60) - 70
    lines = _wrap(d, name, fb, tw, 3)
    y = H // 2 - (len(lines) * 76 + 60) // 2
    for ln in lines:
        d.text((tx, y), ln, font=fb, fill=INK); y += 76
    d.text((tx, y + 12), subtitle, font=fs, fill=INK2)
    d.text((80, 40), "Hệ sinh thái khởi nghiệp ĐMST Việt Nam", font=fm, fill=SEA)
    d.text((W - 80 - d.textlength(site, font=fs), H - 70), site, font=fs, fill=INK2)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    im.save(out_path, "JPEG", quality=84, optimize=True, progressive=True)
    return True
