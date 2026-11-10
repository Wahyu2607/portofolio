import base64
import os
import shutil
from pathlib import Path
import streamlit as st

# ─── Workspace Cleanup & Housekeeping ───
def cleanup_workspace():
    base = Path(r"c:\Users\ACER\Downloads\prtprog")
    assets_dir = base / "assets"
    archive_dir = base / "archive"
    screenshots_dir = base / "screenshots"

    # Daftar file temporary / redundant yang tidak dipakai oleh aplikasi
    unneeded_files = [
        base / "index.html",                      # File HTML mockup awal yang tidak dipakai
        base / "hero_standalone.py",              # File script standalone lama
        base / "debug_info.txt",                  # Log debug lama di root
        archive_dir / "debug_info.txt",           # Log debug sementara saat cropping gambar
        archive_dir / "Untitled_design_raw.png",  # File raw backup crop lama
        archive_dir / "hero_standalone.py",
        assets_dir / "showcase.jpg",              # File screenshot lama yang tidak direferensikan
        base / "showcase.jpg",
    ]
    for f in unneeded_files:
        try:
            if f.is_file():
                f.unlink()
        except Exception:
            pass

    # Hapus folder archive jika sudah kosong atau bersihkan sisa file di dalamnya
    if archive_dir.is_dir():
        try:
            for sub in archive_dir.glob("*"):
                try:
                    if sub.is_file():
                        sub.unlink()
                except Exception:
                    pass
            archive_dir.rmdir()
        except Exception:
            pass

    # Hapus folder screenshots jika kosong
    if screenshots_dir.is_dir():
        try:
            if not any(screenshots_dir.iterdir()):
                screenshots_dir.rmdir()
        except Exception:
            pass

cleanup_workspace()

# ─── Generate & Load profile_clean.png Transparan Murni Bebas Artefak ───
def ensure_profile_clean_image():
    base_dir = Path(r"c:\Users\ACER\Downloads\prtprog")
    assets_dir = base_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    dst_clean = assets_dir / "profile_clean.png"

    # Jika profile_clean.png sudah valid (> 50KB) dan ada, langsung gunakan
    if dst_clean.is_file() and dst_clean.stat().st_size > 50000:
        return

    brain_clean = Path(r"C:\Users\ACER\.gemini\antigravity\brain\f3962daa-9f54-4756-a943-5382ec4f90ce\profile_clean.png")
    brain_untitled = Path(r"C:\Users\ACER\.gemini\antigravity\brain\f3962daa-9f54-4756-a943-5382ec4f90ce\Untitled design.png")

    src_untitled = assets_dir / "Untitled design.png" if (assets_dir / "Untitled design.png").is_file() else base_dir / "Untitled design.png"
    src_profile = assets_dir / "profile.png" if (assets_dir / "profile.png").is_file() else base_dir / "profile.png"
    src_jpg = assets_dir / "gemini2.jpg" if (assets_dir / "gemini2.jpg").is_file() else base_dir / "gemini2.jpg"

    if src_untitled.is_file():
        try:
            from PIL import Image
            import numpy as np
            im = Image.open(src_untitled)
            im_rgba = im.convert("RGBA")
            arr_rgba = np.array(im_rgba)
            
            alpha = arr_rgba[:, :, 3]
            if (alpha > 240).all():
                r, g, b = arr_rgba[:,:,0], arr_rgba[:,:,1], arr_rgba[:,:,2]
                is_bg = (r > 245) & (g > 245) & (b > 245)
                is_fg = ~is_bg
            else:
                is_fg = alpha > 15
            
            fg_y, fg_x = np.where(is_fg)
            if len(fg_y) > 0:
                y1, y2 = fg_y.min(), fg_y.max()
                x1, x2 = fg_x.min(), fg_x.max()
                pad_t = int(im_rgba.height * 0.01)
                y1 = max(0, y1 - pad_t)
                
                cropped = im_rgba.crop((x1, y1, x2 + 1, y2 + 1))
                cropped.save(dst_clean, "PNG")
                try:
                    cropped.save(brain_clean, "PNG")
                    cropped.save(brain_untitled, "PNG")
                except Exception:
                    pass
                return
        except Exception:
            pass

    try:
        from PIL import Image, ImageFilter
        import numpy as np

        # Prioritas 1: Bersihkan profile.png (wajah, sweater, rambut, dan laptop sudah 100% utuh tanpa lubang)
        if src_profile.is_file():
            im = Image.open(src_profile).convert("RGBA")
            arr = np.array(im)
            h, w = arr.shape[:2]

            # 1. Hapus sisa kotak catur di sebelah kanan gagang cangkir (x > 90.2%)
            arr[int(h * 0.74):, int(w * 0.902):, 3] = 0

            # 2. Hapus sisa kotak catur di bawah dasar cangkir & laptop (y > 91.6%)
            arr[int(h * 0.916):, int(w * 0.65):, 3] = 0

            # 3. Hapus sisa kotak catur di atas bibir cangkir sebelah kanan tangan (y < 79.5% dan x > 73%)
            arr[int(h * 0.74):int(h * 0.795), int(w * 0.73):, 3] = 0

            # 4. Hapus sudut luar atas gagang cangkir
            arr[int(h * 0.795):int(h * 0.825), int(w * 0.845):, 3] = 0

            # 5. Hapus sudut luar bawah gagang cangkir
            arr[int(h * 0.892):int(h * 0.916), int(w * 0.845):, 3] = 0

            # 6. Bersihkan kotak catur di dalam lubang lengkungan gagang cangkir
            hy1, hy2 = int(h * 0.835), int(h * 0.880)
            hx1, hx2 = int(w * 0.855), int(w * 0.885)
            hc = arr[hy1:hy2, hx1:hx2]
            rh = hc[:, :, 0].astype(int)
            gh = hc[:, :, 1].astype(int)
            bh = hc[:, :, 2].astype(int)
            diff_h = np.maximum(np.maximum(rh, gh), bh) - np.minimum(np.minimum(rh, gh), bh)
            br_h = (rh + gh + bh) // 3
            is_chk = (diff_h <= 18) & (((br_h >= 190) & (br_h <= 222)) | (br_h >= 246))
            hc[is_chk, 3] = 0
            arr[hy1:hy2, hx1:hx2] = hc

            # 7. Bersihkan artefak garis tipis 1-pixel di tepi gambar
            arr[:, :2, 3] = 0
            arr[:, int(w * 0.995):, 3] = 0
            arr[:2, :, 3] = 0

            out_im = Image.fromarray(arr)
            out_im.save(dst_clean, "PNG")
            try:
                out_im.save(brain_clean, "PNG")
            except Exception:
                pass
            return

        # Prioritas 2: Buat dari gemini2.jpg menggunakan BFS perimeter dan mask cangkir presisi
        if src_jpg.is_file():
            im = Image.open(src_jpg).convert("RGBA")
            arr = np.array(im)
            h, w = arr.shape[:2]

            r = arr[:, :, 0].astype(int)
            g = arr[:, :, 1].astype(int)
            b = arr[:, :, 2].astype(int)

            diff = np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b)
            brightness = (r + g + b) // 3
            min_c = np.minimum(np.minimum(r, g), b)

            # Kotak catur abu-abu & putih netral
            is_checker = (diff <= 26) & (brightness >= 165) & (min_c >= 140)

            # Masking cangkir kopi secara presisi
            cup_mask = np.zeros((h, w), dtype=bool)
            cup_mask[int(h * 0.795):int(h * 0.916), int(w * 0.725):int(w * 0.90)] = True
            cup_mask[int(h * 0.835):int(h * 0.880), int(w * 0.855):int(w * 0.885)] = False

            visited = np.zeros((h, w), dtype=bool)
            bg_mask = np.zeros((h, w), dtype=bool)
            from collections import deque
            q = deque()

            for x in range(w):
                if is_checker[0, x]:
                    visited[0, x] = True
                    q.append((0, x))
                if is_checker[h - 1, x]:
                    visited[h - 1, x] = True
                    q.append((h - 1, x))

            for y in range(h):
                if is_checker[y, 0]:
                    visited[y, 0] = True
                    q.append((y, 0))
                if is_checker[y, w - 1]:
                    visited[y, w - 1] = True
                    q.append((y, w - 1))

            while q:
                cy, cx = q.popleft()
                bg_mask[cy, cx] = True

                for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and not visited[ny, nx]:
                        visited[ny, nx] = True
                        if cup_mask[ny, nx]:
                            continue
                        if is_checker[ny, nx]:
                            q.append((ny, nx))

            fg_alpha = np.where(bg_mask, 0, 255).astype(np.uint8)
            alpha_img = Image.fromarray(fg_alpha).filter(ImageFilter.GaussianBlur(0.8))

            im.putalpha(alpha_img)
            im.save(dst_clean, "PNG")
            try:
                im.save(brain_clean, "PNG")
            except Exception:
                pass
    except Exception:
        pass

ensure_profile_clean_image()

# ─── Load Local Profile Image as Base64 for Streamlit HTML ───
def get_image_base64():
    candidates = [
        "profile_clean.png",
        "Untitled design.png",
        "profile.png",
        "gemini2_nobg.png",
        "gemini2.png",
        "gemini2.jpg",
    ]
    base_dir = Path(r"c:\Users\ACER\Downloads\prtprog")
    search_dirs = [
        base_dir / "assets",
        base_dir,
        Path(__file__).resolve().parent / "assets" if "__file__" in globals() else Path("assets"),
        Path(__file__).resolve().parent if "__file__" in globals() else Path("."),
        Path("assets"),
        Path("."),
    ]
    for d in search_dirs:
        for name in candidates:
            p = d / name
            if p.is_file():
                try:
                    with open(p, "rb") as f:
                        raw = f.read()
                        mime = "image/png" if raw.startswith(b"\x89PNG") else "image/jpeg"
                        data = base64.b64encode(raw).decode("utf-8")
                        if data:
                            return f"data:{mime};base64,{data}"
                except Exception:
                    pass
    return ""

img_b64 = get_image_base64()

# ─── Load Local CV PDF as Base64 for Direct Download ───
def get_cv_base64():
    candidates = [
        "CV_WAHYU PAMUNGKAS.pdf",
        "CV_WAHYU_PAMUNGKAS.pdf",
        "CV.pdf",
    ]
    base_dir = Path(r"c:\Users\ACER\Downloads\prtprog")
    search_dirs = [
        base_dir / "assets",
        base_dir,
        Path(__file__).resolve().parent / "assets" if "__file__" in globals() else Path("assets"),
        Path(__file__).resolve().parent if "__file__" in globals() else Path("."),
        Path("assets"),
        Path("."),
    ]
    for d in search_dirs:
        for name in candidates:
            p = d / name
            if p.is_file():
                try:
                    with open(p, "rb") as f:
                        raw = f.read()
                        data = base64.b64encode(raw).decode("utf-8")
                        if data:
                            return data
                except Exception:
                    pass
    return ""

cv_b64 = get_cv_base64()

# ─── Load Project 01 (Financial Distress) Preview Image as Base64 ───
def get_project_financial_image_base64():
    base_dir = Path(r"c:\Users\ACER\Downloads\prtprog")
    brain_dst = Path(r"C:\Users\ACER\.gemini\antigravity\brain\f3962daa-9f54-4756-a943-5382ec4f90ce\sspr1.jpeg")
    src_ss = base_dir / "assets" / "sspr1.jpeg"
    if src_ss.is_file() and not brain_dst.is_file():
        try:
            shutil.copy2(src_ss, brain_dst)
        except Exception:
            pass

    candidates = [
        base_dir / "assets" / "sspr1.jpeg",
        base_dir / "assets" / "sspr1.jpg",
        base_dir / "assets" / "sspr1.png",
        base_dir / "sspr1.jpeg",
        base_dir / "sspr1.jpg",
        base_dir / "assets" / "financial_distress.jpg",
        base_dir / "assets" / "financial_distress.png",
    ]
    for p in candidates:
        if p.is_file():
            try:
                with open(p, "rb") as f:
                    raw = f.read()
                    mime = "image/png" if raw.startswith(b"\x89PNG") else "image/jpeg"
                    data = base64.b64encode(raw).decode("utf-8")
                    if data:
                        return f"data:{mime};base64,{data}"
            except Exception:
                pass
    return ""

project1_img_b64 = get_project_financial_image_base64()

# ─── Page Configuration ───
st.set_page_config(
    page_title="Wahyu Pamungkas | Portfolio",
    page_icon="💻",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Hide Streamlit Default Elements & Apply Global Dark Theme ───
st.markdown("""
<style>
/* ========== GLOBAL RESET & DARK THEME ========== */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

html, body, .stApp, [data-testid="stAppViewContainer"], .main {
    scroll-behavior: smooth !important;
}

@media (min-height: 720px) and (min-width: 992px) {
    html, body, .stApp, [data-testid="stAppViewContainer"] {
        scroll-snap-type: y proximity;
        scroll-padding-top: clamp(90px, 11vh, 105px);
    }
}
@media (max-height: 719px), (max-width: 991px) {
    html, body, .stApp, [data-testid="stAppViewContainer"] {
        scroll-snap-type: y proximity;
        scroll-padding-top: 80px;
    }
}

.fullscreen-section, .hero-section, .about-section, .skills-section, .projects-section, .footer-section, .blog-section, #home, #about, #skills, #projects, #blog, #contact {
    scroll-margin-top: clamp(92px, 11vh, 105px) !important;
    scroll-snap-align: start;
    scroll-snap-stop: normal;
}

/* Hide Streamlit defaults completely (Status widget checklist, header, toolbar, etc.) */
#MainMenu,
header,
footer,
.stDeployButton,
header[data-testid="stHeader"],
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
[data-testid="stSidebar"],
[data-testid="collapsedControl"],
.stAppToolbar,
.stAppHeader {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    width: 0 !important;
    opacity: 0 !important;
    pointer-events: none !important;
}

/* Root variables (Dark Mode default) */
:root {
    --bg-primary: #0b0f19;
    --bg-secondary: #111827;
    --bg-card: #151c2c;
    --bg-card-hover: #1a2235;
    --accent-purple: #6366f1;
    --accent-purple-hover: #818cf8;
    --accent-purple-glow: rgba(99, 102, 241, 0.3);
    --text-primary: #ffffff;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --border-color: #1e293b;
    --gradient-purple: linear-gradient(135deg, #6366f1, #8b5cf6);
}

/* Light Mode Theme Variables */
:root[data-theme="light"],
[data-theme="light"],
body.light-mode,
.stApp[data-theme="light"],
[data-theme="light"] .stApp,
html:has(#portfolioThemeToggle:checked),
body:has(#portfolioThemeToggle:checked),
.stApp:has(#portfolioThemeToggle:checked),
:root:has(#portfolioThemeToggle:checked) {
    --bg-primary: #f8fafc;
    --bg-secondary: #f1f5f9;
    --bg-card: #ffffff;
    --bg-card-hover: #f8fafc;
    --accent-purple: #6366f1;
    --accent-purple-hover: #4f46e5;
    --accent-purple-glow: rgba(99, 102, 241, 0.18);
    --text-primary: #0f172a;
    --text-secondary: #475569;
    --text-muted: #94a3b8;
    --border-color: #e2e8f0;
    --gradient-purple: linear-gradient(135deg, #6366f1, #8b5cf6);
}

/* Global Smooth Transitions */
body, .stApp, .navbar, .project-card, .stat-card, .code-snippet-box, .testimonial-card, .hero-glow-circle, .hero-digital-system {
    transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
}

/* Main app background */
body {
    background-color: #070a13 !important;
}

.stApp, .main, .block-container {
    background-color: transparent !important;
    background: transparent !important;
    color: var(--text-primary) !important;
}

.stApp {
    background: transparent !important;
    background-color: transparent !important;
}

/* Container width and responsive padding */
.block-container {
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    max-width: 1400px !important;
    width: 95% !important;
}

/* Remove column gaps styling */
[data-testid="stHorizontalBlock"] {
    gap: 1rem;
}

/* Hide all streamlit element labels */
.stMarkdown p { margin-bottom: 0; }

/* ========== NAVBAR (Sticky / Fixed Viewport Pinning & Breakout) ========== */
[data-testid="element-container"]:has(.navbar),
.stMarkdown:has(.navbar),
[data-testid="stMarkdownContainer"]:has(.navbar),
[data-testid="stVerticalBlock"]:has(.navbar),
[data-testid="stVerticalBlockBorderWrapper"]:has(.navbar) {
    contain: none !important;
    transform: none !important;
    filter: none !important;
    perspective: none !important;
    will-change: auto !important;
    overflow: visible !important;
    position: static !important;
}

.navbar {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    right: 0 !important;
    width: 100% !important;
    max-width: 100vw !important;
    z-index: 999999 !important;
    background: rgba(11, 15, 25, 0.88) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border-bottom: 1px solid var(--border-color) !important;
    padding: 0.9rem 2rem !important;
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    box-sizing: border-box !important;
    margin: 0 !important;
    transform: none !important;
    will-change: auto !important;
}

.navbar-brand {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 1.3rem;
    font-weight: 700;
    color: var(--text-primary);
    text-decoration: none;
    font-family: 'Inter', sans-serif;
}

.navbar-brand svg {
    width: 28px;
    height: 28px;
}

.navbar-links {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    list-style: none;
    margin: 0;
    padding: 0;
}

.navbar-links a.nav-item {
    color: var(--text-secondary);
    text-decoration: none;
    font-size: 0.92rem;
    font-weight: 500;
    font-family: 'Inter', sans-serif;
    padding: 0.42rem 0.9rem;
    border-radius: 8px;
    position: relative;
    border: 1px solid transparent;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    cursor: pointer;
}

.navbar-links a.nav-item:hover {
    color: #ffffff;
    background: rgba(255, 255, 255, 0.06);
    border-color: rgba(255, 255, 255, 0.1);
}

/* Base Active Highlight (Neon Purple & Glowing Indicator) */
.navbar-links a.nav-item.active {
    color: #818cf8 !important;
    font-weight: 600 !important;
    background: rgba(99, 102, 241, 0.12) !important;
    border: 1px solid rgba(99, 102, 241, 0.3) !important;
    box-shadow: 0 0 16px rgba(99, 102, 241, 0.22) !important;
}

.navbar-links a.nav-item.active::after {
    content: '';
    position: absolute;
    bottom: -3px;
    left: 20%;
    width: 60%;
    height: 2px;
    background: linear-gradient(90deg, #6366f1, #c084fc);
    border-radius: 2px;
    box-shadow: 0 0 8px rgba(129, 140, 248, 0.85);
}

/* CSS Dynamic Fallback: Deactivate default Home active state when another section is targeted */
body:has(#about:target) .navbar-links a[href="#home"],
body:has(#skills:target) .navbar-links a[href="#home"],
body:has(#projects:target) .navbar-links a[href="#home"],
body:has(#blog:target) .navbar-links a[href="#home"],
body:has(#contact:target) .navbar-links a[href="#home"] {
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
    background: transparent !important;
    border-color: transparent !important;
    box-shadow: none !important;
}

body:has(#about:target) .navbar-links a[href="#home"]::after,
body:has(#skills:target) .navbar-links a[href="#home"]::after,
body:has(#projects:target) .navbar-links a[href="#home"]::after,
body:has(#blog:target) .navbar-links a[href="#home"]::after,
body:has(#contact:target) .navbar-links a[href="#home"]::after {
    display: none !important;
}

/* CSS Dynamic Fallback: Activate targeted section */
body:has(#about:target) .navbar-links a[href="#about"],
body:has(#skills:target) .navbar-links a[href="#skills"],
body:has(#projects:target) .navbar-links a[href="#projects"],
body:has(#blog:target) .navbar-links a[href="#blog"],
body:has(#contact:target) .navbar-links a[href="#contact"],
body:has(#home:target) .navbar-links a[href="#home"] {
    color: #818cf8 !important;
    font-weight: 600 !important;
    background: rgba(99, 102, 241, 0.12) !important;
    border: 1px solid rgba(99, 102, 241, 0.3) !important;
    box-shadow: 0 0 16px rgba(99, 102, 241, 0.22) !important;
}

body:has(#about:target) .navbar-links a[href="#about"]::after,
body:has(#skills:target) .navbar-links a[href="#skills"]::after,
body:has(#projects:target) .navbar-links a[href="#projects"]::after,
body:has(#blog:target) .navbar-links a[href="#blog"]::after,
body:has(#contact:target) .navbar-links a[href="#contact"]::after,
body:has(#home:target) .navbar-links a[href="#home"]::after {
    content: '' !important;
    display: block !important;
    position: absolute !important;
    bottom: -3px !important;
    left: 20% !important;
    width: 60% !important;
    height: 2px !important;
    background: linear-gradient(90deg, #6366f1, #c084fc) !important;
    border-radius: 2px !important;
    box-shadow: 0 0 8px rgba(129, 140, 248, 0.85) !important;
}

.hire-btn {
    background: var(--gradient-purple);
    color: white !important;
    padding: 0.55rem 1.3rem;
    border-radius: 8px;
    text-decoration: none;
    font-size: 0.9rem;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
    display: flex;
    align-items: center;
    gap: 0.4rem;
    transition: transform 0.2s, box-shadow 0.3s;
    box-shadow: 0 4px 15px var(--accent-purple-glow);
}

.hire-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 25px var(--accent-purple-glow);
}

/* ========== NAVBAR ACTIONS & THEME TOGGLE BUTTON ========== */
.navbar-actions {
    display: flex;
    align-items: center;
    gap: 0.85rem;
}

.portfolio-theme-toggle-cb,
input#portfolioThemeToggle,
input#curtainTrigger,
input[type="checkbox"] {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    position: absolute !important;
    width: 0 !important;
    height: 0 !important;
    pointer-events: none !important;
    margin: 0 !important;
    padding: 0 !important;
    border: none !important;
    clip: rect(0, 0, 0, 0) !important;
}

.theme-toggle-btn {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.16);
    color: #ffffff;
    width: 38px;
    height: 38px;
    border-radius: 9px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    font-size: 1.1rem;
    transition: all 0.25s ease;
    outline: none;
    padding: 0;
    user-select: none;
    -webkit-user-select: none;
}

.theme-toggle-btn:hover {
    background: rgba(99, 102, 241, 0.2);
    border-color: rgba(99, 102, 241, 0.45);
    transform: scale(1.08);
    box-shadow: 0 0 15px rgba(99, 102, 241, 0.35);
}

.theme-icon-sun {
    display: none !important;
    pointer-events: none;
    user-select: none;
}
.theme-icon-moon {
    display: inline-block !important;
    pointer-events: none;
    user-select: none;
}

/* ========== LIGHT MODE SPECIFIC COMPONENT STYLING ========== */
[data-theme="light"] body,
body.light-mode,
[data-theme="light"] .stApp,
.light-mode .stApp,
.stApp[data-theme="light"],
.stApp.light-mode,
[data-theme="light"] .main,
.light-mode .main,
[data-theme="light"] .block-container,
.light-mode .block-container,
html:has(#portfolioThemeToggle:checked),
body:has(#portfolioThemeToggle:checked),
.stApp:has(#portfolioThemeToggle:checked),
body:has(#portfolioThemeToggle:checked) .stApp,
body:has(#portfolioThemeToggle:checked) [data-testid="stAppViewContainer"],
body:has(#portfolioThemeToggle:checked) .main,
body:has(#portfolioThemeToggle:checked) .block-container {
    background-color: transparent !important;
    background: transparent !important;
    color: #0f172a !important;
}

body:has(#portfolioThemeToggle:checked) {
    background-color: #f1f5f9 !important;
}

[data-theme="light"] .navbar,
.light-mode .navbar,
body:has(#portfolioThemeToggle:checked) .navbar {
    background: rgba(255, 255, 255, 0.94) !important;
    border-bottom: 1px solid #e2e8f0 !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04) !important;
}

[data-theme="light"] .navbar-brand,
.light-mode .navbar-brand,
body:has(#portfolioThemeToggle:checked) .navbar-brand {
    color: #0f172a !important;
}

[data-theme="light"] .navbar-links a.nav-item,
.light-mode .navbar-links a.nav-item,
body:has(#portfolioThemeToggle:checked) .navbar-links a.nav-item {
    color: #475569 !important;
}

[data-theme="light"] .navbar-links a.nav-item:hover,
.light-mode .navbar-links a.nav-item:hover,
body:has(#portfolioThemeToggle:checked) .navbar-links a.nav-item:hover {
    color: #0f172a !important;
    background: rgba(0, 0, 0, 0.05) !important;
}

[data-theme="light"] .navbar-links a.nav-item.active,
.light-mode .navbar-links a.nav-item.active,
body:has(#portfolioThemeToggle:checked) .navbar-links a.nav-item.active {
    color: #4f46e5 !important;
    background: rgba(99, 102, 241, 0.1) !important;
    border-color: rgba(99, 102, 241, 0.25) !important;
    box-shadow: 0 0 12px rgba(99, 102, 241, 0.15) !important;
}

/* Light mode target indicators */
body:has(#portfolioThemeToggle:checked):has(#about:target) .navbar-links a[href="#about"],
body:has(#portfolioThemeToggle:checked):has(#skills:target) .navbar-links a[href="#skills"],
body:has(#portfolioThemeToggle:checked):has(#projects:target) .navbar-links a[href="#projects"],
body:has(#portfolioThemeToggle:checked):has(#blog:target) .navbar-links a[href="#blog"],
body:has(#portfolioThemeToggle:checked):has(#contact:target) .navbar-links a[href="#contact"],
body:has(#portfolioThemeToggle:checked):has(#home:target) .navbar-links a[href="#home"] {
    color: #4f46e5 !important;
    background: rgba(99, 102, 241, 0.1) !important;
    border: 1px solid rgba(99, 102, 241, 0.25) !important;
    box-shadow: 0 0 12px rgba(99, 102, 241, 0.15) !important;
}

body:has(#portfolioThemeToggle:checked):has(#about:target) .navbar-links a[href="#about"]::after,
body:has(#portfolioThemeToggle:checked):has(#skills:target) .navbar-links a[href="#skills"]::after,
body:has(#portfolioThemeToggle:checked):has(#projects:target) .navbar-links a[href="#projects"]::after,
body:has(#portfolioThemeToggle:checked):has(#blog:target) .navbar-links a[href="#blog"]::after,
body:has(#portfolioThemeToggle:checked):has(#contact:target) .navbar-links a[href="#contact"]::after,
body:has(#portfolioThemeToggle:checked):has(#home:target) .navbar-links a[href="#home"]::after {
    background: linear-gradient(90deg, #4f46e5, #7c3aed) !important;
    box-shadow: 0 0 8px rgba(79, 70, 229, 0.5) !important;
}

[data-theme="light"] .theme-toggle-btn,
.light-mode .theme-toggle-btn,
body:has(#portfolioThemeToggle:checked) .theme-toggle-btn {
    background: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    color: #0f172a !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06) !important;
}

[data-theme="light"] .theme-toggle-btn:hover,
.light-mode .theme-toggle-btn:hover,
body:has(#portfolioThemeToggle:checked) .theme-toggle-btn:hover {
    background: #f1f5f9 !important;
    border-color: #6366f1 !important;
    box-shadow: 0 0 15px rgba(99, 102, 241, 0.25) !important;
}

[data-theme="light"] .theme-icon-sun,
.light-mode .theme-icon-sun,
.stApp[data-theme="light"] .theme-icon-sun,
.stApp.light-mode .theme-icon-sun,
body:has(#portfolioThemeToggle:checked) .theme-icon-sun {
    display: inline-block !important;
}
[data-theme="light"] .theme-icon-moon,
.light-mode .theme-icon-moon,
.stApp[data-theme="light"] .theme-icon-moon,
.stApp.light-mode .theme-icon-moon,
body:has(#portfolioThemeToggle:checked) .theme-icon-moon {
    display: none !important;
}

[data-theme="light"] .hero-badge,
.light-mode .hero-badge,
body:has(#portfolioThemeToggle:checked) .hero-badge {
    background: rgba(99, 102, 241, 0.08) !important;
    color: #4f46e5 !important;
    border-color: rgba(99, 102, 241, 0.25) !important;
    box-shadow: 0 0 12px rgba(99, 102, 241, 0.1) !important;
}

[data-theme="light"] .hero-title,
.light-mode .hero-title,
body:has(#portfolioThemeToggle:checked) .hero-title {
    color: #0f172a !important;
}

[data-theme="light"] .hero-desc,
.light-mode .hero-desc,
body:has(#portfolioThemeToggle:checked) .hero-desc {
    color: #475569 !important;
}

[data-theme="light"] .btn-secondary,
.light-mode .btn-secondary,
body:has(#portfolioThemeToggle:checked) .btn-secondary {
    background: #ffffff !important;
    color: #1e293b !important;
    border: 1px solid #cbd5e1 !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
}

[data-theme="light"] .btn-secondary:hover,
.light-mode .btn-secondary:hover,
body:has(#portfolioThemeToggle:checked) .btn-secondary:hover {
    background: #f8fafc !important;
    border-color: #94a3b8 !important;
    color: #0f172a !important;
}

[data-theme="light"] .hero-tech-stack,
.light-mode .hero-tech-stack,
body:has(#portfolioThemeToggle:checked) .hero-tech-stack {
    border-top-color: #e2e8f0 !important;
}

[data-theme="light"] .hero-tech-label,
.light-mode .hero-tech-label,
body:has(#portfolioThemeToggle:checked) .hero-tech-label {
    color: #64748b !important;
}

[data-theme="light"] .hero-glow-circle,
.light-mode .hero-glow-circle,
body:has(#portfolioThemeToggle:checked) .hero-glow-circle {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 55%, #a855f7 100%) !important;
    box-shadow: 0 15px 45px rgba(99, 102, 241, 0.3), 0 30px 80px rgba(139, 92, 246, 0.2) !important;
}

[data-theme="light"] .hero-digital-system,
.light-mode .hero-digital-system,
body:has(#portfolioThemeToggle:checked) .hero-digital-system {
    filter: drop-shadow(0 15px 35px rgba(99, 102, 241, 0.35)) drop-shadow(0 0 20px rgba(124, 58, 237, 0.25)) !important;
}

[data-theme="light"] .hero-dot-grid g,
.light-mode .hero-dot-grid g,
body:has(#portfolioThemeToggle:checked) .hero-dot-grid g {
    fill: #6366f1 !important;
    opacity: 0.45 !important;
}

[data-theme="light"] .hero-doodle,
.light-mode .hero-doodle,
body:has(#portfolioThemeToggle:checked) .hero-doodle {
    stroke: #6366f1 !important;
}

[data-theme="light"] .code-snippet-box,
.light-mode .code-snippet-box,
body:has(#portfolioThemeToggle:checked) .code-snippet-box {
    background: rgba(255, 255, 255, 0.95) !important;
    border: 1px solid #e2e8f0 !important;
    box-shadow: 0 20px 45px rgba(15, 23, 42, 0.1), 0 0 20px rgba(99, 102, 241, 0.08) !important;
}

[data-theme="light"] .code-snippet-header,
.light-mode .code-snippet-header,
body:has(#portfolioThemeToggle:checked) .code-snippet-header {
    border-bottom: 1px solid #f1f5f9 !important;
}

[data-theme="light"] .code-snippet-header .code-title,
.light-mode .code-snippet-header .code-title,
body:has(#portfolioThemeToggle:checked) .code-snippet-header .code-title {
    color: #475569 !important;
}

[data-theme="light"] .code-snippet-body,
.light-mode .code-snippet-body,
body:has(#portfolioThemeToggle:checked) .code-snippet-body {
    color: #1e293b !important;
}

[data-theme="light"] .code-snippet-body .code-keyword,
.light-mode .code-snippet-body .code-keyword,
body:has(#portfolioThemeToggle:checked) .code-snippet-body .code-keyword {
    color: #7c3aed !important;
}

[data-theme="light"] .code-snippet-body .code-var,
.light-mode .code-snippet-body .code-var,
body:has(#portfolioThemeToggle:checked) .code-snippet-body .code-var {
    color: #0f172a !important;
}

[data-theme="light"] .code-snippet-body .code-key,
.light-mode .code-snippet-body .code-key,
body:has(#portfolioThemeToggle:checked) .code-snippet-body .code-key {
    color: #0284c7 !important;
}

[data-theme="light"] .code-snippet-body .code-string,
.light-mode .code-snippet-body .code-string,
body:has(#portfolioThemeToggle:checked) .code-snippet-body .code-string {
    color: #059669 !important;
}

[data-theme="light"] .section-divider,
.light-mode .section-divider,
body:has(#portfolioThemeToggle:checked) .section-divider {
    background: linear-gradient(90deg, transparent 0%, rgba(226, 232, 240, 0.95) 15%, rgba(99, 102, 241, 0.35) 50%, rgba(226, 232, 240, 0.95) 85%, transparent 100%) !important;
}

[data-theme="light"] .stat-card,
.light-mode .stat-card,
body:has(#portfolioThemeToggle:checked) .stat-card {
    background: rgba(255, 255, 255, 0.7) !important;
    backdrop-filter: blur(8px) !important;
    -webkit-backdrop-filter: blur(8px) !important;
    border-color: rgba(226, 232, 240, 0.9) !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.04) !important;
}

[data-theme="light"] .stat-card:hover,
.light-mode .stat-card:hover,
body:has(#portfolioThemeToggle:checked) .stat-card:hover {
    box-shadow: 0 8px 25px rgba(99, 102, 241, 0.12) !important;
    border-color: rgba(99, 102, 241, 0.3) !important;
}

[data-theme="light"] .stat-number,
.light-mode .stat-number,
body:has(#portfolioThemeToggle:checked) .stat-number {
    color: #0f172a !important;
}

[data-theme="light"] .about-heading,
.light-mode .about-heading,
body:has(#portfolioThemeToggle:checked) .about-heading,
[data-theme="light"] .section-title,
.light-mode .section-title,
body:has(#portfolioThemeToggle:checked) .section-title,
[data-theme="light"] .footer-heading,
.light-mode .footer-heading,
body:has(#portfolioThemeToggle:checked) .footer-heading {
    color: #0f172a !important;
}

[data-theme="light"] .about-text,
.light-mode .about-text,
body:has(#portfolioThemeToggle:checked) .about-text,
[data-theme="light"] .footer-text,
.light-mode .footer-text,
body:has(#portfolioThemeToggle:checked) .footer-text {
    color: #475569 !important;
}

[data-theme="light"] .about-btn,
.light-mode .about-btn,
body:has(#portfolioThemeToggle:checked) .about-btn {
    border-color: #cbd5e1 !important;
    color: #1e293b !important;
}

[data-theme="light"] .about-btn:hover,
.light-mode .about-btn:hover,
body:has(#portfolioThemeToggle:checked) .about-btn:hover {
    background: #f1f5f9 !important;
    border-color: #6366f1 !important;
    color: #4f46e5 !important;
}

[data-theme="light"] .skills-section,
[data-theme="light"] .projects-section,
[data-theme="light"] .footer-section,
.light-mode .skills-section,
.light-mode .projects-section,
.light-mode .footer-section,
body:has(#portfolioThemeToggle:checked) .skills-section,
body:has(#portfolioThemeToggle:checked) .projects-section,
body:has(#portfolioThemeToggle:checked) .footer-section,
body:has(#portfolioThemeToggle:checked) #blog {
    border-top-color: #e2e8f0 !important;
}

[data-theme="light"] .skill-bar-bg,
.light-mode .skill-bar-bg,
body:has(#portfolioThemeToggle:checked) .skill-bar-bg {
    background: #e2e8f0 !important;
}

[data-theme="light"] .project-card,
.light-mode .project-card,
body:has(#portfolioThemeToggle:checked) .project-card {
    background: rgba(255, 255, 255, 0.72) !important;
    backdrop-filter: blur(8px) !important;
    -webkit-backdrop-filter: blur(8px) !important;
    border-color: rgba(226, 232, 240, 0.9) !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05) !important;
}

[data-theme="light"] .project-card:hover,
.light-mode .project-card:hover,
body:has(#portfolioThemeToggle:checked) .project-card:hover {
    box-shadow: 0 12px 35px rgba(99, 102, 241, 0.15) !important;
    border-color: rgba(99, 102, 241, 0.3) !important;
}

[data-theme="light"] .project-title,
.light-mode .project-title,
body:has(#portfolioThemeToggle:checked) .project-title {
    color: #0f172a !important;
}

[data-theme="light"] .project-desc,
.light-mode .project-desc,
body:has(#portfolioThemeToggle:checked) .project-desc {
    color: #64748b !important;
}

[data-theme="light"] .mockup-inner,
.light-mode .mockup-inner,
body:has(#portfolioThemeToggle:checked) .mockup-inner {
    background: #f8fafc !important;
    border-color: #e2e8f0 !important;
}

[data-theme="light"] .mockup-topbar,
.light-mode .mockup-topbar,
body:has(#portfolioThemeToggle:checked) .mockup-topbar {
    background: #f1f5f9 !important;
    border-bottom-color: #e2e8f0 !important;
}

[data-theme="light"] .mockup-line.long,
[data-theme="light"] .mockup-line.medium,
[data-theme="light"] .mockup-line.short,
.light-mode .mockup-line.long,
.light-mode .mockup-line.medium,
.light-mode .mockup-line.short,
body:has(#portfolioThemeToggle:checked) .mockup-line.long,
body:has(#portfolioThemeToggle:checked) .mockup-line.medium,
body:has(#portfolioThemeToggle:checked) .mockup-line.short {
    background: #cbd5e1 !important;
}

[data-theme="light"] .testimonial-card,
.light-mode .testimonial-card,
body:has(#portfolioThemeToggle:checked) .testimonial-card {
    background: rgba(255, 255, 255, 0.72) !important;
    backdrop-filter: blur(8px) !important;
    -webkit-backdrop-filter: blur(8px) !important;
    border-color: rgba(226, 232, 240, 0.9) !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04) !important;
}

[data-theme="light"] .testimonial-text,
.light-mode .testimonial-text,
body:has(#portfolioThemeToggle:checked) .testimonial-text {
    color: #475569 !important;
}

[data-theme="light"] .testimonial-author-name,
.light-mode .testimonial-author-name,
body:has(#portfolioThemeToggle:checked) .testimonial-author-name {
    color: #0f172a !important;
}

[data-theme="light"] .copyright-bar,
.light-mode .copyright-bar,
body:has(#portfolioThemeToggle:checked) .copyright-bar {
    border-top-color: #e2e8f0 !important;
}

[data-theme="light"] .copyright-text,
.light-mode .copyright-text,
body:has(#portfolioThemeToggle:checked) .copyright-text {
    color: #64748b !important;
}

[data-theme="light"] .social-icon,
.light-mode .social-icon,
body:has(#portfolioThemeToggle:checked) .social-icon {
    background: #f1f5f9 !important;
    color: #475569 !important;
    border-color: #e2e8f0 !important;
}

[data-theme="light"] .social-icon:hover,
.light-mode .social-icon:hover,
body:has(#portfolioThemeToggle:checked) .social-icon:hover {
    background: #6366f1 !important;
    color: #ffffff !important;
}

/* ========== HERO SECTION (UNIFIED RESPONSIVE SHOWCASE) ========== */
.hero-container {
    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
    gap: 3.5rem;
    width: 100%;
    max-width: 1280px;
    margin: 0 auto;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    position: relative;
    box-sizing: border-box;
}

.hero-content-col {
    flex: 1 1 52%;
    max-width: 620px;
}

.hero-badge {
    display: inline-block;
    background: rgba(99, 102, 241, 0.12);
    color: #a5b4fc;
    padding: 0.45rem 1.1rem;
    border-radius: 8px;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 1.8px;
    font-family: 'Inter', sans-serif;
    margin-bottom: 0.95rem;
    border: 1px solid rgba(139, 92, 246, 0.32);
    box-shadow: 0 0 15px rgba(99, 102, 241, 0.15);
}

.hero-title {
    font-family: 'Inter', sans-serif;
    font-size: clamp(2.1rem, 3.8vw, 3.1rem);
    font-weight: 800;
    line-height: 1.16;
    margin-bottom: 0.85rem;
    color: #ffffff;
    letter-spacing: -0.5px;
}

.hero-title .highlight {
    background: linear-gradient(135deg, #818cf8 0%, #c084fc 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    display: inline-block;
}

.hero-desc {
    font-family: 'Inter', sans-serif;
    font-size: 1.02rem;
    color: #94a3b8;
    line-height: 1.55;
    margin-bottom: 1.1rem;
    max-width: 500px;
}

.hero-buttons {
    display: flex;
    align-items: center;
    gap: 1.1rem;
    margin-bottom: 0.95rem;
}

.btn-primary {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: #ffffff !important;
    padding: 0.85rem 1.8rem;
    border-radius: 12px;
    text-decoration: none !important;
    font-size: 0.98rem;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
    display: inline-flex;
    align-items: center;
    gap: 0.55rem;
    transition: transform 0.25s ease, box-shadow 0.3s ease;
    box-shadow: 0 10px 25px -5px rgba(99, 102, 241, 0.5), 0 0 15px rgba(139, 92, 246, 0.3);
    border: none;
    cursor: pointer;
}

.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 14px 32px -5px rgba(99, 102, 241, 0.65), 0 0 25px rgba(139, 92, 246, 0.45);
    color: #ffffff !important;
}

.btn-secondary {
    background: rgba(17, 24, 39, 0.7);
    color: #e2e8f0 !important;
    padding: 0.85rem 1.8rem;
    border-radius: 12px;
    text-decoration: none !important;
    font-size: 0.98rem;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
    display: inline-flex;
    align-items: center;
    gap: 0.55rem;
    border: 1px solid rgba(255, 255, 255, 0.12);
    transition: all 0.25s ease;
    cursor: pointer;
    backdrop-filter: blur(8px);
}

.btn-secondary:hover {
    background: rgba(30, 41, 59, 0.9);
    border-color: rgba(255, 255, 255, 0.28);
    color: #ffffff !important;
    transform: translateY(-2px);
}

/* Sisi Kanan: Visual Showcase & Interaktif (Formating Sesuai Gambar Referensi) */
.hero-visual-col {
    flex: 1 1 50%;
    display: flex;
    justify-content: center;
    align-items: center;
    position: relative;
    min-height: clamp(340px, 48vh, 460px);
    overflow: visible !important;
}

.hero-image-wrapper {
    position: relative;
    width: 100%;
    max-width: 500px;
    height: clamp(340px, 48vh, 460px);
    margin: 0 auto;
    overflow: visible !important;
    display: flex;
    justify-content: center;
    align-items: center;
}

/* Hero Digital System: Bentuk Sistem Digital Berbentuk Bulat di Belakang Foto */
.hero-digital-system {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: clamp(320px, 44vh, 430px);
    height: clamp(320px, 44vh, 430px);
    z-index: 1;
    pointer-events: none;
    display: flex;
    align-items: center;
    justify-content: center;
    filter: drop-shadow(0 0 35px rgba(124, 58, 237, 0.45));
    transition: filter 0.3s ease;
}

.hero-glow-circle {
    display: none !important;
}

.digital-hud-svg {
    width: 100%;
    height: 100%;
    overflow: visible;
}

/* Animations for Digital System */
.digital-radar-scanner {
    transform-origin: 260px 260px;
    animation: digitalRadarSweep 5.5s linear infinite;
}
@keyframes digitalRadarSweep {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.digital-ring-circuit {
    transform-origin: 260px 260px;
    animation: digitalRotateCW 22s linear infinite;
}

.digital-ring-telemetry {
    transform-origin: 260px 260px;
    animation: digitalRotateCCW 16s linear infinite;
}

.digital-ring-outer {
    transform-origin: 260px 260px;
    animation: digitalRotateCW 34s linear infinite;
}

.digital-ring-satellites {
    transform-origin: 260px 260px;
    animation: digitalRotateCCW 24s linear infinite;
}

@keyframes digitalRotateCW {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

@keyframes digitalRotateCCW {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(-360deg); }
}

.digital-core-grid {
    animation: digitalGridPulse 3.5s ease-in-out infinite alternate;
}
@keyframes digitalGridPulse {
    0% { opacity: 0.25; }
    100% { opacity: 0.55; }
}

/* Dekorasi Dot Matrix Grid (Pojok kanan atas) */
.hero-dot-grid {
    position: absolute;
    top: 10px;
    right: 15px;
    z-index: 0;
    pointer-events: none;
    opacity: 0.85;
}

/* Dekorasi Curly Doodle Arrow (Sebelah kiri tubuh subjek) */
.hero-doodle {
    position: absolute;
    bottom: 180px;
    left: -25px;
    z-index: 3;
    pointer-events: none;
}

/* Container Subjek Tanpa Background Box (Seamless Floating Cutout - Ukuran Besar & Jelas) */
.hero-card-frame {
    position: relative;
    width: 100%;
    max-width: 500px;
    height: clamp(340px, 48vh, 460px);
    background: transparent !important;
    overflow: visible !important;
    border: none !important;
    box-shadow: none !important;
    z-index: 6 !important; /* Foto selalu prioritas layer terdepan */
    display: flex;
    justify-content: center;
    align-items: center;
    margin: 0 auto;
    padding: 0;
}

.hero-profile-photo,
[data-testid="stMarkdownContainer"] .hero-profile-photo,
.stMarkdown .hero-profile-photo,
.profile-clean-img {
    position: relative !important;
    width: auto !important;
    max-width: 100% !important;
    height: 100% !important;
    max-height: clamp(340px, 48vh, 460px) !important;
    object-fit: contain !important;
    object-position: center bottom !important;
    display: block !important;
    margin: 0 auto !important;
    padding: 0 !important;
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
    filter: drop-shadow(0 20px 40px rgba(0, 0, 0, 0.55)) !important;
    z-index: 6 !important; /* Foto berada di layer depan, tidak tertutup kode */
    transform-origin: center bottom !important;
    transform: scale(1.06) !important;
    transition: transform 0.5s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

.hero-card-frame:hover .hero-profile-photo,
.hero-card-frame:hover .profile-clean-img {
    transform: scale(1.22) !important;
}

/* Floating Card: Code Snippet Box di sisi kanan luar lingkaran bulat ungu - TIDAK TERPOTONG & TIDAK MENUTUPI MUKA */
.code-snippet-box {
    position: absolute;
    top: 67%;
    right: 12px;
    left: auto !important;
    transform: translateY(-50%);
    width: 236px;
    max-width: calc(100% - 250px);
    box-sizing: border-box !important;
    overflow: visible !important;
    background: rgba(13, 17, 28, 0.68);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(129, 140, 248, 0.42);
    border-radius: 16px;
    padding: 10px 14px;
    z-index: 7 !important; /* Di sisi kanan luar, berada di bawah area muka */
    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.75), 0 0 30px rgba(99, 102, 241, 0.3);
    transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
}

.code-snippet-box:hover {
    transform: translateY(-53%) scale(1.03) !important;
    border-color: rgba(129, 140, 248, 0.7) !important;
    box-shadow: 0 30px 65px rgba(0, 0, 0, 0.92), 0 0 45px rgba(99, 102, 241, 0.55) !important;
}

/* Hero Left Column Tech Stack */
.hero-tech-stack {
    margin-top: 0.85rem;
    padding-top: 0.85rem;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.hero-tech-label {
    font-family: 'Inter', sans-serif;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 1.8px;
    color: #64748b;
    margin-bottom: 0.75rem;
    text-transform: uppercase;
}

.hero-tech-icons {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-wrap: wrap;
}

.hero-tech-icons .tech-icon {
    width: 44px;
    height: 44px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: transform 0.25s ease, box-shadow 0.25s ease;
    cursor: pointer;
    font-family: 'Inter', sans-serif;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

.hero-tech-icons .tech-icon:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.6);
}

.hero-tech-icons .tech-html {
    background: #e44d26;
    color: #ffffff;
    font-weight: 900;
    font-size: 1.15rem;
}

.hero-tech-icons .tech-css {
    background: #264de4;
    color: #ffffff;
    font-weight: 900;
    font-size: 1.15rem;
}

.hero-tech-icons .tech-js {
    background: #f7df1e;
    color: #000000;
    font-weight: 900;
    font-size: 0.95rem;
}

.hero-tech-icons .tech-ts {
    background: #3178c6;
    color: #ffffff;
    font-weight: 800;
    font-size: 0.92rem;
}

.hero-tech-icons .tech-react {
    background: #0e1726;
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.35);
    font-size: 1.35rem;
    font-weight: bold;
}

.hero-tech-icons .tech-node {
    background: #22c55e;
    color: #ffffff;
    font-size: 1.25rem;
    font-weight: bold;
}

.hero-tech-icons .tech-git {
    background: #f05032;
    color: #ffffff;
    font-weight: 800;
    font-size: 1rem;
}


.code-snippet-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 7px;
    margin-bottom: 10px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.code-snippet-header .code-title {
    display: flex;
    align-items: center;
    gap: 6px;
    color: #94a3b8;
    font-size: 0.76rem;
    font-family: 'Inter', sans-serif;
    font-weight: 600;
}

.code-snippet-header .code-title span {
    color: #818cf8;
    font-weight: 700;
}

.code-snippet-header .code-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #10b981;
    box-shadow: 0 0 8px #10b981;
    display: inline-block;
    animation: pulseDot 2s infinite ease-in-out;
}

@keyframes pulseDot {
    0%, 100% { opacity: 1; transform: scale(1); box-shadow: 0 0 8px #10b981; }
    50% { opacity: 0.5; transform: scale(0.85); box-shadow: 0 0 3px #10b981; }
}

.code-snippet-body {
    font-family: 'Courier New', Consolas, Monaco, monospace;
    font-size: 0.69rem;
    line-height: 1.52;
    color: #94a3b8;
    white-space: nowrap;
    overflow: visible;
}

.code-snippet-body .code-keyword {
    color: #c084fc;
    font-weight: 600;
}

.code-snippet-body .code-var {
    color: #f8fafc;
}

.code-snippet-body .code-key {
    color: #93c5fd;
}

.code-snippet-body .code-string {
    color: #86efac;
}

.code-snippet-body .code-bracket {
    color: #fbbf24;
}

/* ========== TECH ICONS BAR ========== */
.tech-bar {
    padding: 2rem 0 3rem 0;
    border-top: 1px solid var(--border-color);
}

.tech-bar-label {
    font-family: 'Inter', sans-serif;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 2px;
    color: var(--text-muted);
    margin-bottom: 1.2rem;
}

.tech-icons {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    align-items: center;
}

.tech-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    font-weight: 700;
    font-family: 'Inter', sans-serif;
    transition: transform 0.2s, box-shadow 0.3s;
    cursor: default;
}

.tech-icon:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
}

.tech-html { background: linear-gradient(135deg, #e34f26, #f16529); color: white; }
.tech-css { background: linear-gradient(135deg, #264de4, #2965f1); color: white; }
.tech-js { background: linear-gradient(135deg, #f0db4f, #e8d44d); color: #323330; }
.tech-ts { background: linear-gradient(135deg, #3178c6, #235a97); color: white; }
.tech-react { background: linear-gradient(135deg, #1a1a2e, #16213e); color: #61dafb; }
.tech-node { background: linear-gradient(135deg, #339933, #2d8a2d); color: white; }
.tech-next { background: linear-gradient(135deg, #1a1a2e, #111); color: white; }
.tech-git { background: linear-gradient(135deg, #f05032, #de4c27); color: white; }

/* ========== SECTION COMMON ========== */
.section {
    padding: 4rem 0;
}

.section-label {
    font-family: 'Inter', sans-serif;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 2px;
    color: var(--accent-purple-hover);
    margin-bottom: 0.5rem;
}

.section-title {
    font-family: 'Inter', sans-serif;
    font-size: 2rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 2rem;
    line-height: 1.3;
}

/* ========== FULLSCREEN SECTION FRAMEWORK & TRANSITIONS ========== */
/* ========== FULLSCREEN SECTION FRAMEWORK & CARD STYLING ========== */
.fullscreen-section {
    min-height: calc(100vh - 128px) !important;
    height: auto !important;
    max-height: none !important;
    width: 100% !important;
    max-width: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    align-items: center !important;
    scroll-snap-align: start !important;
    box-sizing: border-box !important;
    padding: clamp(1.8rem, 3.2vh, 2.6rem) clamp(1.5rem, 3vw, 2.8rem) !important;
    margin-bottom: clamp(45px, 7vh, 75px) !important;
    position: relative !important;
    overflow: visible !important;
    background: rgba(11, 15, 25, 0.42) !important;
    backdrop-filter: blur(8px) saturate(125%) !important;
    -webkit-backdrop-filter: blur(8px) saturate(125%) !important;
    border-radius: 26px !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    box-shadow: 0 25px 60px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.09) !important;
    transition: transform 0.6s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.6s ease, border-color 0.3s ease;
}

[data-theme="light"] .fullscreen-section,
.light-mode .fullscreen-section,
body:has(#portfolioThemeToggle:checked) .fullscreen-section {
    background: rgba(255, 255, 255, 0.52) !important;
    backdrop-filter: blur(8px) saturate(125%) !important;
    -webkit-backdrop-filter: blur(8px) saturate(125%) !important;
    border: 1px solid rgba(255, 255, 255, 0.8) !important;
    box-shadow: 0 20px 45px rgba(15, 23, 42, 0.06), inset 0 1px 0 rgba(255, 255, 255, 0.9) !important;
}

/* Halaman Home di awal buka dan saat navigasi berada persis di tengah layar (jarak simetris di bawah navbar & di atas batas layar) */
.hero-section,
#home {
    margin-top: clamp(92px, 11vh, 105px) !important;
    scroll-margin-top: clamp(92px, 11vh, 105px) !important;
}

.hero-section .hero-container {
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    margin: auto 0 !important;
    width: 100% !important;
}

@media (max-height: 720px), (max-width: 991px) {
    .fullscreen-section {
        height: auto !important;
        min-height: 85vh !important;
        max-height: none !important;
        overflow: visible !important;
        padding: clamp(1.5rem, 2.5vh, 2rem) 1.25rem !important;
        border-radius: 20px !important;
    }
    .hero-section,
    #home {
        margin-top: 80px !important;
        scroll-margin-top: 80px !important;
    }
}

.section-inner {
    width: 100%;
    max-width: 1280px;
    margin: 0 auto;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    justify-content: center;
    position: relative;
}

/* Smooth section entrance on navigation */
@keyframes sectionEnter {
    0% {
        opacity: 0.65;
        transform: translateY(18px) scale(0.99);
    }
    100% {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
}

.fullscreen-section:target .section-inner {
    animation: sectionEnter 0.65s cubic-bezier(0.16, 1, 0.3, 1) both;
}

/* ========== FIXED DELICATE ANIMATED BACKGROUND (TETAP & PALING BELAKANG) ========== */
.fixed-ambient-bg {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    z-index: -1 !important;
    pointer-events: none !important;
    overflow: hidden !important;
    contain: strict;
}

.bg-deep-canvas {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: radial-gradient(ellipse at 50% 30%, #0d1326 0%, #080c18 60%, #040710 100%);
}

.bg-cyber-grid {
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background-image: linear-gradient(rgba(99, 102, 241, 0.05) 1px, transparent 1px),
                      linear-gradient(90deg, rgba(99, 102, 241, 0.05) 1px, transparent 1px);
    background-size: 55px 55px;
    background-position: 0 0;
    animation: driftGrid 50s linear infinite;
    pointer-events: none;
    opacity: 0.78;
}

@keyframes driftGrid {
    0% { transform: translate(0, 0); }
    100% { transform: translate(55px, 55px); }
}

.ambient-orb {
    position: absolute;
    border-radius: 50%;
    filter: blur(85px);
    pointer-events: none;
    opacity: 0.32;
    will-change: transform;
}

.orb-primary {
    top: 15%;
    left: 10%;
    width: clamp(350px, 45vw, 650px);
    height: clamp(350px, 45vw, 650px);
    background: radial-gradient(circle, #6366f1 0%, rgba(99, 102, 241, 0) 70%);
    animation: orbFloat1 28s ease-in-out infinite alternate;
}

.orb-secondary {
    bottom: 12%;
    right: 8%;
    width: clamp(380px, 48vw, 700px);
    height: clamp(380px, 48vw, 700px);
    background: radial-gradient(circle, #8b5cf6 0%, rgba(139, 92, 246, 0) 70%);
    animation: orbFloat2 32s ease-in-out infinite alternate;
}

.orb-accent {
    top: 55%;
    left: 45%;
    width: clamp(300px, 35vw, 500px);
    height: clamp(300px, 35vw, 500px);
    background: radial-gradient(circle, #38bdf8 0%, rgba(56, 189, 248, 0) 70%);
    opacity: 0.22;
    animation: orbFloat3 24s ease-in-out infinite alternate;
}

@keyframes orbFloat1 {
    0% { transform: translate(0, 0) scale(1); }
    50% { transform: translate(60px, 45px) scale(1.12); }
    100% { transform: translate(-40px, 80px) scale(0.92); }
}

@keyframes orbFloat2 {
    0% { transform: translate(0, 0) scale(1); }
    50% { transform: translate(-70px, -50px) scale(1.15); }
    100% { transform: translate(50px, -30px) scale(0.9); }
}

@keyframes orbFloat3 {
    0% { transform: translate(0, 0) scale(0.95); }
    50% { transform: translate(-40px, 60px) scale(1.18); }
    100% { transform: translate(40px, -45px) scale(1.02); }
}

.bg-constellation-svg {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
}

.star-pulse {
    animation: starPulseAnim 4s ease-in-out infinite alternate;
}
.s1 { animation-delay: 0s; }
.s2 { animation-delay: 1.1s; }
.s3 { animation-delay: 2.2s; }
.s4 { animation-delay: 3.1s; }

@keyframes starPulseAnim {
    0% { opacity: 0.35; transform: scale(0.85); }
    50% { opacity: 1; transform: scale(1.4); }
    100% { opacity: 0.35; transform: scale(0.85); }
}

.star-sparkle {
    animation: sparkleGlow 5s ease-in-out infinite alternate;
}
.sp1 { animation-delay: 0.4s; }
.sp2 { animation-delay: 1.8s; }
.sp3 { animation-delay: 3.2s; }

@keyframes sparkleGlow {
    0% { opacity: 0.25; transform: scale(0.8) rotate(0deg); }
    50% { opacity: 0.85; transform: scale(1.3) rotate(45deg); filter: drop-shadow(0 0 6px #c084fc); }
    100% { opacity: 0.25; transform: scale(0.8) rotate(90deg); }
}

[data-theme="light"] .bg-deep-canvas,
.light-mode .bg-deep-canvas,
body:has(#portfolioThemeToggle:checked) .bg-deep-canvas {
    background: radial-gradient(ellipse at 50% 30%, #f8fafc 0%, #edf2f7 60%, #e2e8f0 100%) !important;
}
[data-theme="light"] .bg-cyber-grid,
.light-mode .bg-cyber-grid,
body:has(#portfolioThemeToggle:checked) .bg-cyber-grid {
    background-image: linear-gradient(rgba(99, 102, 241, 0.08) 1px, transparent 1px),
                      linear-gradient(90deg, rgba(99, 102, 241, 0.08) 1px, transparent 1px) !important;
    opacity: 0.8 !important;
}
[data-theme="light"] .ambient-orb,
.light-mode .ambient-orb,
body:has(#portfolioThemeToggle:checked) .ambient-orb {
    opacity: 0.16 !important;
}

/* ========== TRANSPARENT GAP BETWEEN SECTIONS (NO BADGE / NO BEAM) ========== */
.section-window-separator {
    display: none !important;
}

/* ========== ABOUT SECTION ========== */
.about-section {
    position: relative;
}

.about-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 3.5rem;
    align-items: center;
    width: 100%;
}

.stats-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.2rem;
    width: 100%;
}

/* ========== SKILLS SECTION ========== */
.skills-section {
    border-top: 1px solid var(--border-color);
}

.skills-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 2.2rem;
    width: 100%;
    margin-top: 0.5rem;
}

/* ========== PROJECTS SECTION ========== */
.projects-section {
    border-top: 1px solid var(--border-color);
}

.projects-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.8rem;
    width: 100%;
}

/* ========== BLOG SECTION ========== */
.blog-section {
    border-top: 1px solid var(--border-color);
}

.blog-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.8rem;
    width: 100%;
}

/* ========== FOOTER / CTA SECTION ========== */
.footer-section {
    border-top: 1px solid var(--border-color);
    justify-content: space-between;
}

.contact-inner {
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding-top: 0 !important;
}

.contact-grid {
    display: grid;
    grid-template-columns: 1fr 1.2fr 0.8fr;
    gap: 2.5rem;
    align-items: start;
    width: 100%;
}

/* ========== VERTICAL SLIDE NAVIGATION DOTS ========== */
.scroll-nav-dots {
    display: none !important;
}

.scroll-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.25);
    border: 1px solid rgba(255, 255, 255, 0.15);
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    display: block;
    position: relative;
    cursor: pointer;
    text-decoration: none !important;
}

.scroll-dot:hover {
    background: #818cf8;
    transform: scale(1.35);
    box-shadow: 0 0 10px rgba(99, 102, 241, 0.6);
}

.dot-tooltip {
    position: absolute;
    right: 22px;
    top: 50%;
    transform: translateY(-50%) translateX(6px);
    background: rgba(15, 23, 42, 0.92);
    backdrop-filter: blur(8px);
    color: #ffffff;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 5px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    white-space: nowrap;
    opacity: 0;
    pointer-events: none;
    transition: all 0.2s ease;
    font-family: 'Inter', sans-serif;
}

.scroll-dot:hover .dot-tooltip {
    opacity: 1;
    transform: translateY(-50%) translateX(0);
}

/* Active dot styling via :target */
body:has(#home:target) .scroll-nav-dots a[href="#home"],
body:not(:has(:target)) .scroll-nav-dots a[href="#home"],
body:has(#about:target) .scroll-nav-dots a[href="#about"],
body:has(#skills:target) .scroll-nav-dots a[href="#skills"],
body:has(#projects:target) .scroll-nav-dots a[href="#projects"],
body:has(#blog:target) .scroll-nav-dots a[href="#blog"],
body:has(#contact:target) .scroll-nav-dots a[href="#contact"] {
    background: #6366f1 !important;
    height: 24px !important;
    border-radius: 6px !important;
    box-shadow: 0 0 14px rgba(99, 102, 241, 0.8) !important;
}

body:has(#about:target) .scroll-nav-dots a[href="#home"],
body:has(#skills:target) .scroll-nav-dots a[href="#home"],
body:has(#projects:target) .scroll-nav-dots a[href="#home"],
body:has(#blog:target) .scroll-nav-dots a[href="#blog"],
body:has(#contact:target) .scroll-nav-dots a[href="#contact"] {
    background: rgba(255, 255, 255, 0.25) !important;
    height: 10px !important;
    border-radius: 50% !important;
    box-shadow: none !important;
}

/* Light mode for dots */
body:has(#portfolioThemeToggle:checked) .scroll-dot {
    background: rgba(15, 23, 42, 0.2);
    border-color: rgba(15, 23, 42, 0.15);
}

body:has(#portfolioThemeToggle:checked) .scroll-dot:hover {
    background: #4f46e5;
    box-shadow: 0 0 10px rgba(79, 70, 229, 0.4);
}

body:has(#portfolioThemeToggle:checked) .dot-tooltip {
    background: rgba(255, 255, 255, 0.95);
    color: #0f172a;
    border-color: #e2e8f0;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

body:has(#portfolioThemeToggle:checked):has(#home:target) .scroll-nav-dots a[href="#home"],
body:has(#portfolioThemeToggle:checked):not(:has(:target)) .scroll-nav-dots a[href="#home"],
body:has(#portfolioThemeToggle:checked):has(#about:target) .scroll-nav-dots a[href="#about"],
body:has(#portfolioThemeToggle:checked):has(#skills:target) .scroll-nav-dots a[href="#skills"],
body:has(#portfolioThemeToggle:checked):has(#projects:target) .scroll-nav-dots a[href="#projects"],
body:has(#portfolioThemeToggle:checked):has(#blog:target) .scroll-nav-dots a[href="#blog"],
body:has(#portfolioThemeToggle:checked):has(#contact:target) .scroll-nav-dots a[href="#contact"] {
    background: #4f46e5 !important;
    height: 24px !important;
    border-radius: 6px !important;
    box-shadow: 0 0 12px rgba(79, 70, 229, 0.6) !important;
}

body:has(#portfolioThemeToggle:checked):has(#about:target) .scroll-nav-dots a[href="#home"],
body:has(#portfolioThemeToggle:checked):has(#skills:target) .scroll-nav-dots a[href="#home"],
body:has(#portfolioThemeToggle:checked):has(#projects:target) .scroll-nav-dots a[href="#home"],
body:has(#portfolioThemeToggle:checked):has(#blog:target) .scroll-nav-dots a[href="#blog"],
body:has(#portfolioThemeToggle:checked):has(#contact:target) .scroll-nav-dots a[href="#contact"] {
    background: rgba(15, 23, 42, 0.2) !important;
    height: 10px !important;
    border-radius: 50% !important;
    box-shadow: none !important;
}

@media (max-width: 1024px) {
    .scroll-nav-dots {
        display: none !important;
    }
}

/* ========== ABOUT SECTION ========== */
.about-section {
    position: relative;
}

.about-badge {
    display: inline-block;
    background: rgba(99, 102, 241, 0.12);
    color: var(--accent-purple-hover);
    padding: 0.35rem 0.9rem;
    border-radius: 6px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 1.5px;
    font-family: 'Inter', sans-serif;
    margin-bottom: 1rem;
    border: 1px solid rgba(99, 102, 241, 0.2);
}

.about-heading {
    font-family: 'Inter', sans-serif;
    font-size: 2rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 1.5rem;
    line-height: 1.3;
}

.about-text {
    font-family: 'Inter', sans-serif;
    font-size: 0.95rem;
    color: var(--text-secondary);
    line-height: 1.8;
    margin-bottom: 2rem;
}

.about-btn {
    background: transparent;
    color: var(--text-primary);
    padding: 0.7rem 1.3rem;
    border-radius: 10px;
    text-decoration: none;
    font-size: 0.9rem;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    border: 1px solid var(--border-color);
    transition: all 0.3s;
}

.about-btn:hover {
    background: var(--bg-card);
    border-color: var(--accent-purple);
    color: white;
    text-decoration: none;
}

/* Stat Cards */
.stat-card {
    background: rgba(21, 28, 44, 0.52);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 16px;
    padding: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    transition: transform 0.3s, border-color 0.3s, box-shadow 0.3s;
}

.stat-card:hover {
    transform: translateY(-4px);
    border-color: rgba(99, 102, 241, 0.4);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.35);
    background: rgba(21, 28, 44, 0.72);
}

.stat-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    background: rgba(99, 102, 241, 0.12);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.stat-icon svg {
    width: 24px;
    height: 24px;
    color: var(--accent-purple-hover);
}

.stat-number {
    font-family: 'Inter', sans-serif;
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1;
    margin-bottom: 0.2rem;
}

.stat-label {
    font-family: 'Inter', sans-serif;
    font-size: 0.8rem;
    color: var(--text-secondary);
}

/* ========== SKILLS SECTION ========== */
.skills-section {
    border-top: 1px solid var(--border-color);
}

.skill-item {
    margin-bottom: 1.5rem;
}

.skill-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.6rem;
}

.skill-name-group {
    display: flex;
    align-items: center;
    gap: 0.6rem;
}

.skill-icon {
    width: 28px;
    height: 28px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.7rem;
    font-weight: 700;
}

.skill-name {
    font-family: 'Inter', sans-serif;
    font-size: 0.9rem;
    font-weight: 500;
    color: var(--text-primary);
}

.skill-pct {
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text-secondary);
}

.skill-bar-bg {
    width: 100%;
    height: 8px;
    background: var(--bg-secondary);
    border-radius: 4px;
    overflow: hidden;
}

.skill-bar-fill {
    height: 100%;
    border-radius: 4px;
    background: var(--gradient-purple);
    transition: width 1s ease-in-out;
}

/* ========== PROJECTS SECTION ========== */
.projects-section {
    border-top: 1px solid var(--border-color);
}

.project-card {
    background: rgba(21, 28, 44, 0.52);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 16px;
    overflow: hidden;
    transition: transform 0.3s, box-shadow 0.3s, border-color 0.3s;
    height: 100%;
}

.project-card:hover {
    transform: translateY(-6px);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.45);
    border-color: rgba(99, 102, 241, 0.4);
    background: rgba(21, 28, 44, 0.75);
}

.project-image {
    width: 100%;
    height: clamp(140px, 18vh, 195px);
    object-fit: cover;
    background: linear-gradient(135deg, #1a1a3e, #2d1b69, #0b0f19);
    position: relative;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
}

.project-thumbnail-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: center top;
    display: block;
    transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1), filter 0.3s ease;
}

.project-card:hover .project-thumbnail-img {
    transform: scale(1.06);
    filter: brightness(1.08);
}

.project-number {
    position: absolute;
    top: 12px;
    left: 12px;
    background: rgba(11, 15, 25, 0.78);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    color: var(--accent-purple-hover);
    padding: 0.25rem 0.6rem;
    border-radius: 6px;
    font-size: 0.7rem;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
    border: 1px solid rgba(99, 102, 241, 0.4);
    z-index: 3 !important;
}

.project-mockup {
    font-size: 3rem;
    opacity: 0.6;
}

.project-info {
    padding: 1.2rem 1.4rem;
}

.project-title {
    font-family: 'Inter', sans-serif;
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
}

.project-desc {
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    color: var(--text-secondary);
    line-height: 1.6;
    margin-bottom: 1rem;
}

.project-link {
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    color: var(--accent-purple-hover);
    text-decoration: none;
    font-weight: 600;
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    transition: color 0.3s, gap 0.3s;
}

.project-link:hover {
    color: var(--accent-purple);
    gap: 0.7rem;
}

/* ========== FOOTER / CTA SECTION ========== */
.footer-section {
    border-top: 1px solid var(--border-color);
}

.footer-label {
    font-family: 'Inter', sans-serif;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 2px;
    color: var(--accent-purple-hover);
    margin-bottom: 0.8rem;
}

.footer-heading {
    font-family: 'Inter', sans-serif;
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1.3;
    margin-bottom: 1rem;
}

.footer-text {
    font-family: 'Inter', sans-serif;
    font-size: 0.9rem;
    color: var(--text-secondary);
    line-height: 1.7;
    margin-bottom: 1.5rem;
}

.cta-btn {
    background: var(--gradient-purple);
    color: white;
    padding: 0.7rem 1.3rem;
    border-radius: 10px;
    text-decoration: none;
    font-size: 0.9rem;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    border: none;
    cursor: pointer;
    box-shadow: 0 4px 15px var(--accent-purple-glow);
    transition: transform 0.2s, box-shadow 0.3s;
}

.cta-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 30px var(--accent-purple-glow);
    color: white;
    text-decoration: none;
}

/* Testimonial card */
.testimonial-card {
    background: rgba(21, 28, 44, 0.52);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 16px;
    padding: 1.8rem;
    position: relative;
}

.testimonial-quote-icon {
    font-size: 2.5rem;
    color: var(--accent-purple);
    line-height: 1;
    margin-bottom: 0.8rem;
    font-family: Georgia, serif;
}

.testimonial-text {
    font-family: 'Inter', sans-serif;
    font-size: 0.9rem;
    color: var(--text-secondary);
    line-height: 1.7;
    font-style: italic;
    margin-bottom: 1.2rem;
}

.testimonial-author {
    display: flex;
    align-items: center;
    gap: 0.8rem;
}

.testimonial-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--accent-purple), #8b5cf6);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    color: white;
    font-weight: 600;
}

.testimonial-author-name {
    font-family: 'Inter', sans-serif;
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--text-primary);
}

.testimonial-author-role {
    font-family: 'Inter', sans-serif;
    font-size: 0.75rem;
    color: var(--text-muted);
}

/* Social Icons */
.social-icons {
    display: flex;
    gap: 0.8rem;
    margin-bottom: 1.2rem;
}

.social-icon {
    width: 42px;
    height: 42px;
    border-radius: 10px;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-secondary);
    text-decoration: none;
    font-size: 1.1rem;
    transition: all 0.3s;
}

.social-icon:hover {
    background: var(--accent-purple);
    border-color: var(--accent-purple);
    color: white;
    transform: translateY(-3px);
}

.contact-item {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-bottom: 0.7rem;
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    color: var(--text-secondary);
}

.contact-item svg {
    width: 16px;
    height: 16px;
    color: var(--accent-purple-hover);
    flex-shrink: 0;
}

/* Copyright */
.copyright-bar {
    border-top: 1px solid var(--border-color);
    padding: 1.5rem 0;
    margin-top: 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
}

.copyright-text {
    font-family: 'Inter', sans-serif;
    font-size: 0.8rem;
    color: var(--text-muted);
}

.copyright-heart {
    color: #ef4444;
}

/* ========== CAROUSEL DOTS ========== */
.carousel-dots {
    display: flex;
    justify-content: center;
    gap: 0.5rem;
    margin-top: 1.5rem;
}

.carousel-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--text-muted);
    transition: all 0.3s;
}

.carousel-dot.active {
    background: var(--accent-purple);
    width: 24px;
    border-radius: 4px;
}

/* ========== SPECTACULAR CINEMATIC SHUTTER & KINETIC ENTRANCE ========== */
.cinematic-curtain {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    background: radial-gradient(ellipse at center, #171d36 0%, #0d1226 50%, #050814 100%) !important;
    z-index: 9999999 !important;
    pointer-events: auto !important;
    cursor: pointer !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    overflow: hidden !important;
    opacity: 1 !important;
    visibility: visible !important;
    transition: opacity 0.45s 0.8s ease, visibility 0.45s 0.8s ease !important;
}

.cinematic-curtain.opened,
body:has(#curtainTrigger:checked) .cinematic-curtain {
    opacity: 0 !important;
    visibility: hidden !important;
    pointer-events: none !important;
}

/* Dua sayap pembelah layar (kiri dan kanan) - Seamless tanpa garis tegak */
.curtain-panel {
    position: absolute !important;
    top: 0 !important;
    width: 51vw !important;
    height: 100vh !important;
    background: radial-gradient(ellipse at center, #171d36 0%, #0d1226 50%, #050814 100%) !important;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    z-index: 1 !important;
    will-change: transform !important;
    transform: translateX(0);
    transition: transform 1.15s cubic-bezier(0.77, 0, 0.175, 1) !important;
}

.curtain-left {
    left: 0 !important;
    border: none !important;
    border-right: none !important;
    transform: translateX(0);
}

.curtain-right {
    right: 0 !important;
    border: none !important;
    border-left: none !important;
    transform: translateX(0);
}

.cinematic-curtain.opened .curtain-left,
body:has(#curtainTrigger:checked) .cinematic-curtain .curtain-left {
    transform: translateX(-145%) !important;
}

.cinematic-curtain.opened .curtain-right,
body:has(#curtainTrigger:checked) .cinematic-curtain .curtain-right {
    transform: translateX(145%) !important;
}

/* Tekstur Cyber Grid Pattern - Menyatu Rata Tanpa Garis Sambungan Tengah */
.curtain-grid-texture {
    display: block !important;
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    width: 100% !important;
    height: 100% !important;
    background-image: linear-gradient(rgba(99, 102, 241, 0.08) 1px, transparent 1px),
                      linear-gradient(90deg, rgba(99, 102, 241, 0.08) 1px, transparent 1px) !important;
    background-size: 38px 38px !important;
    background-position: center center !important;
    pointer-events: none !important;
}

/* Lingkaran Cahaya Ambient Tengah (Bulat / Radial - Bukan Garis Lurus) */
.curtain-ambient-glow {
    position: absolute !important;
    top: 50% !important;
    left: 50% !important;
    transform: translate(-50%, -50%) !important;
    width: min(580px, 85vw) !important;
    height: min(420px, 65vh) !important;
    background: radial-gradient(circle, rgba(99, 102, 241, 0.28) 0%, rgba(168, 85, 247, 0.14) 40%, transparent 70%) !important;
    filter: blur(35px) !important;
    pointer-events: none !important;
    z-index: 2 !important;
    animation: ambientGlowPulse 3.8s ease-in-out infinite alternate !important;
}

@keyframes ambientGlowPulse {
    0% { opacity: 0.65; transform: translate(-50%, -50%) scale(0.92); }
    100% { opacity: 1; transform: translate(-50%, -50%) scale(1.08); }
}

/* Tidak ada garis laser lurus ke bawah */
.curtain-laser {
    display: none !important;
}

/* Konten Pembuka: Logo, Title & Tombol Masuk */
.curtain-content {
    position: relative !important;
    z-index: 4 !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
    opacity: 1 !important;
    transform: scale(1) !important;
    transition: transform 0.65s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.65s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

.cinematic-curtain.opened .curtain-content,
body:has(#curtainTrigger:checked) .cinematic-curtain .curtain-content {
    animation: wordExplosionClick 0.75s cubic-bezier(0.16, 1, 0.3, 1) forwards !important;
    pointer-events: none !important;
}

@keyframes wordExplosionClick {
    0% {
        transform: scale(1);
        opacity: 1;
        filter: blur(0);
    }
    35% {
        transform: scale(1.12);
        opacity: 1;
        filter: blur(1px);
        text-shadow: 0 0 35px #818cf8, 0 0 75px #c084fc;
    }
    100% {
        transform: scale(1.9);
        opacity: 0;
        filter: blur(18px);
    }
}

.curtain-logo {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-bottom: 0.8rem;
}

.curtain-logo-icon {
    width: 36px;
    height: 36px;
    filter: drop-shadow(0 0 10px #818cf8);
}

.curtain-logo-text {
    font-family: 'Inter', sans-serif;
    font-size: 1.25rem;
    font-weight: 800;
    letter-spacing: 2px;
    color: #ffffff;
    text-shadow: 0 0 15px rgba(99, 102, 241, 0.8);
}

.curtain-title {
    font-family: 'Inter', sans-serif;
    font-size: clamp(2rem, 6vw, 3.8rem);
    font-weight: 900;
    letter-spacing: 5px;
    line-height: 1.1;
    color: #ffffff;
    display: flex;
    gap: 0.8rem;
    flex-wrap: wrap;
    justify-content: center;
}

.word-welcome {
    background: linear-gradient(135deg, #ffffff 15%, #818cf8 60%, #c084fc 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 0 0 35px rgba(129, 140, 248, 0.7);
    letter-spacing: 7px;
}

.word-wahyu {
    background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 0 0 30px rgba(255, 255, 255, 0.5);
}

.word-pamungkas {
    background: linear-gradient(135deg, #818cf8 0%, #c084fc 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 0 0 40px rgba(129, 140, 248, 0.8);
}

.curtain-badge {
    font-family: 'Inter', sans-serif;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 4px;
    color: #94a3b8;
    margin-top: 0.6rem;
    text-transform: uppercase;
}

/* Tombol Spektakuler Masuk (Click to Enter) */
.curtain-enter-btn {
    margin-top: 2rem;
    display: inline-flex;
    align-items: center;
    gap: 0.65rem;
    padding: 0.85rem 2.4rem;
    background: rgba(99, 102, 241, 0.16);
    border: 1.5px solid rgba(129, 140, 248, 0.55);
    border-radius: 999px;
    color: #ffffff;
    font-family: 'Inter', sans-serif;
    font-size: 0.88rem;
    font-weight: 700;
    letter-spacing: 3px;
    cursor: pointer;
    box-shadow: 0 0 25px rgba(99, 102, 241, 0.35), inset 0 0 15px rgba(129, 140, 248, 0.2);
    position: relative;
    overflow: hidden;
    transition: all 0.35s ease;
    animation: enterBtnGlow 2.4s ease-in-out infinite alternate;
}

.curtain-enter-btn:hover {
    background: rgba(99, 102, 241, 0.3);
    border-color: #c084fc;
    box-shadow: 0 0 35px rgba(168, 85, 247, 0.6), inset 0 0 20px rgba(129, 140, 248, 0.4);
    transform: scale(1.05);
}

@keyframes enterBtnGlow {
    0% {
        box-shadow: 0 0 18px rgba(99, 102, 241, 0.3), inset 0 0 10px rgba(129, 140, 248, 0.15);
        border-color: rgba(129, 140, 248, 0.45);
    }
    100% {
        box-shadow: 0 0 35px rgba(168, 85, 247, 0.65), inset 0 0 20px rgba(192, 132, 252, 0.35);
        border-color: #c084fc;
    }
}

.enter-sparkle {
    color: #c084fc;
    font-size: 0.95rem;
    text-shadow: 0 0 10px #818cf8;
    animation: sparkleSpin 3s linear infinite;
}

@keyframes sparkleSpin {
    0% { transform: scale(0.9) rotate(0deg); opacity: 0.7; }
    50% { transform: scale(1.2) rotate(180deg); opacity: 1; }
    100% { transform: scale(0.9) rotate(360deg); opacity: 0.7; }
}

.curtain-hint {
    margin-top: 0.85rem;
    font-family: 'Inter', sans-serif;
    font-size: 0.75rem;
    font-weight: 500;
    color: #94a3b8;
    letter-spacing: 1.5px;
    opacity: 0.85;
}

/* Partikel & Serpihan Kata Menyebar (Shards Dispersion) */
.curtain-particles {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 100%;
    height: 100%;
    pointer-events: none;
}

.c-particle {
    position: absolute;
    font-size: 1.5rem;
    color: #c084fc;
    text-shadow: 0 0 15px #818cf8, 0 0 30px rgba(168, 85, 247, 0.6);
    pointer-events: none;
    animation: particleFloatIdle 3.2s ease-in-out infinite alternate;
}

.p1 { top: 22%; left: 24%; animation-delay: 0s; }
.p2 { top: 26%; right: 24%; animation-delay: 0.6s; }
.p3 { top: 68%; left: 26%; animation-delay: 1.2s; }
.p4 { top: 72%; right: 26%; animation-delay: 1.8s; }
.p5 { top: 16%; left: 48%; animation-delay: 0.9s; }
.p6 { top: 82%; left: 52%; animation-delay: 1.5s; }
.p7 { top: 48%; left: 16%; animation-delay: 0.3s; }
.p8 { top: 50%; right: 16%; animation-delay: 2.1s; }

@keyframes particleFloatIdle {
    0% { opacity: 0.35; transform: scale(0.85) translateY(0); }
    50% { opacity: 1; transform: scale(1.2) translateY(-10px) rotate(45deg); filter: drop-shadow(0 0 10px #c084fc); }
    100% { opacity: 0.35; transform: scale(0.85) translateY(0); }
}

.cinematic-curtain.opened .p1, body:has(#curtainTrigger:checked) .cinematic-curtain .p1 { animation: burstP1 0.85s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
.cinematic-curtain.opened .p2, body:has(#curtainTrigger:checked) .cinematic-curtain .p2 { animation: burstP2 0.85s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
.cinematic-curtain.opened .p3, body:has(#curtainTrigger:checked) .cinematic-curtain .p3 { animation: burstP3 0.85s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
.cinematic-curtain.opened .p4, body:has(#curtainTrigger:checked) .cinematic-curtain .p4 { animation: burstP4 0.85s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
.cinematic-curtain.opened .p5, body:has(#curtainTrigger:checked) .cinematic-curtain .p5 { animation: burstP5 0.85s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
.cinematic-curtain.opened .p6, body:has(#curtainTrigger:checked) .cinematic-curtain .p6 { animation: burstP6 0.85s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
.cinematic-curtain.opened .p7, body:has(#curtainTrigger:checked) .cinematic-curtain .p7 { animation: burstP7 0.85s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
.cinematic-curtain.opened .p8, body:has(#curtainTrigger:checked) .cinematic-curtain .p8 { animation: burstP8 0.85s cubic-bezier(0.16, 1, 0.3, 1) forwards; }

@keyframes burstP1 { 0% { opacity: 1; transform: translate(-50%, -50%) scale(0.6); } 100% { opacity: 0; transform: translate(-260px, -200px) rotate(180deg) scale(1.8); } }
@keyframes burstP2 { 0% { opacity: 1; transform: translate(-50%, -50%) scale(0.6); } 100% { opacity: 0; transform: translate(260px, -180px) rotate(-180deg) scale(1.8); } }
@keyframes burstP3 { 0% { opacity: 1; transform: translate(-50%, -50%) scale(0.6); } 100% { opacity: 0; transform: translate(-300px, 160px) rotate(140deg) scale(1.8); } }
@keyframes burstP4 { 0% { opacity: 1; transform: translate(-50%, -50%) scale(0.6); } 100% { opacity: 0; transform: translate(280px, 190px) rotate(-140deg) scale(1.8); } }
@keyframes burstP5 { 0% { opacity: 1; transform: translate(-50%, -50%) scale(0.6); } 100% { opacity: 0; transform: translate(0px, -260px) rotate(90deg) scale(2); } }
@keyframes burstP6 { 0% { opacity: 1; transform: translate(-50%, -50%) scale(0.6); } 100% { opacity: 0; transform: translate(0px, 260px) rotate(-90deg) scale(2); } }
@keyframes burstP7 { 0% { opacity: 1; transform: translate(-340px, 0px) rotate(220deg) scale(2); } 100% { opacity: 0; transform: translate(-420px, 0px) scale(0); } }
@keyframes burstP8 { 0% { opacity: 1; transform: translate(340px, 0px) rotate(-220deg) scale(2); } 100% { opacity: 0; transform: translate(420px, 0px) scale(0); } }

/* Kinetic Typography: Kata-kata Halaman Utama Meluncur Masuk Secara Spektakuler */
#home.in-view .hero-badge {
    animation: kineticSlideBadge 0.9s 0.15s cubic-bezier(0.16, 1, 0.3, 1) both;
}
@keyframes kineticSlideBadge {
    0% {
        opacity: 0;
        transform: translateY(-30px) scale(0.85);
        letter-spacing: 5px;
    }
    100% {
        opacity: 1;
        transform: translateY(0) scale(1);
        letter-spacing: 1.5px;
    }
}

.hero-title .slide-word {
    display: inline-block;
    will-change: transform, opacity, filter;
}

#home.in-view .hero-title .line-1 {
    animation: kineticSlideLine1 1.05s 0.25s cubic-bezier(0.16, 1, 0.3, 1) both;
}
@keyframes kineticSlideLine1 {
    0% {
        opacity: 0;
        transform: translateY(50px) rotateX(-25deg);
        filter: blur(14px);
    }
    100% {
        opacity: 1;
        transform: translateY(0) rotateX(0deg);
        filter: blur(0);
    }
}

#home.in-view .hero-title .line-2 {
    animation: kineticSlideLine2 1.05s 0.38s cubic-bezier(0.16, 1, 0.3, 1) both;
}
@keyframes kineticSlideLine2 {
    0% {
        opacity: 0;
        transform: translateY(50px) rotateX(-25deg);
        filter: blur(14px);
    }
    100% {
        opacity: 1;
        transform: translateY(0) rotateX(0deg);
        filter: blur(0);
    }
}

#home.in-view .hero-desc {
    animation: kineticSlideDesc 0.95s 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
}
@keyframes kineticSlideDesc {
    0% {
        opacity: 0;
        transform: translateY(35px);
        filter: blur(8px);
    }
    100% {
        opacity: 1;
        transform: translateY(0);
        filter: blur(0);
    }
}

#home.in-view .hero-buttons {
    animation: kineticSlideBtns 0.9s 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
}
@keyframes kineticSlideBtns {
    0% {
        opacity: 0;
        transform: translateY(30px) scale(0.92);
    }
    100% {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
}

#home.in-view .hero-tech-stack {
    animation: kineticSlideTech 0.9s 0.7s cubic-bezier(0.16, 1, 0.3, 1) both;
}
@keyframes kineticSlideTech {
    0% {
        opacity: 0;
        transform: translateY(25px);
    }
    100% {
        opacity: 1;
        transform: translateY(0);
    }
}

#home.in-view .hero-visual-col {
    animation: kineticSlideVisual 1.15s 0.25s cubic-bezier(0.16, 1, 0.3, 1) both;
}
@keyframes kineticSlideVisual {
    0% {
        opacity: 0;
        transform: scale(0.85) translateY(45px);
        filter: blur(14px);
    }
    100% {
        opacity: 1;
        transform: scale(1) translateY(0);
        filter: blur(0);
    }
}

#home.in-view .code-snippet-box {
    animation: kineticSlideCode 1.05s 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
}
@keyframes kineticSlideCode {
    0% {
        opacity: 0;
        transform: translateY(-42%) scale(0.93);
        filter: blur(8px);
    }
    100% {
        opacity: 1;
        transform: translateY(-50%) scale(1);
        filter: blur(0);
    }
}

/* Light mode for code snippet box */
body:has(#portfolioThemeToggle:checked) .code-snippet-box {
    background: rgba(255, 255, 255, 0.94) !important;
    border-color: rgba(99, 102, 241, 0.22) !important;
    box-shadow: 0 20px 45px rgba(99, 102, 241, 0.16), 0 4px 12px rgba(0, 0, 0, 0.05) !important;
}
body:has(#portfolioThemeToggle:checked) .code-snippet-body {
    color: #475569 !important;
}
body:has(#portfolioThemeToggle:checked) .code-snippet-body .code-var {
    color: #1e293b !important;
}

/* ========== ANIMASI SPEKTAKULER UNTUK SEMUA HALAMAN (HOME, ABOUT, SKILLS, PROJECTS, BLOG, CONTACT) ========== */

/* Efek Shimmer Karakter & Teks Neon Dinamis */
.kinetic-word {
    display: inline-block;
    will-change: transform, opacity, filter;
}

.highlight {
    background: linear-gradient(135deg, #818cf8 0%, #c084fc 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    display: inline-block;
    text-shadow: 0 0 25px rgba(129, 140, 248, 0.4);
}

/* 1. ABOUT ME SECTION ANIMATIONS */
.about-badge {
    animation: badgePulseTracking 1.8s ease-in-out infinite alternate;
}
@keyframes badgePulseTracking {
    0% {
        box-shadow: 0 0 0 rgba(99, 102, 241, 0);
        border-color: rgba(99, 102, 241, 0.25);
    }
    100% {
        box-shadow: 0 0 15px rgba(99, 102, 241, 0.45);
        border-color: rgba(99, 102, 241, 0.7);
    }
}

.about-section.in-view .about-heading,
#about:target .about-heading {
    animation: kineticHeadingReveal 0.9s cubic-bezier(0.16, 1, 0.3, 1) both;
}
@keyframes kineticHeadingReveal {
    0% {
        opacity: 0;
        transform: translateY(35px) rotateX(-15deg);
        filter: blur(10px);
    }
    100% {
        opacity: 1;
        transform: translateY(0) rotateX(0deg);
        filter: blur(0);
    }
}

.about-section.in-view .about-text,
#about:target .about-text {
    animation: kineticTextSlide 0.85s 0.15s cubic-bezier(0.16, 1, 0.3, 1) both;
}
@keyframes kineticTextSlide {
    0% {
        opacity: 0;
        transform: translateY(25px);
    }
    100% {
        opacity: 1;
        transform: translateY(0);
    }
}

.about-section.in-view .about-btn,
#about:target .about-btn {
    animation: kineticBtnBounce 0.85s 0.25s cubic-bezier(0.16, 1, 0.3, 1) both;
}
@keyframes kineticBtnBounce {
    0% {
        opacity: 0;
        transform: scale(0.9) translateY(20px);
    }
    100% {
        opacity: 1;
        transform: scale(1) translateY(0);
    }
}

/* 4 Stat Cards: Staggered 3D Cascading Entrance */
.about-section.in-view .stats-grid .stat-card:nth-child(1),
#about:target .stats-grid .stat-card:nth-child(1) {
    animation: statCardIn 0.8s 0.1s cubic-bezier(0.16, 1, 0.3, 1) both;
}
.about-section.in-view .stats-grid .stat-card:nth-child(2),
#about:target .stats-grid .stat-card:nth-child(2) {
    animation: statCardIn 0.8s 0.22s cubic-bezier(0.16, 1, 0.3, 1) both;
}
.about-section.in-view .stats-grid .stat-card:nth-child(3),
#about:target .stats-grid .stat-card:nth-child(3) {
    animation: statCardIn 0.8s 0.34s cubic-bezier(0.16, 1, 0.3, 1) both;
}
.about-section.in-view .stats-grid .stat-card:nth-child(4),
#about:target .stats-grid .stat-card:nth-child(4) {
    animation: statCardIn 0.8s 0.46s cubic-bezier(0.16, 1, 0.3, 1) both;
}

@keyframes statCardIn {
    0% {
        opacity: 0;
        transform: translateX(40px) translateY(20px) rotateY(-10deg);
        filter: blur(8px);
    }
    100% {
        opacity: 1;
        transform: translateX(0) translateY(0) rotateY(0deg);
        filter: blur(0);
    }
}

.stat-number {
    animation: statNumGlow 3s ease-in-out infinite alternate;
}
@keyframes statNumGlow {
    0% {
        text-shadow: 0 0 10px rgba(99, 102, 241, 0.3);
    }
    100% {
        text-shadow: 0 0 25px rgba(129, 140, 248, 0.8), 0 0 40px rgba(192, 132, 252, 0.5);
    }
}

.stat-icon {
    animation: iconGentleFloat 4s ease-in-out infinite alternate;
}
@keyframes iconGentleFloat {
    0% { transform: translateY(0); }
    100% { transform: translateY(-4px); }
}

/* 2. SKILLS SECTION ANIMATIONS */
.skills-section.in-view .section-title,
#skills:target .section-title {
    animation: kineticHeadingReveal 0.9s cubic-bezier(0.16, 1, 0.3, 1) both;
}

/* 9 Skill Items: Wave Entrance */
.skills-section.in-view .skills-grid .skill-group-col:nth-child(1) .skill-item:nth-child(1),
#skills:target .skills-grid .skill-group-col:nth-child(1) .skill-item:nth-child(1) { animation: skillCascade 0.75s 0.08s cubic-bezier(0.16, 1, 0.3, 1) both; }
.skills-section.in-view .skills-grid .skill-group-col:nth-child(1) .skill-item:nth-child(2),
#skills:target .skills-grid .skill-group-col:nth-child(1) .skill-item:nth-child(2) { animation: skillCascade 0.75s 0.16s cubic-bezier(0.16, 1, 0.3, 1) both; }
.skills-section.in-view .skills-grid .skill-group-col:nth-child(1) .skill-item:nth-child(3),
#skills:target .skills-grid .skill-group-col:nth-child(1) .skill-item:nth-child(3) { animation: skillCascade 0.75s 0.24s cubic-bezier(0.16, 1, 0.3, 1) both; }
.skills-section.in-view .skills-grid .skill-group-col:nth-child(2) .skill-item:nth-child(1),
#skills:target .skills-grid .skill-group-col:nth-child(2) .skill-item:nth-child(1) { animation: skillCascade 0.75s 0.14s cubic-bezier(0.16, 1, 0.3, 1) both; }
.skills-section.in-view .skills-grid .skill-group-col:nth-child(2) .skill-item:nth-child(2),
#skills:target .skills-grid .skill-group-col:nth-child(2) .skill-item:nth-child(2) { animation: skillCascade 0.75s 0.22s cubic-bezier(0.16, 1, 0.3, 1) both; }
.skills-section.in-view .skills-grid .skill-group-col:nth-child(2) .skill-item:nth-child(3),
#skills:target .skills-grid .skill-group-col:nth-child(2) .skill-item:nth-child(3) { animation: skillCascade 0.75s 0.30s cubic-bezier(0.16, 1, 0.3, 1) both; }
.skills-section.in-view .skills-grid .skill-group-col:nth-child(3) .skill-item:nth-child(1),
#skills:target .skills-grid .skill-group-col:nth-child(3) .skill-item:nth-child(1) { animation: skillCascade 0.75s 0.20s cubic-bezier(0.16, 1, 0.3, 1) both; }
.skills-section.in-view .skills-grid .skill-group-col:nth-child(3) .skill-item:nth-child(2),
#skills:target .skills-grid .skill-group-col:nth-child(3) .skill-item:nth-child(2) { animation: skillCascade 0.75s 0.28s cubic-bezier(0.16, 1, 0.3, 1) both; }
.skills-section.in-view .skills-grid .skill-group-col:nth-child(3) .skill-item:nth-child(3),
#skills:target .skills-grid .skill-group-col:nth-child(3) .skill-item:nth-child(3) { animation: skillCascade 0.75s 0.36s cubic-bezier(0.16, 1, 0.3, 1) both; }

@keyframes skillCascade {
    0% {
        opacity: 0;
        transform: translateY(30px) scale(0.94);
        filter: blur(6px);
    }
    100% {
        opacity: 1;
        transform: translateY(0) scale(1);
        filter: blur(0);
    }
}

/* Skill Bar: Dynamic Fill Animation with Laser Shimmer Streak */
.skills-section.in-view .skill-bar-fill,
#skills:target .skill-bar-fill {
    animation: barExpand 1.2s 0.25s cubic-bezier(0.16, 1, 0.3, 1) both;
}
.skill-bar-fill {
    position: relative;
    overflow: hidden;
}
@keyframes barExpand {
    0% {
        width: 0% !important;
        opacity: 0.3;
    }
}

.skill-bar-fill::after {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 60%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.8), transparent);
    animation: barLaserStreak 2.4s infinite ease-in-out;
}
@keyframes barLaserStreak {
    0% { left: -100%; }
    50%, 100% { left: 160%; }
}

.skill-pct {
    animation: pctGlow 2.5s ease-in-out infinite alternate;
}
@keyframes pctGlow {
    0% { color: var(--text-primary); text-shadow: none; }
    100% { color: #818cf8; text-shadow: 0 0 8px rgba(129, 140, 248, 0.7); }
}

/* 3. FEATURED PROJECTS SECTION ANIMATIONS */
.projects-section.in-view .section-title,
#projects:target .section-title {
    animation: kineticHeadingReveal 0.9s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.projects-section.in-view .projects-grid .project-card:nth-child(1),
#projects:target .projects-grid .project-card:nth-child(1) {
    animation: projectCardLeftIn 0.95s 0.1s cubic-bezier(0.16, 1, 0.3, 1) both;
}
.projects-section.in-view .projects-grid .project-card:nth-child(2),
#projects:target .projects-grid .project-card:nth-child(2) {
    animation: projectCardCenterIn 0.95s 0.22s cubic-bezier(0.16, 1, 0.3, 1) both;
}
.projects-section.in-view .projects-grid .project-card:nth-child(3),
#projects:target .projects-grid .project-card:nth-child(3) {
    animation: projectCardRightIn 0.95s 0.34s cubic-bezier(0.16, 1, 0.3, 1) both;
}

@keyframes projectCardLeftIn {
    0% {
        opacity: 0;
        transform: translateX(-45px) translateY(35px) rotate(-3deg);
        filter: blur(8px);
    }
    100% {
        opacity: 1;
        transform: translateX(0) translateY(0) rotate(0deg);
        filter: blur(0);
    }
}
@keyframes projectCardCenterIn {
    0% {
        opacity: 0;
        transform: translateY(50px) scale(0.92);
        filter: blur(8px);
    }
    100% {
        opacity: 1;
        transform: translateY(0) scale(1);
        filter: blur(0);
    }
}
@keyframes projectCardRightIn {
    0% {
        opacity: 0;
        transform: translateX(45px) translateY(35px) rotate(3deg);
        filter: blur(8px);
    }
    100% {
        opacity: 1;
        transform: translateX(0) translateY(0) rotate(0deg);
        filter: blur(0);
    }
}

/* Project Number Badges Glow */
.project-number {
    animation: numBadgeGlow 2.5s ease-in-out infinite alternate;
}
@keyframes numBadgeGlow {
    0% { text-shadow: 0 0 10px rgba(99, 102, 241, 0.4); }
    100% { text-shadow: 0 0 25px rgba(129, 140, 248, 0.9), 0 0 40px rgba(192, 132, 252, 0.6); }
}

/* Animated SVG Chart Line inside Crypto Mockup */
.mockup-inner svg polyline {
    stroke-dasharray: 400;
    stroke-dashoffset: 400;
    animation: drawCryptoLine 2.2s 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards, lineGlow 3s infinite alternate;
}
@keyframes drawCryptoLine {
    to { stroke-dashoffset: 0; }
}
@keyframes lineGlow {
    0% { filter: drop-shadow(0 0 2px rgba(99, 102, 241, 0.3)); }
    100% { filter: drop-shadow(0 0 8px rgba(99, 102, 241, 0.9)); }
}

/* Interactive Project Link Arrow Slide */
.project-link span {
    display: inline-block;
    transition: transform 0.25s ease;
}
.project-card:hover .project-link span {
    transform: translateX(6px);
}

/* 4. LATEST ARTICLES / BLOG SECTION ANIMATIONS */
.blog-section.in-view .section-title,
#blog:target .section-title {
    animation: kineticHeadingReveal 0.9s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.blog-section.in-view .blog-grid > div:nth-child(1),
#blog:target .blog-grid > div:nth-child(1) {
    animation: blogCardIn 0.85s 0.12s cubic-bezier(0.16, 1, 0.3, 1) both;
}
.blog-section.in-view .blog-grid > div:nth-child(2),
#blog:target .blog-grid > div:nth-child(2) {
    animation: blogCardIn 0.85s 0.24s cubic-bezier(0.16, 1, 0.3, 1) both;
}
.blog-section.in-view .blog-grid > div:nth-child(3),
#blog:target .blog-grid > div:nth-child(3) {
    animation: blogCardIn 0.85s 0.36s cubic-bezier(0.16, 1, 0.3, 1) both;
}

@keyframes blogCardIn {
    0% {
        opacity: 0;
        transform: translateY(45px) scale(0.94);
        filter: blur(8px);
    }
    100% {
        opacity: 1;
        transform: translateY(0) scale(1);
        filter: blur(0);
    }
}

/* 5. CONTACT / FOOTER SECTION ANIMATIONS */
.footer-section.in-view .footer-heading,
#contact:target .footer-heading {
    animation: kineticHeadingReveal 0.9s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.footer-section.in-view .contact-col,
#contact:target .contact-col {
    animation: contactColLeft 0.9s 0.1s cubic-bezier(0.16, 1, 0.3, 1) both;
}
@keyframes contactColLeft {
    0% {
        opacity: 0;
        transform: translateX(-40px);
        filter: blur(8px);
    }
    100% {
        opacity: 1;
        transform: translateX(0);
        filter: blur(0);
    }
}

.footer-section.in-view .testimonial-card,
#contact:target .testimonial-card {
    animation: testimonialIn 0.95s 0.22s cubic-bezier(0.16, 1, 0.3, 1) both;
}
@keyframes testimonialIn {
    0% {
        opacity: 0;
        transform: translateY(40px) scale(0.92);
        filter: blur(8px);
    }
    100% {
        opacity: 1;
        transform: translateY(0) scale(1);
        filter: blur(0);
    }
}

.testimonial-quote-icon {
    display: inline-block;
    animation: quotePulseAnim 2.5s ease-in-out infinite alternate;
}
@keyframes quotePulseAnim {
    0% { transform: scale(1); color: #818cf8; text-shadow: 0 0 10px rgba(99, 102, 241, 0.4); }
    100% { transform: scale(1.15); color: #c084fc; text-shadow: 0 0 25px rgba(192, 132, 252, 0.8); }
}

.cta-btn {
    animation: ctaBtnGlow 2.5s infinite alternate;
}
@keyframes ctaBtnGlow {
    0% { box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4); }
    100% { box-shadow: 0 6px 30px rgba(99, 102, 241, 0.8), 0 0 20px rgba(192, 132, 252, 0.5); }
}

.footer-section.in-view .contact-info-col,
#contact:target .contact-info-col {
    animation: contactColRight 0.9s 0.32s cubic-bezier(0.16, 1, 0.3, 1) both;
}
@keyframes contactColRight {
    0% {
        opacity: 0;
        transform: translateX(40px);
        filter: blur(8px);
    }
    100% {
        opacity: 1;
        transform: translateX(0);
        filter: blur(0);
    }
}

.social-icons .social-icon {
    transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.3s ease, border-color 0.3s ease !important;
}
.social-icons .social-icon:hover {
    transform: translateY(-4px) rotate(8deg) scale(1.12) !important;
    border-color: #818cf8 !important;
    box-shadow: 0 0 20px rgba(99, 102, 241, 0.6) !important;
}

.copyright-heart {
    display: inline-block;
    animation: heartBeat 1.4s infinite ease-in-out;
}
@keyframes heartBeat {
    0%, 100% { transform: scale(1); }
    20% { transform: scale(1.3); }
    40% { transform: scale(1.1); }
    60% { transform: scale(1.25); }
}

/* NATIVE SCROLL-DRIVEN ANIMATIONS FOR MODERN CHROMIUM (CHROME & EDGE) */
@supports (animation-timeline: view()) {
    .about-heading, .skills-section .section-title, .projects-section .section-title, .blog-section .section-title, .footer-heading {
        animation: kineticHeadingReveal 0.85s cubic-bezier(0.16, 1, 0.3, 1) both;
        animation-timeline: view();
        animation-range: entry 10% cover 35%;
    }
    .stats-grid .stat-card {
        animation: statCardIn 0.85s cubic-bezier(0.16, 1, 0.3, 1) both;
        animation-timeline: view();
        animation-range: entry 5% cover 30%;
    }
    .skill-bar-fill {
        animation: barExpand 1.1s cubic-bezier(0.16, 1, 0.3, 1) both;
        animation-timeline: view();
        animation-range: entry 10% cover 40%;
    }
    .projects-grid .project-card {
        animation: projectCardCenterIn 0.85s cubic-bezier(0.16, 1, 0.3, 1) both;
        animation-timeline: view();
        animation-range: entry 5% cover 30%;
    }
    .blog-grid > div {
        animation: blogCardIn 0.85s cubic-bezier(0.16, 1, 0.3, 1) both;
        animation-timeline: view();
        animation-range: entry 5% cover 30%;
    }
    .testimonial-card {
        animation: testimonialIn 0.85s cubic-bezier(0.16, 1, 0.3, 1) both;
        animation-timeline: view();
        animation-range: entry 5% cover 30%;
    }
}

/* ========== RESPONSIVE ACROSS ALL DEVICES ========== */
@media (max-width: 1200px) {
    .hero-image-wrapper { max-width: 480px; height: 540px; }
    .hero-digital-system {
        width: clamp(340px, 48vh, 460px) !important;
        height: clamp(340px, 48vh, 460px) !important;
        top: 40% !important;
    }
    .hero-card-frame { height: 540px; max-width: 480px; z-index: 6 !important; }
    .hero-profile-photo, .profile-clean-img { max-height: 540px !important; z-index: 6 !important; transform: scale(1.08) !important; }
    .code-snippet-box {
        top: 67% !important;
        right: 8px !important;
        left: auto !important;
        transform: translateY(-50%) !important;
        width: 220px !important;
        padding: 9px 12px !important;
        z-index: 7 !important;
    }
}

@media (max-width: 992px) {
    /* Responsive layout & disable fullpage locking on tablets/phones for effortless scrolling */
    html, body, .stApp, [data-testid="stAppViewContainer"], .main {
        scroll-snap-type: none !important;
    }
    .fullscreen-section {
        height: auto !important;
        min-height: auto !important;
        max-height: none !important;
        overflow: visible !important;
        padding: clamp(1.8rem, 3vh, 2.5rem) 1.25rem !important;
    }
    .hero-section,
    #home {
        margin-top: 80px !important;
        scroll-margin-top: 80px !important;
    }
    .hero-container {
        flex-direction: column !important;
        gap: 2.5rem !important;
        padding-top: 20px !important;
        text-align: center !important;
    }
    .hero-content-col {
        max-width: 100% !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
    }
    .hero-buttons {
        justify-content: center !important;
    }
    .hero-tech-icons {
        justify-content: center !important;
    }
    .hero-visual-col {
        width: 100% !important;
        min-height: auto !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
    }
    .hero-image-wrapper {
        max-width: clamp(280px, 75vw, 400px) !important;
        height: auto !important;
        min-height: 280px !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
    }
    .hero-digital-system {
        width: clamp(280px, 72vw, 380px) !important;
        height: clamp(280px, 72vw, 380px) !important;
        top: 42% !important;
    }
    .hero-card-frame {
        height: clamp(280px, 45vh, 440px) !important;
        max-width: 100% !important;
        z-index: 6 !important;
    }
    .hero-profile-photo, .profile-clean-img {
        max-height: clamp(300px, 48vh, 460px) !important;
        z-index: 6 !important;
        transform: scale(1.1) !important;
        transform-origin: bottom center !important;
    }
    /* Kode ditempatkan di bawah foto - sama sekali tidak menutupi foto! */
    .code-snippet-box {
        position: relative !important;
        top: auto !important;
        right: auto !important;
        bottom: auto !important;
        left: auto !important;
        transform: none !important;
        margin: 1.5rem auto 0 auto !important;
        width: 92% !important;
        max-width: 320px !important;
        z-index: 3 !important;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.7) !important;
    }
    .about-grid { grid-template-columns: 1fr !important; gap: 2rem !important; }
    .skills-grid { grid-template-columns: repeat(2, 1fr) !important; gap: 1.2rem !important; }
    .projects-grid { grid-template-columns: 1fr !important; gap: 1.5rem !important; }
    .blog-grid { grid-template-columns: 1fr !important; gap: 1.5rem !important; }
    .contact-grid { grid-template-columns: 1fr !important; gap: 2rem !important; }
}

@media (max-width: 768px) {
    .skills-grid { grid-template-columns: 1fr !important; }
    .stats-grid { grid-template-columns: 1fr !important; }
    .navbar {
        padding: 0.6rem 0.85rem !important;
        gap: 0.5rem !important;
    }
    .navbar-links {
        gap: 0.5rem !important;
        overflow-x: auto !important;
        white-space: nowrap !important;
        scrollbar-width: none !important;
        -ms-overflow-style: none !important;
        max-width: 52vw !important;
        padding: 0.2rem 0.2rem !important;
    }
    .navbar-links::-webkit-scrollbar {
        display: none !important;
    }
    .nav-item {
        font-size: 0.82rem !important;
        padding: 0.35rem 0.65rem !important;
    }
    .hire-btn {
        padding: 0.45rem 0.85rem !important;
        font-size: 0.82rem !important;
    }
    .hero-title {
        font-size: clamp(1.8rem, 7vw, 2.6rem) !important;
    }
    .section-title {
        font-size: clamp(1.4rem, 5.5vw, 1.8rem) !important;
    }
    .about-heading {
        font-size: clamp(1.35rem, 5.5vw, 1.8rem) !important;
    }
    .footer-heading {
        font-size: clamp(1.3rem, 5vw, 1.7rem) !important;
    }
    .scroll-nav-dots {
        display: none !important;
    }
}

@media (max-width: 480px) {
    .hero-buttons {
        flex-direction: column !important;
        width: 100% !important;
        max-width: 280px !important;
    }
    .btn-primary, .btn-secondary {
        width: 100% !important;
        justify-content: center !important;
    }
    .stat-card {
        padding: 1.1rem !important;
    }
    .stat-number {
        font-size: 1.8rem !important;
    }
}

/* Project image patterns */
.project-pattern-1 {
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #1e1b4b 100%);
}
.project-pattern-2 {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
}
.project-pattern-3 {
    background: linear-gradient(135deg, #0b0f19 0%, #1a1a3e 50%, #2d1b69 100%);
}

/* Project image inner mockup elements */
.mockup-inner {
    width: 85%;
    height: 75%;
    background: rgba(0,0,0,0.3);
    border-radius: 8px;
    border: 1px solid rgba(255,255,255,0.08);
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.mockup-topbar {
    height: 24px;
    background: rgba(0,0,0,0.4);
    display: flex;
    align-items: center;
    padding: 0 8px;
    gap: 4px;
    flex-shrink: 0;
}

.mockup-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
}

.mockup-dot.red { background: #ff5f56; }
.mockup-dot.yellow { background: #ffbd2e; }
.mockup-dot.green { background: #27c93f; }

.mockup-body {
    flex: 1;
    padding: 10px;
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.mockup-line {
    height: 6px;
    border-radius: 3px;
    background: rgba(255,255,255,0.08);
}

.mockup-line.short { width: 40%; }
.mockup-line.medium { width: 65%; }
.mockup-line.long { width: 85%; }
.mockup-line.accent { background: rgba(99, 102, 241, 0.3); width: 50%; }

.mockup-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
    margin-top: 4px;
}

.mockup-card-mini {
    height: 35px;
    border-radius: 4px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.05);
}

/* Fallback Avatar Silhouette SVG styling */
.avatar-silhouette {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    z-index: 2;
}

.person-head {
    fill: #e2e8f0;
}
.person-body {
    fill: #94a3b8;
}
</style>
""", unsafe_allow_html=True)


# ─── NAVBAR & THEME CONTROLLER ───
is_light_mode = False
try:
    if hasattr(st, "query_params") and st.query_params.get("theme") == "light":
        is_light_mode = True
except Exception:
    pass

checked_attr = "checked" if is_light_mode else ""

navbar_html = f"""<!-- FIXED DELICATE ANIMATED BACKGROUND (TETAP & PALING BELAKANG) -->
<div class="fixed-ambient-bg" aria-hidden="true">
<div class="bg-deep-canvas"></div>
<div class="bg-cyber-grid"></div>
<div class="ambient-orb orb-primary"></div>
<div class="ambient-orb orb-secondary"></div>
<div class="ambient-orb orb-accent"></div>
<svg class="bg-constellation-svg" viewBox="0 0 1440 900" preserveAspectRatio="xMidYMid slice" fill="none" xmlns="http://www.w3.org/2000/svg">
<g class="constellation-network" opacity="0.45">
<line x1="120" y1="180" x2="280" y2="120" stroke="#818cf8" stroke-width="0.8" stroke-dasharray="4 6" />
<line x1="280" y1="120" x2="420" y2="240" stroke="#6366f1" stroke-width="0.8" stroke-dasharray="3 5" />
<line x1="420" y1="240" x2="560" y2="160" stroke="#c084fc" stroke-width="0.8" stroke-dasharray="6 6" />
<line x1="880" y1="220" x2="1050" y2="150" stroke="#818cf8" stroke-width="0.8" stroke-dasharray="4 6" />
<line x1="1050" y1="150" x2="1240" y2="260" stroke="#6366f1" stroke-width="0.8" stroke-dasharray="5 5" />
<line x1="200" y1="720" x2="380" y2="650" stroke="#c084fc" stroke-width="0.8" stroke-dasharray="4 6" />
<line x1="380" y1="650" x2="540" y2="760" stroke="#818cf8" stroke-width="0.8" stroke-dasharray="5 5" />
<line x1="920" y1="700" x2="1100" y2="620" stroke="#818cf8" stroke-width="0.8" stroke-dasharray="4 6" />
<line x1="1100" y1="620" x2="1280" y2="740" stroke="#c084fc" stroke-width="0.8" stroke-dasharray="5 5" />
<circle cx="120" cy="180" r="2.2" fill="#818cf8" class="star-pulse s1" />
<circle cx="280" cy="120" r="2.6" fill="#c084fc" class="star-pulse s2" />
<circle cx="420" cy="240" r="1.8" fill="#38bdf8" class="star-pulse s3" />
<circle cx="560" cy="160" r="2.2" fill="#818cf8" class="star-pulse s4" />
<circle cx="880" cy="220" r="2.4" fill="#c084fc" class="star-pulse s2" />
<circle cx="1050" cy="150" r="1.8" fill="#38bdf8" class="star-pulse s1" />
<circle cx="1240" cy="260" r="2.6" fill="#818cf8" class="star-pulse s3" />
<circle cx="200" cy="720" r="2.2" fill="#818cf8" class="star-pulse s4" />
<circle cx="380" cy="650" r="2.6" fill="#c084fc" class="star-pulse s1" />
<circle cx="540" cy="760" r="1.8" fill="#38bdf8" class="star-pulse s2" />
<circle cx="920" cy="700" r="2.2" fill="#818cf8" class="star-pulse s3" />
<circle cx="1100" cy="620" r="2.6" fill="#c084fc" class="star-pulse s4" />
<circle cx="1280" cy="740" r="1.8" fill="#38bdf8" class="star-pulse s1" />
<text x="320" y="380" font-size="12" fill="#818cf8" opacity="0.6" class="star-sparkle sp1">✦</text>
<text x="820" y="440" font-size="11" fill="#c084fc" opacity="0.5" class="star-sparkle sp2">✦</text>
<text x="1150" y="480" font-size="13" fill="#38bdf8" opacity="0.55" class="star-sparkle sp3">✦</text>
<text x="180" y="520" font-size="11" fill="#818cf8" opacity="0.5" class="star-sparkle sp2">✦</text>
<text x="680" y="260" font-size="12" fill="#c084fc" opacity="0.6" class="star-sparkle sp1">✦</text>
</g>
</svg>
</div>

<!-- SPECTACULAR CINEMATIC SHUTTER & EXPLODING WORDS ENTRANCE -->
<input type="checkbox" id="curtainTrigger" style="display:none !important;" />
<div class="cinematic-curtain" id="cinematicIntro" onclick="(function(el){{ el.classList.add('opened'); var cb=document.getElementById('curtainTrigger'); if(cb) cb.checked=true; var h=document.getElementById('home'); if(h){{ h.classList.remove('in-view'); void h.offsetWidth; h.classList.add('in-view'); }} setTimeout(function(){{ el.style.display='none'; }}, 1250); }})(this);">
<div class="curtain-panel curtain-left">
<div class="curtain-grid-texture"></div>
</div>
<div class="curtain-panel curtain-right">
<div class="curtain-grid-texture"></div>
</div>
<div class="curtain-ambient-glow"></div>
<div class="curtain-content">
<div class="curtain-logo">
<svg class="curtain-logo-icon" viewBox="0 0 32 32" fill="none">
<path d="M8 10L3 16L8 22" stroke="#6366f1" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M24 10L29 16L24 22" stroke="#6366f1" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M18 6L14 26" stroke="#c084fc" stroke-width="2.5" stroke-linecap="round"/>
</svg>
<span class="curtain-logo-text">Yuui.Dev</span>
</div>
<div class="curtain-title">
<span class="curtain-word word-welcome">WELCOME</span>
</div>
<div class="curtain-badge">WEB DEVELOPER &amp; DESIGNER</div>
<div class="curtain-enter-btn">
<span class="enter-sparkle">✦</span>
<span class="enter-btn-text">KLIK UNTUK MASUK</span>
<span class="enter-sparkle">✦</span>
</div>
<div class="curtain-hint">Klik di mana saja untuk membuka portfolio</div>
<div class="curtain-particles">
<span class="c-particle p1">✦</span>
<span class="c-particle p2">✦</span>
<span class="c-particle p3">✦</span>
<span class="c-particle p4">✦</span>
<span class="c-particle p5">✦</span>
<span class="c-particle p6">✦</span>
<span class="c-particle p7">✦</span>
<span class="c-particle p8">✦</span>
</div>
</div>
</div>
<div class="navbar">
<a href="#home" class="navbar-brand">
<svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M8 10L3 16L8 22" stroke="#6366f1" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M24 10L29 16L24 22" stroke="#6366f1" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M18 6L14 26" stroke="#818cf8" stroke-width="2" stroke-linecap="round"/>
</svg>
Yuui.Dev
</a>
<div class="navbar-links">
<a href="#home" class="nav-item active">Home</a>
<a href="#about" class="nav-item">About</a>
<a href="#skills" class="nav-item">Skills</a>
<a href="#projects" class="nav-item">Projects</a>
<a href="#blog" class="nav-item">Blog</a>
<a href="#contact" class="nav-item">Contact</a>
</div>
<div class="navbar-actions">
<input type="checkbox" id="portfolioThemeToggle" class="portfolio-theme-toggle-cb" style="display:none !important;" {checked_attr} />
<label for="portfolioThemeToggle" class="theme-toggle-btn" title="Ganti Mode Terang / Gelap" role="button" tabindex="0">
<span class="theme-icon-moon">🌙</span>
<span class="theme-icon-sun">☀️</span>
</label>
<a href="#contact" class="hire-btn">Hire Me <span>↗</span></a>
</div>
</div>
<img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg'/%3E" style="display:none;" onerror="(function(){{try{{var nbs=document.querySelectorAll('.navbar');if(nbs.length>1){{for(var i=0;i<nbs.length-1;i++){{nbs[i].remove();}}}}var nb=document.querySelector('.navbar');if(nb&amp;&amp;nb.parentElement&amp;&amp;nb.parentElement!==document.body){{document.body.appendChild(nb);}}}}catch(e){{}}}})()" />"""

st.markdown(navbar_html, unsafe_allow_html=True)


# ─── HERO SECTION ───
if img_b64:
    img_src = img_b64 if img_b64.startswith("data:") else f"data:image/png;base64,{img_b64}"
    avatar_content = f'<img src="{img_src}" alt="Wahyu Pamungkas" class="hero-profile-photo profile-clean-img" />'
else:
    avatar_content = '<svg class="avatar-silhouette" width="160" height="200" viewBox="0 0 160 200" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="80" cy="55" r="38" fill="#cbd5e1"/><rect x="52" y="45" width="22" height="16" rx="4" stroke="#475569" stroke-width="2.5" fill="none"/><rect x="86" y="45" width="22" height="16" rx="4" stroke="#475569" stroke-width="2.5" fill="none"/><line x1="74" y1="53" x2="86" y2="53" stroke="#475569" stroke-width="2"/><path d="M40 200 C40 145 45 120 80 110 C115 120 120 145 120 200" fill="#334155"/><path d="M65 110 L80 125 L95 110" stroke="#475569" stroke-width="2" fill="none"/></svg>'

if cv_b64:
    cv_download_link = f'href="data:application/pdf;base64,{cv_b64}" download="CV_WAHYU PAMUNGKAS.pdf"'
else:
    cv_download_link = 'href="#"'

hero_html = f"""<section class="fullscreen-section hero-section" id="home">
<div class="section-inner">
<div class="hero-container">
<div class="hero-content-col">
<div class="hero-badge">I'M A WEB DEVELOPER</div>
<h1 class="hero-title">
<span class="slide-word line-1">Hi, I'm <span class="highlight">Wahyu Pamungkas</span></span><br/>
<span class="slide-word line-2">I build things for the web.</span>
</h1>
<p class="hero-desc">
I'm a passionate web developer specializing in building
exceptional digital experiences with modern technologies.
</p>
<div class="hero-buttons">
<a href="#projects" class="btn-primary">View My Work <span>↗</span></a>
<a {cv_download_link} class="btn-secondary" title="Download CV (Wahyu Pamungkas)">Download CV <span>⤓</span></a>
</div>
<div class="hero-tech-stack">
<div class="hero-tech-label">TECHNOLOGIES I WORK WITH</div>
<div class="hero-tech-icons">
<div class="tech-icon tech-html" title="HTML5">
<svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><path d="M1.5 0h21l-1.91 21.563L11.977 24l-8.564-2.438L1.5 0zm7.031 9.75l-.232-2.718 10.059.003.076-.757.076-.771.076-.758H6.792l.61 6.951h7.15l-.274 2.97-2.29.617-2.29-.617-.163-1.756H7.2l.275 3.85 4.513 1.228 4.513-1.232.668-7.018-.028.002H8.53z"/></svg>
</div>
<div class="tech-icon tech-css" title="CSS3">
<svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><path d="M1.5 0h21l-1.91 21.563L11.977 24l-8.565-2.438L1.5 0zm17.09 4.413L5.41 4.41l.213 2.622 10.125.002-.255 2.716h-6.64l.24 2.573h6.182l-.366 3.523-2.91.804-2.956-.81-.188-2.11h-2.61l.29 3.855L12 19.002l4.5-1.244 1.59-13.345z"/></svg>
</div>
<div class="tech-icon tech-js" title="JavaScript">
<span style="font-size:0.95rem;font-weight:800;">JS</span>
</div>
<div class="tech-icon tech-ts" title="TypeScript">
<span style="font-size:0.9rem;font-weight:800;">TS</span>
</div>
<div class="tech-icon tech-react" title="React">
<svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><path d="M14.23 12.004a2.236 2.236 0 0 1-2.235 2.236 2.236 2.236 0 0 1-2.236-2.236 2.236 2.236 0 0 1 2.235-2.236 2.236 2.236 0 0 1 2.236 2.236zm2.648-10.69c-1.346 0-3.107.96-4.888 2.622-1.78-1.653-3.542-2.602-4.887-2.602-.31 0-.592.068-.846.206C4.97 2.252 4.56 4.318 5.128 7.03c-2.81.82-4.627 2.175-4.627 3.645 0 1.468 1.81 2.822 4.612 3.642-.56 2.706-.156 4.77 1.13 5.48.254.14.54.21.852.21 1.346 0 3.107-.96 4.888-2.624 1.78 1.654 3.542 2.603 4.887 2.603.31 0 .592-.068.846-.206 1.286-.71 1.69-2.774 1.128-5.48 2.802-.82 4.613-2.174 4.613-3.644 0-1.47-1.81-2.824-4.613-3.645.563-2.712.16-4.778-1.13-5.488a1.712 1.712 0 0 0-.846-.206z"/></svg>
</div>
<div class="tech-icon tech-node" title="Node.js">
<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M11.998,24c-0.321,0-0.641-0.084-0.922-0.247l-2.936-1.737c-0.438-0.245-0.224-0.332-0.08-0.383 c0.585-0.203,0.703-0.25,1.328-0.604c0.065-0.037,0.151-0.023,0.218,0.017l2.256,1.339c0.082,0.045,0.197,0.045,0.272,0 l8.795-5.076c0.082-0.047,0.134-0.141,0.134-0.238V6.921c0-0.099-0.053-0.192-0.137-0.242l-8.791-5.072 c-0.081-0.047-0.189-0.047-0.271,0L3.075,6.68C2.99,6.729,2.936,6.825,2.936,6.921v10.15c0,0.097,0.054,0.189,0.136,0.235 l2.409,1.392c1.307,0.654,2.108-0.116,2.108-0.89V7.787c0-0.142,0.114-0.253,0.256-0.253h1.115c0.139,0,0.255,0.112,0.255,0.253 v10.021c0,1.745-0.95,2.745-2.604,2.745c-0.508,0-0.909,0-2.026-0.551L2.28,18.675c-0.57-0.329-0.922-0.945-0.922-1.604V6.921 c0-0.659,0.353-1.275,0.922-1.603l8.795-5.082c0.557-0.315,1.296-0.315,1.848,0l8.794,5.082c0.57,0.329,0.924,0.944,0.924,1.603 v10.15c0,0.659-0.354,1.273-0.924,1.604l-8.794,5.078C12.643,23.916,12.324,24,11.998,24z"/></svg>
</div>
<div class="tech-icon tech-git" title="Git">
<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M23.546 10.93L13.067.452c-.604-.603-1.582-.603-2.188 0L8.708 2.627l2.76 2.76c.645-.215 1.379-.07 1.889.441.516.515.658 1.258.438 1.9l2.66 2.66c.645-.222 1.387-.078 1.9.435.72.72.72 1.884 0 2.604-.72.719-1.885.719-2.604 0-.54-.541-.674-1.337-.404-1.996L12.86 8.955v6.525c.176.086.342.203.488.348.713.721.713 1.883 0 2.6-.713.721-1.88.721-2.593 0-.713-.717-.713-1.879 0-2.6.182-.18.387-.316.605-.406V8.835c-.217-.091-.424-.222-.6-.401-.545-.545-.676-1.342-.396-2.009L7.636 3.7.45 10.881c-.6.605-.6 1.584 0 2.189l10.48 10.477c.604.604 1.582.604 2.186 0l10.43-10.43c.605-.603.605-1.582 0-2.187"/></svg>
</div>
</div>
</div>
</div>
<div class="hero-visual-col">
<div class="hero-image-wrapper">
<svg class="hero-dot-grid" width="84" height="56" viewBox="0 0 84 56" fill="none">
<g fill="#4f46e5" opacity="0.65">
<circle cx="6" cy="6" r="2.5"/><circle cx="21" cy="6" r="2.5"/><circle cx="36" cy="6" r="2.5"/><circle cx="51" cy="6" r="2.5"/><circle cx="66" cy="6" r="2.5"/><circle cx="81" cy="6" r="2.5"/>
<circle cx="6" cy="21" r="2.5"/><circle cx="21" cy="21" r="2.5"/><circle cx="36" cy="21" r="2.5"/><circle cx="51" cy="21" r="2.5"/><circle cx="66" cy="21" r="2.5"/><circle cx="81" cy="21" r="2.5"/>
<circle cx="6" cy="36" r="2.5"/><circle cx="21" cy="36" r="2.5"/><circle cx="36" cy="36" r="2.5"/><circle cx="51" cy="36" r="2.5"/><circle cx="66" cy="36" r="2.5"/><circle cx="81" cy="36" r="2.5"/>
<circle cx="6" cy="51" r="2.5"/><circle cx="21" cy="51" r="2.5"/><circle cx="36" cy="51" r="2.5"/><circle cx="51" cy="51" r="2.5"/><circle cx="66" cy="51" r="2.5"/><circle cx="81" cy="51" r="2.5"/>
</g>
</svg>
<svg class="hero-doodle" width="55" height="55" viewBox="0 0 60 60" fill="none" stroke="#a5b4fc" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<path d="M 8 48 C 2 30, 20 18, 32 25 C 42 32, 38 46, 26 44 C 18 42, 22 28, 45 22" />
<path d="M 37 18 L 47 22 L 44 32" />
</svg>
<div class="hero-digital-system">
<svg class="digital-hud-svg" viewBox="0 0 520 520" fill="none" xmlns="http://www.w3.org/2000/svg">
<defs>
<radialGradient id="cyberCoreGrad" cx="50%" cy="50%" r="50%">
<stop offset="0%" stop-color="#4f46e5" />
<stop offset="55%" stop-color="#7c3aed" />
<stop offset="85%" stop-color="#581c87" />
<stop offset="100%" stop-color="#2e1065" />
</radialGradient>
<radialGradient id="cyberBloom" cx="50%" cy="50%" r="50%">
<stop offset="55%" stop-color="#818cf8" stop-opacity="0.32" />
<stop offset="100%" stop-color="#818cf8" stop-opacity="0" />
</radialGradient>
<linearGradient id="radarSweep" x1="0%" y1="0%" x2="100%" y2="100%">
<stop offset="0%" stop-color="#38bdf8" stop-opacity="0.45" />
<stop offset="70%" stop-color="#818cf8" stop-opacity="0.08" />
<stop offset="100%" stop-color="#6366f1" stop-opacity="0" />
</linearGradient>
<filter id="cyberGlow" x="-20%" y="-20%" width="140%" height="140%">
<feGaussianBlur stdDeviation="4" result="blur" />
<feMerge>
<feMergeNode in="blur" />
<feMergeNode in="SourceGraphic" />
</feMerge>
</filter>
<filter id="intenseGlow" x="-30%" y="-30%" width="160%" height="160%">
<feGaussianBlur stdDeviation="7" result="blur1" />
<feGaussianBlur stdDeviation="2.5" result="blur2" />
<feMerge>
<feMergeNode in="blur1" />
<feMergeNode in="blur2" />
<feMergeNode in="SourceGraphic" />
</feMerge>
</filter>
</defs>
<circle cx="260" cy="260" r="248" fill="url(#cyberBloom)" />
<circle cx="260" cy="260" r="182" fill="url(#cyberCoreGrad)" />
<g class="digital-core-grid" opacity="0.35">
<circle cx="260" cy="260" r="148" stroke="#c084fc" stroke-width="1" stroke-dasharray="4 6" />
<circle cx="260" cy="260" r="112" stroke="#818cf8" stroke-width="1.2" stroke-dasharray="10 5" />
<circle cx="260" cy="260" r="78" stroke="#38bdf8" stroke-width="1" stroke-dasharray="2 4" />
<circle cx="260" cy="260" r="42" stroke="#ffffff" stroke-width="1.2" stroke-dasharray="6 6" />
<line x1="85" y1="260" x2="435" y2="260" stroke="#818cf8" stroke-width="1" stroke-dasharray="5 5" />
<line x1="260" y1="85" x2="260" y2="435" stroke="#818cf8" stroke-width="1" stroke-dasharray="5 5" />
<line x1="135" y1="135" x2="385" y2="385" stroke="#c084fc" stroke-width="0.8" stroke-dasharray="3 6" />
<line x1="385" y1="135" x2="135" y2="385" stroke="#c084fc" stroke-width="0.8" stroke-dasharray="3 6" />
</g>
<g class="digital-radar-scanner">
<path d="M 260 260 L 260 78 A 182 182 0 0 1 388 131 Z" fill="url(#radarSweep)" />
<line x1="260" y1="260" x2="260" y2="78" stroke="#38bdf8" stroke-width="2" filter="url(#cyberGlow)" />
</g>
<g class="digital-ring-circuit">
<circle cx="260" cy="260" r="196" stroke="#818cf8" stroke-width="1.8" stroke-dasharray="35 15 10 15 80 20" opacity="0.8" />
<circle cx="260" cy="64" r="4.5" fill="#38bdf8" filter="url(#intenseGlow)" />
<circle cx="456" cy="260" r="4.5" fill="#c084fc" filter="url(#intenseGlow)" />
<circle cx="260" cy="456" r="4.5" fill="#38bdf8" filter="url(#intenseGlow)" />
<circle cx="64" cy="260" r="4.5" fill="#c084fc" filter="url(#intenseGlow)" />
<circle cx="398" cy="122" r="3" fill="#a5b4fc" />
<circle cx="122" cy="398" r="3" fill="#a5b4fc" />
</g>
<g class="digital-ring-telemetry">
<circle cx="260" cy="260" r="216" stroke="#c084fc" stroke-width="2.4" stroke-dasharray="90 30 20 15 45 30" opacity="0.85" filter="url(#cyberGlow)" />
<circle cx="260" cy="260" r="223" stroke="rgba(129, 140, 248, 0.45)" stroke-width="1" stroke-dasharray="2 10" />
</g>
<g class="digital-ring-outer">
<circle cx="260" cy="260" r="238" stroke="#6366f1" stroke-width="1.8" stroke-dasharray="140 40 40 40" opacity="0.75" />
<circle cx="260" cy="260" r="246" stroke="rgba(192, 132, 252, 0.5)" stroke-width="1" stroke-dasharray="6 8" />
<path d="M 410 95 L 435 95 L 435 120" stroke="#38bdf8" stroke-width="2.5" fill="none" filter="url(#cyberGlow)" />
<path d="M 435 400 L 435 425 L 410 425" stroke="#38bdf8" stroke-width="2.5" fill="none" filter="url(#cyberGlow)" />
<path d="M 110 425 L 85 425 L 85 400" stroke="#38bdf8" stroke-width="2.5" fill="none" filter="url(#cyberGlow)" />
<path d="M 85 120 L 85 95 L 110 95" stroke="#38bdf8" stroke-width="2.5" fill="none" filter="url(#cyberGlow)" />
<text x="260" y="24" font-family="'Courier New', monospace" font-size="8.5" font-weight="bold" fill="#38bdf8" text-anchor="middle" letter-spacing="3" opacity="0.95">SYS.ONLINE // 0x7F4B</text>
<text x="260" y="504" font-family="'Courier New', monospace" font-size="8.5" font-weight="bold" fill="#c084fc" text-anchor="middle" letter-spacing="3" opacity="0.95">CORE.ACTIVE // DEV.MODE</text>
</g>
<g class="digital-ring-satellites">
<rect x="254" y="6" width="12" height="6" rx="2" fill="#38bdf8" filter="url(#intenseGlow)" />
<rect x="508" y="254" width="6" height="12" rx="2" fill="#c084fc" filter="url(#intenseGlow)" />
<rect x="254" y="508" width="12" height="6" rx="2" fill="#38bdf8" filter="url(#intenseGlow)" />
<rect x="6" y="254" width="6" height="12" rx="2" fill="#c084fc" filter="url(#intenseGlow)" />
</g>
</svg>
</div>
<div class="hero-card-frame">
{avatar_content}
</div>
<div class="code-snippet-box">
<div class="code-snippet-header">
<div class="code-title">
<span>&lt;/&gt;</span> Code
</div>
<div class="code-dot"></div>
</div>
<div class="code-snippet-body">
<span class="code-keyword">const</span> <span class="code-var">developer</span> = {{<br/>
&nbsp;&nbsp;<span class="code-key">name</span>: <span class="code-string">"Wahyu Pamungkas"</span>,<br/>
&nbsp;&nbsp;<span class="code-key">skills</span>: [<span class="code-string">"HTML"</span>, <span class="code-string">"CSS"</span>,<br/>
&nbsp;&nbsp;&nbsp;&nbsp;<span class="code-string">"JavaScript"</span>, <span class="code-string">"React"</span>],<br/>
&nbsp;&nbsp;<span class="code-key">passion</span>: <span class="code-string">"Building things<br/>
&nbsp;&nbsp;&nbsp;&nbsp;for the web"</span><br/>
}};
</div>
</div>
</div>
</div>
</div>
</div>
</section>"""

st.markdown(hero_html, unsafe_allow_html=True)


# ─── ABOUT ME SECTION ───
about_html = """<section class="fullscreen-section about-section" id="about">
<div class="section-inner">
<div class="about-grid">
<div class="about-left">
<div class="about-badge">ABOUT ME</div>
<h2 class="about-heading"><span class="kinetic-word">I'm passionate about</span><br/><span class="highlight kinetic-word">creating digital solutions</span></h2>
<p class="about-text">
With 4+ years of experience in web development, I help
businesses and individuals bring their ideas to life through
clean, efficient, and user-friendly code.
</p>
<a href="#contact" class="about-btn">Learn More About Me <span>↗</span></a>
</div>
<div class="about-right stats-grid">
<div class="stat-card">
<div class="stat-icon">
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#818cf8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
<rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
<line x1="8" y1="21" x2="16" y2="21"/>
<line x1="12" y1="17" x2="12" y2="21"/>
</svg>
</div>
<div>
<div class="stat-number">4+</div>
<div class="stat-label">Years Experience</div>
</div>
</div>
<div class="stat-card">
<div class="stat-icon">
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#818cf8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
<path d="M16 18L22 12L16 6"/>
<path d="M8 6L2 12L8 18"/>
</svg>
</div>
<div>
<div class="stat-number">50+</div>
<div class="stat-label">Projects Completed</div>
</div>
</div>
<div class="stat-card">
<div class="stat-icon">
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#818cf8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
<circle cx="9" cy="7" r="4"/>
<path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
<path d="M16 3.13a4 4 0 0 1 0 7.75"/>
</svg>
</div>
<div>
<div class="stat-number">30+</div>
<div class="stat-label">Happy Clients</div>
</div>
</div>
<div class="stat-card">
<div class="stat-icon">
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#818cf8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
<path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/>
<path d="M9 12l2 2 4-4"/>
</svg>
</div>
<div>
<div class="stat-number">100%</div>
<div class="stat-label">Client Satisfaction</div>
</div>
</div>
</div>
</div>
</div>
</section>"""

st.markdown(about_html, unsafe_allow_html=True)


# ─── SKILLS SECTION ───
skills_data = [
    # Column 1
    [
        ("HTML", "#e34f26", "95"),
        ("CSS", "#264de4", "90"),
        ("JavaScript", "#f0db4f", "90"),
    ],
    # Column 2
    [
        ("React.js", "#61dafb", "85"),
        ("Next.js", "#ffffff", "80"),
        ("TypeScript", "#3178c6", "85"),
    ],
    # Column 3
    [
        ("Node.js", "#339933", "80"),
        ("Tailwind CSS", "#38bdf8", "90"),
        ("Git", "#f05032", "85"),
    ],
]

skill_icons = {
    "HTML": '<svg width="16" height="16" viewBox="0 0 24 24" fill="#e34f26"><path d="M1.5 0h21l-1.91 21.563L11.977 24l-8.564-2.438L1.5 0zm7.031 9.75l-.232-2.718 10.059.003.076-.757.076-.771.076-.758H6.792l.61 6.951h7.15l-.274 2.97-2.29.617-2.29-.617-.163-1.756H7.2l.275 3.85 4.513 1.228 4.513-1.232.668-7.018-.028.002H8.53z"/></svg>',
    "CSS": '<svg width="16" height="16" viewBox="0 0 24 24" fill="#264de4"><path d="M1.5 0h21l-1.91 21.563L11.977 24l-8.565-2.438L1.5 0zm17.09 4.413L5.41 4.41l.213 2.622 10.125.002-.255 2.716h-6.64l.24 2.573h6.182l-.366 3.523-2.91.804-2.956-.81-.188-2.11h-2.61l.29 3.855L12 19.002l4.5-1.244 1.59-13.345z"/></svg>',
    "JavaScript": '<span style="font-size:0.65rem;font-weight:800;color:#f0db4f;">JS</span>',
    "React.js": '<svg width="16" height="16" viewBox="0 0 24 24" fill="#61dafb"><circle cx="12" cy="12" r="2.139"/><path d="M6.008 16.938c-.247-.14-.39-.396-.39-.674V7.736c0-.278.143-.535.39-.674l8-4.618c.245-.141.545-.141.79 0l8 4.618c.247.14.39.396.39.674v8.528c0 .278-.143.535-.39.674l-8 4.618c-.245.141-.545.141-.79 0l-8-4.618z" fill="none" stroke="#61dafb" stroke-width="1"/></svg>',
    "Next.js": '<span style="font-size:0.65rem;font-weight:800;color:#fff;">N</span>',
    "TypeScript": '<span style="font-size:0.6rem;font-weight:800;color:#3178c6;">TS</span>',
    "Node.js": '<svg width="16" height="16" viewBox="0 0 24 24" fill="#339933"><path d="M11.998,24c-0.321,0-0.641-0.084-0.922-0.247l-2.936-1.737c-0.438-0.245-0.224-0.332-0.08-0.383 c0.585-0.203,0.703-0.25,1.328-0.604c0.065-0.037,0.151-0.023,0.218,0.017l2.256,1.339c0.082,0.045,0.197,0.045,0.272,0 l8.795-5.076c0.082-0.047,0.134-0.141,0.134-0.238V6.921c0-0.099-0.053-0.192-0.137-0.242l-8.791-5.072 c-0.081-0.047-0.189-0.047-0.271,0L3.075,6.68C2.99,6.729,2.936,6.825,2.936,6.921v10.15c0,0.097,0.054,0.189,0.136,0.235 l2.409,1.392c1.307,0.654,2.108-0.116,2.108-0.89V7.787c0-0.142,0.114-0.253,0.256-0.253h1.115c0.139,0,0.255,0.112,0.255,0.253 v10.021c0,1.745-0.95,2.745-2.604,2.745c-0.508,0-0.909,0-2.026-0.551L2.28,18.675c-0.57-0.329-0.922-0.945-0.922-1.604V6.921 c0-0.659,0.353-1.275,0.922-1.603l8.795-5.082c0.557-0.315,1.296-0.315,1.848,0l8.794,5.082c0.57,0.329,0.924,0.944,0.924,1.603 v10.15c0,0.659-0.354,1.273-0.924,1.604l-8.794,5.078C12.643,23.916,12.324,24,11.998,24z"/></svg>',
    "Tailwind CSS": '<svg width="16" height="16" viewBox="0 0 24 24" fill="#38bdf8"><path d="M12.001,4.8c-3.2,0-5.2,1.6-6,4.8c1.2-1.6,2.6-2.2,4.2-1.8c0.913,0.228,1.565,0.89,2.288,1.624 C13.666,10.618,15.027,12,18.001,12c3.2,0,5.2-1.6,6-4.8c-1.2,1.6-2.6,2.2-4.2,1.8c-0.913-0.228-1.565-0.89-2.288-1.624 C16.337,6.182,14.976,4.8,12.001,4.8z M6.001,12c-3.2,0-5.2,1.6-6,4.8c1.2-1.6,2.6-2.2,4.2-1.8 c0.913,0.228,1.565,0.89,2.288,1.624c1.177,1.194,2.538,2.576,5.512,2.576c3.2,0,5.2-1.6,6-4.8c-1.2,1.6-2.6,2.2-4.2,1.8 c-0.913-0.228-1.565-0.89-2.288-1.624C10.337,13.382,8.976,12,6.001,12z"/></svg>',
    "Git": '<svg width="16" height="16" viewBox="0 0 24 24" fill="#f05032"><path d="M23.546 10.93L13.067.452c-.604-.603-1.582-.603-2.188 0L8.708 2.627l2.76 2.76c.645-.215 1.379-.07 1.889.441.516.515.658 1.258.438 1.9l2.66 2.66c.645-.222 1.387-.078 1.9.435.72.72.72 1.884 0 2.604-.72.719-1.885.719-2.604 0-.54-.541-.674-1.337-.404-1.996L12.86 8.955v6.525c.176.086.342.203.488.348.713.721.713 1.883 0 2.6-.713.721-1.88.721-2.593 0-.713-.717-.713-1.879 0-2.6.182-.18.387-.316.605-.406V8.835c-.217-.091-.424-.222-.6-.401-.545-.545-.676-1.342-.396-2.009L7.636 3.7.45 10.881c-.6.605-.6 1.584 0 2.189l10.48 10.477c.604.604 1.582.604 2.186 0l10.43-10.43c.605-.603.605-1.582 0-2.187"/></svg>',
}

skills_cards_html = ""
for skill_group in skills_data:
    skills_cards_html += '<div class="skill-group-col">\n'
    for name, color, pct in skill_group:
        icon_html = skill_icons.get(name, f'<span style="font-size:0.6rem;font-weight:700;color:{color};">●</span>')
        skills_cards_html += (
            f'<div class="skill-item">'
            f'<div class="skill-header">'
            f'<div class="skill-name-group">'
            f'<div class="skill-icon" style="background:{color}20; border: 1px solid {color}40;">'
            f'{icon_html}'
            f'</div>'
            f'<span class="skill-name">{name}</span>'
            f'</div>'
            f'<span class="skill-pct">{pct}%</span>'
            f'</div>'
            f'<div class="skill-bar-bg">'
            f'<div class="skill-bar-fill" style="width:{pct}%;"></div>'
            f'</div>'
            f'</div>\n'
        )
    skills_cards_html += '</div>\n'

skills_html = f"""<section class="fullscreen-section skills-section" id="skills">
<div class="section-inner">
<div style="text-align: center; margin-bottom: 2rem;">
<div class="section-label" style="text-align:center;">MY SKILLS</div>
<div class="section-title" style="text-align:center; margin-bottom: 0;"><span class="kinetic-word">Technologies</span> <span class="highlight kinetic-word">I Master</span></div>
</div>
<div class="skills-grid">
{skills_cards_html}
</div>
</div>
</section>"""

st.markdown(skills_html, unsafe_allow_html=True)


# ─── PROJECTS SECTION ───
projects = [
    {
        "num": "01",
        "title": "Prediksi Financial Distress",
        "desc": "Aplikasi web prediksi kesulitan keuangan industri manufaktur BEI berbasis Streamlit menggunakan model Altman Z-Score & Extreme Gradient Boosting (XGBoost).",
        "pattern": "project-pattern-1",
        "mockup": "financial",
        "link": "https://financialdistress.streamlit.app/",
        "image": project1_img_b64,
    },
    {
        "num": "02",
        "title": "Task Management App",
        "desc": "Collaborative task management application",
        "pattern": "project-pattern-2",
        "mockup": "taskapp",
        "link": "#",
    },
    {
        "num": "03",
        "title": "Crypto Dashboard",
        "desc": "Real-time cryptocurrency tracking dashboard",
        "pattern": "project-pattern-3",
        "mockup": "crypto",
        "link": "#",
    },
]

mockup_contents = {
    "financial": (
        '<div class="mockup-inner">'
        '<div class="mockup-topbar">'
        '<div class="mockup-dot red"></div>'
        '<div class="mockup-dot yellow"></div>'
        '<div class="mockup-dot green"></div>'
        '<span style="font-size:7px;color:rgba(129,140,248,0.7);margin-left:6px;font-family:monospace;">financialdistress.streamlit.app</span>'
        '</div>'
        '<div class="mockup-body">'
        '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">'
        '<div class="mockup-line accent" style="width:48%;height:8px;"></div>'
        '<span style="font-size:7px;color:#38bdf8;background:rgba(56,189,248,0.15);padding:1px 4px;border-radius:3px;font-weight:600;">Streamlit ML</span>'
        '</div>'
        '<div style="height:36px;border-radius:4px;background:linear-gradient(90deg,rgba(99,102,241,0.1),rgba(192,132,252,0.25),rgba(56,189,248,0.15));margin-top:4px;position:relative;overflow:hidden;">'
        '<svg width="100%" height="100%" viewBox="0 0 200 36" preserveAspectRatio="none">'
        '<polyline points="0,28 35,22 70,30 110,12 150,18 200,6" fill="none" stroke="#818cf8" stroke-width="1.8"/>'
        '<circle cx="110" cy="12" r="3" fill="#c084fc"/>'
        '<circle cx="200" cy="6" r="3" fill="#38bdf8"/>'
        '</svg>'
        '</div>'
        '<div style="display:flex;gap:4px;margin-top:6px;">'
        '<div style="flex:1;height:14px;background:rgba(34,197,94,0.15);border-radius:3px;font-size:7px;color:#4ade80;display:flex;align-items:center;justify-content:center;font-weight:600;">Safe Zone</div>'
        '<div style="flex:1;height:14px;background:rgba(239,68,68,0.15);border-radius:3px;font-size:7px;color:#f87171;display:flex;align-items:center;justify-content:center;font-weight:600;">Distress</div>'
        '</div>'
        '</div>'
        '</div>'
    ),
    "ecommerce": (
        '<div class="mockup-inner">'
        '<div class="mockup-topbar">'
        '<div class="mockup-dot red"></div>'
        '<div class="mockup-dot yellow"></div>'
        '<div class="mockup-dot green"></div>'
        '</div>'
        '<div class="mockup-body">'
        '<div class="mockup-line accent" style="width:35%;height:8px;"></div>'
        '<div class="mockup-line long"></div>'
        '<div class="mockup-line medium"></div>'
        '<div class="mockup-grid">'
        '<div class="mockup-card-mini"></div>'
        '<div class="mockup-card-mini"></div>'
        '<div class="mockup-card-mini"></div>'
        '<div class="mockup-card-mini"></div>'
        '</div>'
        '<div class="mockup-line short" style="margin-top:6px;background:rgba(99,102,241,0.4);height:10px;border-radius:5px;"></div>'
        '</div>'
        '</div>'
    ),
    "taskapp": (
        '<div class="mockup-inner">'
        '<div class="mockup-topbar">'
        '<div class="mockup-dot red"></div>'
        '<div class="mockup-dot yellow"></div>'
        '<div class="mockup-dot green"></div>'
        '</div>'
        '<div class="mockup-body">'
        '<div class="mockup-line accent" style="width:45%;height:8px;"></div>'
        '<div style="display:flex;gap:6px;margin-top:4px;">'
        '<div style="flex:1;height:25px;background:rgba(99,102,241,0.15);border-radius:4px;border:1px solid rgba(99,102,241,0.2);"></div>'
        '<div style="flex:1;height:25px;background:rgba(255,255,255,0.04);border-radius:4px;border:1px solid rgba(255,255,255,0.06);"></div>'
        '<div style="flex:1;height:25px;background:rgba(255,255,255,0.04);border-radius:4px;border:1px solid rgba(255,255,255,0.06);"></div>'
        '</div>'
        '<div class="mockup-line long" style="margin-top:6px;"></div>'
        '<div class="mockup-line medium"></div>'
        '<div class="mockup-line short"></div>'
        '<div class="mockup-line long"></div>'
        '</div>'
        '</div>'
    ),
    "crypto": (
        '<div class="mockup-inner">'
        '<div class="mockup-topbar">'
        '<div class="mockup-dot red"></div>'
        '<div class="mockup-dot yellow"></div>'
        '<div class="mockup-dot green"></div>'
        '</div>'
        '<div class="mockup-body">'
        '<div style="display:flex;gap:6px;">'
        '<div style="flex:1;height:20px;background:rgba(34,197,94,0.15);border-radius:4px;border:1px solid rgba(34,197,94,0.2);display:flex;align-items:center;justify-content:center;font-size:7px;color:rgba(34,197,94,0.6);">▲</div>'
        '<div style="flex:1;height:20px;background:rgba(239,68,68,0.15);border-radius:4px;border:1px solid rgba(239,68,68,0.2);display:flex;align-items:center;justify-content:center;font-size:7px;color:rgba(239,68,68,0.6);">▼</div>'
        '<div style="flex:1;height:20px;background:rgba(99,102,241,0.15);border-radius:4px;border:1px solid rgba(99,102,241,0.2);display:flex;align-items:center;justify-content:center;font-size:7px;color:rgba(99,102,241,0.6);">◆</div>'
        '</div>'
        '<div style="height:50px;border-radius:4px;background:linear-gradient(90deg,rgba(99,102,241,0.1),rgba(99,102,241,0.3),rgba(99,102,241,0.1));margin-top:4px;position:relative;overflow:hidden;">'
        '<svg width="100%" height="100%" viewBox="0 0 200 50" preserveAspectRatio="none">'
        '<polyline points="0,40 30,35 60,20 90,30 120,10 150,25 180,15 200,20" fill="none" stroke="rgba(99,102,241,0.5)" stroke-width="1.5"/>'
        '</svg>'
        '</div>'
        '<div class="mockup-line medium" style="margin-top:4px;"></div>'
        '<div class="mockup-line short"></div>'
        '</div>'
        '</div>'
    ),
}

project_cards_html = ""
for project in projects:
    proj_link = project.get("link", "#")
    target_attr = 'target="_blank" rel="noopener noreferrer"' if proj_link != "#" else ""
    proj_img = project.get("image", "")

    if proj_img:
        card_visual = f'<img src="{proj_img}" alt="{project["title"]}" class="project-thumbnail-img" />'
    else:
        card_visual = mockup_contents.get(project["mockup"], "")

    project_cards_html += (
        f'<div class="project-card">'
        f'<a href="{proj_link}" {target_attr} style="text-decoration:none;display:block;color:inherit;">'
        f'<div class="project-image {project["pattern"]}">'
        f'<div class="project-number">{project["num"]}</div>'
        f'{card_visual}'
        f'</div>'
        f'</a>'
        f'<div class="project-info">'
        f'<div class="project-title"><a href="{proj_link}" {target_attr} style="color:inherit;text-decoration:none;">{project["title"]}</a></div>'
        f'<div class="project-desc">{project["desc"]}</div>'
        f'<a href="{proj_link}" {target_attr} class="project-link">View Project <span>→</span></a>'
        f'</div>'
        f'</div>\n'
    )

projects_html = f"""<section class="fullscreen-section projects-section" id="projects">
<div class="section-inner">
<div style="text-align: center; margin-bottom: 1.8rem;">
<div class="section-label" style="text-align:center;">FEATURED PROJECTS</div>
<div class="section-title" style="text-align:center; margin-bottom: 0;"><span class="kinetic-word">Some of My</span> <span class="highlight kinetic-word">Recent Work</span></div>
</div>
<div class="projects-grid">
{project_cards_html}
</div>
<div class="carousel-dots" style="margin-top: 1.5rem;">
<div class="carousel-dot active"></div>
<div class="carousel-dot"></div>
<div class="carousel-dot"></div>
</div>
</div>
</section>"""

st.markdown(projects_html, unsafe_allow_html=True)


# ─── BLOG SECTION ───
blog_posts = [
    {
        "title": "Mastering Responsive Web Design with Tailwind CSS",
        "date": "Oct 15, 2024",
        "read_time": "5 min read",
        "desc": "Tips and best practices for building fluid, mobile-first layouts.",
    },
    {
        "title": "Why Next.js & React 19 Are Changing the Web",
        "date": "Sep 28, 2024",
        "read_time": "7 min read",
        "desc": "Deep dive into server components and performance optimization.",
    },
    {
        "title": "Building Modern Interactive Web Portfolios",
        "date": "Aug 12, 2024",
        "read_time": "4 min read",
        "desc": "How to create high-converting developer showcases and cards.",
    },
]

blog_cards_html = ""
for post in blog_posts:
    blog_cards_html += (
        f'<div class="project-card" style="padding: 1.4rem; display: flex; flex-direction: column; justify-content: space-between;">'
        f'<div>'
        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 0.8rem; font-size: 0.75rem; color: var(--accent-purple-hover); font-family: \'Inter\', sans-serif;">'
        f'<span>{post["date"]}</span>'
        f'<span>{post["read_time"]}</span>'
        f'</div>'
        f'<div class="project-title" style="font-size: 1.05rem; margin-bottom: 0.6rem;">{post["title"]}</div>'
        f'<div class="project-desc">{post["desc"]}</div>'
        f'</div>'
        f'<a href="#" class="project-link" style="margin-top: 1rem;">Read Article <span>→</span></a>'
        f'</div>\n'
    )

blog_html = f"""<section class="fullscreen-section blog-section" id="blog">
<div class="section-inner">
<div style="text-align: center; margin-bottom: 2rem;">
<div class="section-label" style="text-align:center;">LATEST ARTICLES</div>
<div class="section-title" style="text-align:center; margin-bottom: 0;"><span class="kinetic-word">Articles &amp; Insights</span> <span class="highlight kinetic-word">From My Blog</span></div>
</div>
<div class="blog-grid">
{blog_cards_html}
</div>
</div>
</section>"""

st.markdown(blog_html, unsafe_allow_html=True)


# ─── FOOTER / CTA SECTION ───
contact_html = """<section class="fullscreen-section footer-section" id="contact">
<div class="section-inner contact-inner">
<div class="contact-grid">
<div class="contact-col">
<div class="footer-label">LET'S WORK TOGETHER</div>
<h2 class="footer-heading"><span class="kinetic-word">Have a project</span> <span class="highlight kinetic-word">in mind?</span></h2>
<p class="footer-text">
I'm always open to discussing new projects and
opportunities. Let's create something amazing together!
</p>
<a href="mailto:hello@wahyupamungkas.com" class="cta-btn">Get In Touch <span>↗</span></a>
</div>
<div class="testimonial-col">
<div class="testimonial-card">
<div class="testimonial-quote-icon">❝</div>
<p class="testimonial-text">
Wahyu is an exceptional developer who delivers
high-quality work on time. His attention to detail
and problem-solving skills are outstanding.
</p>
<div class="testimonial-author">
<div class="testimonial-avatar">S</div>
<div>
<div class="testimonial-author-name">Sarah Johnson</div>
<div class="testimonial-author-role">CEO, TechStart</div>
</div>
</div>
</div>
</div>
<div class="contact-info-col">
<div class="footer-label">FOLLOW ME</div>
<div class="social-icons">
<a href="#" class="social-icon" title="GitHub">
<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/></svg>
</a>
<a href="#" class="social-icon" title="LinkedIn">
<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
</a>
<a href="#" class="social-icon" title="Twitter">
<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"/></svg>
</a>
<a href="#" class="social-icon" title="Instagram">
<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C8.74 0 8.333.015 7.053.072 5.775.132 4.905.333 4.14.63c-.789.306-1.459.717-2.126 1.384S.935 3.35.63 4.14C.333 4.905.131 5.775.072 7.053.012 8.333 0 8.74 0 12s.015 3.667.072 4.947c.06 1.277.261 2.148.558 2.913.306.788.717 1.459 1.384 2.126.667.666 1.336 1.079 2.126 1.384.766.296 1.636.499 2.913.558C8.333 23.988 8.74 24 12 24s3.667-.015 4.947-.072c1.277-.06 2.148-.262 2.913-.558.788-.306 1.459-.718 2.126-1.384.666-.667 1.079-1.335 1.384-2.126.296-.765.499-1.636.558-2.913.06-1.28.072-1.687.072-4.947s-.015-3.667-.072-4.947c-.06-1.277-.262-2.149-.558-2.913-.306-.789-.718-1.459-1.384-2.126C21.319 1.347 20.651.935 19.86.63c-.765-.297-1.636-.499-2.913-.558C15.667.012 15.26 0 12 0zm0 2.16c3.203 0 3.585.016 4.85.071 1.17.055 1.805.249 2.227.415.562.217.96.477 1.382.896.419.42.679.819.896 1.381.164.422.36 1.057.413 2.227.057 1.266.07 1.646.07 4.85s-.015 3.585-.074 4.85c-.061 1.17-.256 1.805-.421 2.227-.224.562-.479.96-.899 1.382-.419.419-.824.679-1.38.896-.42.164-1.065.36-2.235.413-1.274.057-1.649.07-4.859.07-3.211 0-3.586-.015-4.859-.074-1.171-.061-1.816-.256-2.236-.421-.569-.224-.96-.479-1.379-.899-.421-.419-.69-.824-.9-1.38-.165-.42-.359-1.065-.42-2.235-.045-1.26-.061-1.649-.061-4.844 0-3.196.016-3.586.061-4.861.061-1.17.255-1.814.42-2.234.21-.57.479-.96.9-1.381.419-.419.81-.689 1.379-.898.42-.166 1.051-.361 2.221-.421 1.275-.045 1.65-.06 4.859-.06l.045.03zm0 3.678c-3.405 0-6.162 2.76-6.162 6.162 0 3.405 2.76 6.162 6.162 6.162 3.405 0 6.162-2.76 6.162-6.162 0-3.405-2.76-6.162-6.162-6.162zM12 16c-2.21 0-4-1.79-4-4s1.79-4 4-4 4 1.79 4 4-1.79 4-4 4zm7.846-10.405c0 .795-.646 1.44-1.44 1.44-.795 0-1.44-.646-1.44-1.44 0-.794.646-1.439 1.44-1.439.793-.001 1.44.645 1.44 1.439z"/></svg>
</a>
</div>
<div class="contact-item">
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
hello@wahyupamungkas.com
</div>
<div class="contact-item">
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
+1 (555) 123-4567
</div>
</div>
</div>
<div class="copyright-bar">
<div class="copyright-text">© 2024 Wahyu Pamungkas. All rights reserved.</div>
<div class="copyright-text">Made with <span class="copyright-heart">❤️</span> by Wahyu Pamungkas</div>
</div>
</div>
</section>"""

st.markdown(contact_html, unsafe_allow_html=True)


# ─── INTERACTION & DYNAMIC SCROLL ANIMATION CONTROLLER ───
st.components.v1.html("""
<script>
(function() {
    try {
        var doc = (window.parent && window.parent.document) ? window.parent.document : document;
        
        // Ensure navbar is pinned directly to doc.body so it stays permanently fixed across all scrolling
        try {
            var nbs = doc.querySelectorAll('.navbar');
            if (nbs && nbs.length > 1) {
                for (var k = 0; k < nbs.length - 1; k++) {
                    nbs[k].remove();
                }
            }
            var nb = doc.querySelector('.navbar');
            if (nb && nb.parentElement && nb.parentElement !== doc.body) {
                doc.body.appendChild(nb);
            }
        } catch(e) {}
        
        function updateActiveNav(id) {
            if (!id) return;
            var navLinks = doc.querySelectorAll('.navbar-links a.nav-item');
            if (navLinks && navLinks.length) {
                for (var i = 0; i < navLinks.length; i++) {
                    var href = navLinks[i].getAttribute('href');
                    if (href === '#' + id) {
                        navLinks[i].classList.add('active');
                    } else {
                        navLinks[i].classList.remove('active');
                    }
                }
            }
            var scrollDots = doc.querySelectorAll('.scroll-nav-dots a.scroll-dot');
            if (scrollDots && scrollDots.length) {
                for (var j = 0; j < scrollDots.length; j++) {
                    var dotHref = scrollDots[j].getAttribute('href');
                    if (dotHref === '#' + id) {
                        scrollDots[j].classList.add('active');
                    } else {
                        scrollDots[j].classList.remove('active');
                    }
                }
            }
        }

        doc.addEventListener('click', function(e) {
            var link = e.target.closest ? e.target.closest('.navbar-links a.nav-item, .navbar-brand, .hire-btn, .scroll-dot') : null;
            if (link) {
                var href = link.getAttribute('href');
                if (href && href.charAt(0) === '#') {
                    var targetId = href.substring(1);
                    var targetEl = doc.getElementById(targetId);
                    if (targetEl) {
                        e.preventDefault();
                        targetEl.scrollIntoView({ behavior: 'smooth' });
                        try {
                            if (window.parent && window.parent.history) {
                                window.parent.history.pushState(null, '', '#' + targetId);
                            }
                        } catch(err){}
                        updateActiveNav(targetId);
                    }
                }
            }
        });

        var curtain = doc.getElementById('cinematicIntro');
        function handleCurtainOpen() {
            if (!curtain) return;
            curtain.classList.add('opened');
            var cb = doc.getElementById('curtainTrigger');
            if (cb) cb.checked = true;
            var homeSec = doc.getElementById('home');
            if (homeSec) {
                homeSec.classList.remove('in-view');
                void homeSec.offsetWidth;
                homeSec.classList.add('in-view');
            }
            setTimeout(function() {
                if (curtain) {
                    curtain.style.display = 'none';
                    curtain.style.visibility = 'hidden';
                    curtain.style.pointerEvents = 'none';
                }
            }, 1250);
        }
        if (curtain) {
            curtain.addEventListener('click', handleCurtainOpen);
        } else {
            var homeSec = doc.getElementById('home');
            if (homeSec) homeSec.classList.add('in-view');
        }

        var sections = doc.querySelectorAll('.fullscreen-section');
        if (sections && sections.length) {
            var ObserverClass = (window.parent && window.parent.IntersectionObserver) ? window.parent.IntersectionObserver : IntersectionObserver;
            if (ObserverClass) {
                var observer = new ObserverClass(function(entries) {
                    entries.forEach(function(entry) {
                        var id = entry.target.getAttribute('id');
                        if (entry.isIntersecting) {
                            entry.target.classList.add('in-view');
                            if (id) updateActiveNav(id);
                        } else {
                            entry.target.classList.remove('in-view');
                        }
                    });
                }, { threshold: 0.18 });
                
                for (var s = 0; s < sections.length; s++) {
                    observer.observe(sections[s]);
                }
            }
        }
        
        if (window.parent) {
            window.parent.addEventListener('hashchange', function() {
                var h = window.parent.location.hash;
                if (h) {
                    var targetId = h.substring(1);
                    var targetSec = doc.getElementById(targetId);
                    if (targetSec) targetSec.classList.add('in-view');
                    updateActiveNav(targetId);
                }
            });
        }
    } catch(err) {
        // fail silently
    }
})();
</script>
""", height=0)
