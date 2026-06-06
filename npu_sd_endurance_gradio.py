"""
NPU BenchMark for AMD — Gradio Edition
AMD Ryzen AI / XDNA2+ / RyzenAI 1.7.1

Browser-based benchmark dashboard for Stable Diffusion on AMD NPU.
Auto-opens browser on launch. Closing browser tab stops the test.

Requirements:
    - AMD RyzenAI Software 1.7.1 installed
      https://ryzenai.docs.amd.com/en/latest/inst.html
    - conda environment: xdna171
    - ONNX model folders in ./models/
    - RYZEN_AI_INSTALLATION_PATH env var (set automatically by AMD installer)

Usage:
    conda activate xdna171
    python npu_sd_endurance_gradio.py

    The app auto-detects your RyzenAI installation path.
    If needed, override with:  set DD_ROOT=C:\\path\\to\\GenAI-SD

Design by Hiko
"""

import os, sys, time, json, threading, subprocess, webbrowser
from pathlib import Path
from datetime import datetime
from collections import deque

try:
    import psutil
except ImportError:
    print("[Error] psutil not found. Run: pip install psutil")
    sys.exit(1)

try:
    import gradio as gr
except ImportError:
    print("[Error] gradio not found.")
    sys.exit(1)

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ───────────────────────────────────────────────────
# Path config  (auto-detect dev vs packaged)
# ───────────────────────────────────────────────────
APP_ROOT = Path(__file__).resolve().parent

if (APP_ROOT / "sd_runtime").exists():
    # ── Packaged (BenchMarkCV) structure ─────────────────────────
    SD_RUNTIME     = APP_ROOT / "sd_runtime"
    MODELS_DIR     = APP_ROOT / "models"
    CUSTOM_OP_PATH = str(APP_ROOT / "amd" / "deployment" / "onnx_custom_ops.dll")
    DD_ROOT        = str(APP_ROOT / "amd" / "GenAI-SD")
    RESULTS_DIR    = APP_ROOT / "results"
else:
    # ── Standalone / GitHub mode ──────────────────────────────────
    # AMD installer sets RYZEN_AI_INSTALLATION_PATH automatically.
    # Override with DD_ROOT env var if needed.
    _SDK = Path(os.environ.get(
        "RYZEN_AI_INSTALLATION_PATH",
        r"C:\Program Files\RyzenAI\1.7.1"
    ))
    SD_RUNTIME     = _SDK / "GenAI-SD"          # inference scripts live here
    MODELS_DIR     = APP_ROOT / "models"         # put your model folders here
    CUSTOM_OP_PATH = str(_SDK / "deployment" / "onnx_custom_ops.dll")
    DD_ROOT        = os.environ.get("DD_ROOT", str(_SDK / "GenAI-SD"))
    RESULTS_DIR    = APP_ROOT / "endurance_results"

OUTPUT_DIR = RESULTS_DIR / "images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

XRT_SMI = r"C:\Windows\System32\AMD\xrt-smi.exe"

# ───────────────────────────────────────────────────
# Model config
# ───────────────────────────────────────────────────
MODELS = {
    "sd15": {
        "name": "SD 1.5", "folder": "sd_15", "script": "run_sd.py",
        "model_id": "runwayml/stable-diffusion-v1-5",
        "steps": 20, "guidance": 7.5, "tier": "lite",
        "vram_gb": 3.5, "res": "512×512",
    },
    "sd_turbo": {
        "name": "SD Turbo", "folder": "sd_turbo_bfp", "script": "run_sd.py",
        "model_id": "stabilityai/sd-turbo",
        "steps": 1, "guidance": 0.0, "tier": "lite",
        "vram_gb": 3.5, "res": "512×512",
    },
    "sdxl_turbo": {
        "name": "SDXL Turbo", "folder": "sdxl_turbo_bfp", "script": "run_sd_xl.py",
        "model_id": "stabilityai/sdxl-turbo",
        "steps": 1, "guidance": 0.0, "tier": "full",
        "vram_gb": 6.0, "res": "512×512",
    },
    "vega": {
        "name": "Segmind Vega", "folder": "Segmind-Vega_bfp", "script": "run_sd_xl.py",
        "model_id": "segmind/Segmind-Vega",
        "steps": 20, "guidance": 7.5, "tier": "full",
        "vram_gb": 6.5, "res": "1024×1024",
    },
    "sdxl_base": {
        "name": "SDXL Base", "folder": "sdxl-base-1.0_bfp", "script": "run_sd_xl.py",
        "model_id": "stabilityai/stable-diffusion-xl-base-1.0",
        "steps": 50, "guidance": 7.5, "tier": "full",
        "vram_gb": 7.5, "res": "1024×1024",
    },
}

# ───────────────────────────────────────────────────
# Duration / rounds presets
# ───────────────────────────────────────────────────
DURATION_PRESETS = {
    "10 minutes":  600,
    "30 minutes":  1800,
    "1 hour":      3600,
    "2 hours":     7200,
    "8 hours":     28800,
    "12 hours":    43200,
    "24 hours":    86400,
    "Custom":      None,
}

ROUNDS_PRESETS = {
    "10 rounds":   10,
    "100 rounds":  100,
    "500 rounds":  500,
    "1000 rounds": 1000,
    "1500 rounds": 1500,
    "Custom":      None,
}

# ───────────────────────────────────────────────────
# Default prompts (60 scenes)
# ───────────────────────────────────────────────────
DEFAULT_PROMPTS = """\
a majestic mountain range at golden hour, cinematic lighting, photorealistic, 8k
misty ancient forest at dawn, sunbeams through towering trees, ethereal atmosphere
volcanic eruption at night, rivers of glowing lava, dramatic stormy sky, epic scale
arctic tundra under shimmering aurora borealis, polar night, breathtaking colors
tropical rainforest hidden waterfall, lush emerald vegetation, mist rising, vibrant
red rock canyon at sunset, American southwest desert, long shadows, warm tones
massive storm waves crashing against rocky sea cliffs, dramatic, powerful, cinematic
japanese cherry blossom park in spring, pink petals drifting, soft diffused light
narrow autumn forest path, canopy of gold and crimson leaves, peaceful, cinematic
rolling wheat fields at harvest, rustic barns, warm afternoon light, rural beauty
sahara desert at sunrise, infinite sand dunes, soft pink sky, vast and empty
swiss alpine meadow in summer, wildflowers, distant snow-capped peaks, idyllic
deep amazon river winding through jungle, parrots in flight, lush and mysterious
perfectly frozen mountain lake in winter, mirror reflection, serene minimalist beauty
black sand volcanic beach, turquoise water, dramatic contrasts, Iceland coastline
lavender fields in provence at dusk, purple rows to the horizon, romantic, hazy
giant redwood forest, ancient towering trees, misty shafts of light, sacred feeling
scottish highlands at dawn, rolling green hills, fog in the valleys, moody sky
coral atoll from above, turquoise lagoon, white sand, tropical paradise aerial view
thunderstorm over the great plains, lightning bolts, dark dramatic clouds, powerful
cyberpunk megacity at night, neon reflections in rain-soaked streets, busy, vivid
ancient japanese pagoda surrounded by cherry blossoms, misty mountain backdrop
steampunk victorian city with brass airships, fog and gas lamps, atmospheric
abandoned gothic cathedral reclaimed by nature, vines and light beams, haunting
futuristic dubai at dusk, gleaming glass towers, golden haze, architectural wonder
medieval european village market, cobblestones and timber frames, warm morning light
tokyo shibuya crossing at night, neon chaos, hundreds of pedestrians, energy
ancient colosseum in rome at dawn, warm stone glow, historical grandeur
brutalist concrete architecture, dramatic shadows, bold geometric forms, monochrome
floating sky city above clouds, bridges and gardens, utopian fantasy, magical
venetian canal at golden hour, gondolas, reflections on water, romantic ambiance
grand central station interior, sunbeams through tall windows, architectural beauty
ancient greek temple on clifftop, aegean sea view, white marble, classical glory
moroccan medina at dusk, lanterns and spice stalls, labyrinthine streets, vibrant
new york city skyline from brooklyn bridge at blue hour, reflections on the river
massive space station orbiting earth, milky way visible, sci-fi concept art, epic
alien planet landscape, two moons rising, bioluminescent exotic flora, vivid colors
ancient dragon soaring over medieval kingdom at twilight, fire breath, epic fantasy
giant battle mech standing in ruined city, battle-worn, dramatic storm clouds
crystal cave with enormous glowing mineral formations, otherworldly, beautiful
magical portal to another realm, swirling cosmic energy, ancient stone arch
chain of floating sky islands connected by waterfalls, lush gardens, fantasy world
biopunk underwater city, domed habitats, bio-luminescent sea creatures, mysterious
nebula star formation viewed from a spacecraft window, cosmic scale, awe-inspiring
wizards tower library, floating spell books, warm candlelight, ancient magical
enchanted winter forest, glowing blue fireflies, gentle snowfall, fairy tale
mechanical clockwork city, intricate gears and pipes, steampunk industrial art
dragon turtle island, ancient beast with a forest on its shell, fantasy myth
time travel vortex, swirling clocks and light, paradox visualization, sci-fi art
elvish forest city high in the treetops, bridges and lanterns, tolkien inspired
cozy bookshop on a rainy evening, warm amber light, steamed windows, inviting
solitary lighthouse in a fierce atlantic storm, dramatic waves, hope in darkness
overgrown abandoned amusement park at dusk, nostalgic and eerie, reclaimed nature
campfire circle in a dark pine forest, warm glow, starry sky above, peaceful
sunflower field at peak summer golden hour, cheerful and vast, insects and birds
old stone lighthouse keeper cottage, cliff edge at dawn, fog rolling in from sea
traditional japanese onsen in winter, steam rising, snow on pine trees, serenity
grand ballroom frozen in time, chandeliers and dust, abandoned elegance, haunting
midnight diner on an empty highway, neon sign, rain outside, american solitude
hot air balloon festival at sunrise, dozens of balloons over a misty valley, joy"""

NEG_PROMPT  = "blurry, low quality, ugly, deformed, watermark, text, signature, bad anatomy"
BASE_SEED   = 1000
PORT        = 7862
MAX_GALLERY = 40   # max images shown in gallery

# ───────────────────────────────────────────────────
# Shared state (thread-safe)
# ───────────────────────────────────────────────────
_lock  = threading.Lock()
_state = {
    "status":          "idle",     # idle | running | stopping | complete
    "start_time":      None,
    "target_sec":      0,
    "target_rounds":   0,
    "mode":            "duration", # duration | rounds
    "total_ok":        0,
    "total_fail":      0,
    "current_model":   "",
    "current_prompt":  "",
    "current_run":     0,
    "avg_speed":       0.0,
    "images":          [],         # list of (PIL Image, label)
    "log_lines":       deque(maxlen=200),
    "by_model":        {},
    "timeline":        [],
    "stop_flag":       False,
    "last_heartbeat":  time.time(),
    "npu_pct":         0.0,
    "cpu_pct":         0.0,
}

def sget(key):
    with _lock:
        return _state[key]

def sset(key, val):
    with _lock:
        _state[key] = val

def slog(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}]  {msg}"
    with _lock:
        _state["log_lines"].append(line)
    print(line)

# ───────────────────────────────────────────────────
# NPU monitor
# ───────────────────────────────────────────────────
_npu_stop  = threading.Event()
_npu_luid  = None   # e.g. "luid_0x00000000_0x0001632F"

def _detect_npu_luid():
    """Find the NPU LUID: the only device with ONLY Compute engines.
    iGPU has 3D+Copy+Video+Compute; NPU has Compute only."""
    import re, csv as _csv, io as _io
    from collections import defaultdict as _dd
    try:
        r = subprocess.run(
            ["typeperf", "-q", "GPU Engine"],
            capture_output=True, text=True, timeout=10,
            encoding="utf-8", errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        luid_engtypes = _dd(set)
        for line in r.stdout.splitlines():
            m = re.search(r"(luid_0x[0-9A-Fa-f]+_0x[0-9A-Fa-f]+).*?engtype_([^)\\]+)", line)
            if m:
                luid_engtypes[m.group(1)].add(m.group(2).strip())
        for luid, engtypes in luid_engtypes.items():
            # NPU: every engine type contains "Compute"; no "3D" present
            if engtypes and all("Compute" in e for e in engtypes) and not any("3D" in e for e in engtypes):
                return luid
    except Exception:
        pass
    return None

def _npu_thread():
    """Poll both NPU% (typeperf GPU Engine) and CPU% (psutil) every ~3 s."""
    import csv as _csv, io as _io
    global _npu_luid

    psutil.cpu_percent(interval=None)   # prime psutil

    # Detect NPU LUID once at startup
    _npu_luid = _detect_npu_luid()
    if _npu_luid:
        slog(f"[NPU Monitor] LUID detected: {_npu_luid}")
    else:
        slog("[NPU Monitor] NPU LUID not found — NPU% unavailable")

    while not _npu_stop.is_set():
        # ── CPU % ──────────────────────────────────────────
        try:
            sset("cpu_pct", round(psutil.cpu_percent(interval=None), 1))
        except Exception:
            pass

        # ── NPU % via typeperf (2 samples for rate counters) ─────
        if _npu_luid:
            try:
                import csv as _csv2, io as _io2
                r = subprocess.run(
                    ["typeperf",
                     r"\GPU Engine(*)\Utilization Percentage",
                     "-si", "1", "-sc", "2"],
                    capture_output=True, text=True, timeout=10,
                    encoding="utf-8", errors="replace",
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                rows = [row for row in _csv2.reader(_io2.StringIO(r.stdout))
                        if any(c.strip() for c in row)]
                # rows[0]=headers  rows[1]=sample1(=0 baseline)  rows[2]=sample2(real)
                if len(rows) >= 3:
                    headers = rows[0]
                    data    = rows[2]
                    npu_vals = []
                    for col_i, hdr in enumerate(headers[1:], 1):
                        if _npu_luid in hdr:
                            try:
                                v = float(data[col_i].strip())
                                if v > 0:
                                    npu_vals.append(v)
                            except (ValueError, IndexError):
                                pass
                    sset("npu_pct", min(100.0, round(sum(npu_vals), 1)))
                    # Diagnostic: log non-zero GPU entries for first 5 cycles
                    with _lock:
                        dc = _state.setdefault("_diag_count", 0) + 1
                        _state["_diag_count"] = dc
                    if dc <= 10:
                        nz = []
                        for ci, hdr in enumerate(headers[1:], 1):
                            try:
                                v2 = float(data[ci].strip())
                                if v2 > 0.01:
                                    luid_part = hdr[hdr.find("luid_"):]
                                    luid_part = luid_part[:luid_part.find("_phys")]
                                    nz.append((luid_part, v2))
                            except Exception:
                                pass
                        if nz:
                            slog(f"[NPU diag #{dc}] npu={sum(npu_vals):.2f}% non-zero:")
                            for lp, vv in nz[:5]:
                                slog(f"  {vv:6.3f}%  {lp}")
                        else:
                            slog(f"[NPU diag #{dc}] all GPU values = 0.0")
            except Exception as exc:
                slog(f"[NPU] error: {exc}")

        time.sleep(0.5)

# ───────────────────────────────────────────────────
# System detection
# ───────────────────────────────────────────────────
def detect_system():
    mem   = psutil.virtual_memory()
    total = mem.total / 1024 ** 3
    avail = mem.available / 1024 ** 3
    if total >= 28:
        tier = "full"
        rec  = "Full tier recommended (32 GB RAM) — all 5 models"
    elif total >= 14:
        tier = "lite"
        rec  = "Lite tier recommended (16 GB RAM) — SD 1.5 + SD Turbo"
    else:
        tier = "lite"
        rec  = "Lite tier required (<16 GB RAM) — SD 1.5 only"
    return tier, total, avail, rec

def available_models():
    found = []
    for key, cfg in MODELS.items():
        if (MODELS_DIR / cfg["folder"]).exists():
            found.append(key)
    return found

def model_choices(tier_filter="all"):
    found = available_models()
    choices = []
    if tier_filter == "all":
        keys = found
    elif tier_filter == "lite":
        keys = [k for k in found if MODELS[k]["tier"] == "lite"]
    else:
        keys = found
    for k in keys:
        cfg = MODELS[k]
        choices.append(f"{cfg['name']}  ({cfg['res']}, ~{cfg['vram_gb']}GB)")
    return choices if choices else ["No models found in models/"]

# ───────────────────────────────────────────────────
# Token counter (approximate)
# ───────────────────────────────────────────────────
def count_tokens(text: str) -> int:
    """Approximate CLIP token count. Rule of thumb: ~1.3 tokens per word."""
    words = len(text.split())
    return int(words * 1.33) + 1

def validate_prompts(text: str) -> tuple[list[str], list[str]]:
    """Return (valid_prompts, warnings)."""
    lines   = [l.strip() for l in text.strip().splitlines() if l.strip()]
    warnings = []
    valid    = []
    for i, line in enumerate(lines, 1):
        t = count_tokens(line)
        if t > 77:
            warnings.append(f"Line {i}: ~{t} tokens (max 77) — will be truncated")
        has_cjk = any('\u4e00' <= c <= '\u9fff' or '\u3040' <= c <= '\u30ff'
                      for c in line)
        if has_cjk:
            warnings.append(f"Line {i}: contains non-English characters")
        valid.append(line)
    return valid, warnings

# ───────────────────────────────────────────────────
# Placeholder image (for in-progress generation)
# ───────────────────────────────────────────────────
def make_placeholder(model_name=""):
    img  = Image.new("RGB", (512, 512), (20, 18, 38))
    draw = ImageDraw.Draw(img)
    # Subtle grid
    for x in range(0, 512, 32):
        draw.line([(x, 0), (x, 512)], fill=(30, 28, 52), width=1)
    for y in range(0, 512, 32):
        draw.line([(0, y), (512, y)], fill=(30, 28, 52), width=1)
    # Pulsing circle outline
    cx, cy, r = 256, 220, 48
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=(136, 102, 238), width=2)
    draw.ellipse([cx-r+8, cy-r+8, cx+r-8, cy+r-8], outline=(100, 75, 200), width=1)
    # Text
    draw.text((256, 296), "Generating...", fill=(136, 102, 238), anchor="mm")
    if model_name:
        draw.text((256, 326), model_name, fill=(80, 75, 120), anchor="mm")
    return img

# ───────────────────────────────────────────────────
# Single inference run
# ───────────────────────────────────────────────────
def run_once(model_key, prompt, seed, run_num):
    cfg        = MODELS[model_key]
    script     = SD_RUNTIME / "test" / cfg["script"]
    model_path = MODELS_DIR / cfg["folder"]
    t_before   = time.time()

    env = os.environ.copy()
    env.update({"DD_ROOT": DD_ROOT, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"})

    # Add placeholder to gallery
    ph  = make_placeholder(cfg["name"])
    lbl = f"#{run_num}  {cfg['name']}  Generating..."
    with _lock:
        imgs = list(_state["images"])
        imgs.append((ph, lbl))
        if len(imgs) > MAX_GALLERY:
            imgs = imgs[-MAX_GALLERY:]
        _state["images"] = imgs
        _state["current_model"]  = cfg["name"]
        _state["current_prompt"] = prompt[:60] + "..."
        _state["current_run"]    = run_num

    cmd = [
        sys.executable, str(script),
        "--model_id",              cfg["model_id"],
        "--model_path",            str(model_path),
        "--custom_op_path",        CUSTOM_OP_PATH,
        "--prompt",                prompt,
        "--n_prompt",              NEG_PROMPT,
        "--num_inference_steps",   str(cfg["steps"]),
        "--guidance_scale",        str(cfg["guidance"]),
        "--seed",                  str(seed),
        "--output_path",           str(OUTPUT_DIR),
        "--num_images_per_prompt", "1",
    ]

    slog(f"#{run_num}  [{cfg['name']}]  {prompt[:50]}...")

    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           env=env, timeout=300,
                           encoding="utf-8", errors="replace")
        elapsed = time.time() - t_before

        if r.returncode != 0:
            slog(f"  FAIL  exit={r.returncode}  {elapsed:.1f}s")
            with _lock:
                _state["total_fail"] += 1
                imgs = list(_state["images"])
                if imgs:
                    fail_img = make_placeholder(cfg["name"])
                    draw = ImageDraw.Draw(fail_img)
                    draw.text((256, 256), "✗  FAILED", fill=(220, 80, 80), anchor="mm")
                    imgs[-1] = (fail_img, f"#{run_num}  {cfg['name']}  FAILED")
                    _state["images"] = imgs
            return None

        # Parse speed
        speed = None
        for ln in (r.stderr or "").splitlines():
            if "unet(NPU)" in ln and "avg time" in ln:
                try:
                    parts = ln.split()
                    for i, p in enumerate(parts):
                        if p == "mode":
                            speed = 1.0 / float(parts[i + 1].replace("s", ""))
                            break
                except Exception:
                    pass
        if speed is None:
            speed = cfg["steps"] / elapsed

        # Find generated image
        imgs_found = sorted(
            [f for f in list(OUTPUT_DIR.glob("*.png")) + list(OUTPUT_DIR.glob("*.jpg"))
             if f.stat().st_mtime >= t_before - 3],
            key=lambda x: x.stat().st_mtime, reverse=True
        )
        pil_img = Image.open(imgs_found[0]) if imgs_found else make_placeholder(cfg["name"])

        lbl_done = f"#{run_num}  {cfg['name']}  {elapsed:.0f}s  {speed:.2f}it/s"
        with _lock:
            _state["total_ok"] += 1
            imgs = list(_state["images"])
            if imgs:
                imgs[-1] = (pil_img, lbl_done)
                _state["images"] = imgs
            m = _state["by_model"].setdefault(model_key, {"count": 0, "times": [], "speeds": []})
            m["count"]  += 1
            m["times"].append(elapsed)
            m["speeds"].append(speed)
            _state["timeline"].append({"model": cfg["name"], "elapsed": elapsed, "speed": speed})
            all_speeds = [s for v in _state["by_model"].values() for s in v["speeds"]]
            _state["avg_speed"] = sum(all_speeds) / len(all_speeds) if all_speeds else 0.0

        slog(f"  OK  {elapsed:.1f}s  {speed:.3f} it/s")
        return {"elapsed": elapsed, "speed": speed}

    except subprocess.TimeoutExpired:
        slog(f"  TIMEOUT (>300s)")
        with _lock:
            _state["total_fail"] += 1
        return None
    except Exception as e:
        slog(f"  ERROR: {e}")
        with _lock:
            _state["total_fail"] += 1
        return None

# ───────────────────────────────────────────────────
# Endurance worker
# ───────────────────────────────────────────────────
def endurance_worker(model_keys, prompts, mode, target_sec, target_rounds,
                     seed_mode, fixed_seed):
    sset("status", "running")
    sset("start_time", time.time())
    sset("target_sec", target_sec)
    sset("target_rounds", target_rounds)
    sset("mode", mode)

    run_num          = 0
    last_checkpoint  = time.time()

    slog(f"Endurance test started  mode={mode}  models={[MODELS[k]['name'] for k in model_keys]}")

    while True:
        # Stop conditions
        if sget("stop_flag"):
            slog("Stop flag detected — finishing current run")
            break

        # Heartbeat check (browser closed)
        if time.time() - sget("last_heartbeat") > 20:
            slog("No heartbeat for 20s — browser closed, stopping test")
            break

        start_time = sget("start_time")
        if mode == "duration" and (time.time() - start_time) >= target_sec:
            slog("Duration target reached")
            break
        if mode == "rounds" and run_num >= target_rounds:
            slog("Round target reached")
            break

        for model_key in model_keys:
            # Re-check stops inside model loop
            if sget("stop_flag"):
                break
            if time.time() - sget("last_heartbeat") > 20:
                break
            if mode == "duration" and (time.time() - start_time) >= target_sec:
                break
            if mode == "rounds" and run_num >= target_rounds:
                break

            run_num += 1
            prompt  = prompts[(run_num - 1) % len(prompts)]
            seed    = fixed_seed if seed_mode == "fixed" else BASE_SEED + run_num

            run_once(model_key, prompt, seed, run_num)

        # Checkpoint every 30 min
        if time.time() - last_checkpoint >= 1800:
            _save_checkpoint()
            last_checkpoint = time.time()

    # Final
    _save_checkpoint()
    if HAS_MPL:
        _make_chart()
    sset("status", "complete")
    sset("stop_flag", False)
    slog("Test complete.")

def _save_checkpoint():
    with _lock:
        data = {
            "timestamp":  datetime.now().isoformat(),
            "total_ok":   _state["total_ok"],
            "total_fail": _state["total_fail"],
            "by_model": {
                k: {"count": v["count"],
                    "avg_s": round(sum(v["times"]) / len(v["times"]), 2) if v["times"] else 0}
                for k, v in _state["by_model"].items()
            },
        }
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    p  = RESULTS_DIR / f"checkpoint_{ts}.json"
    with open(p, "w") as f:
        json.dump(data, f, indent=2)
    slog(f"Checkpoint saved: {p.name}")

def _make_chart():
    with _lock:
        timeline = list(_state["timeline"])
        by_model = {k: dict(v) for k, v in _state["by_model"].items()}
    if not timeline:
        return None

    COLORS  = ["#7eb3f5", "#f5a97e", "#7ef5b0", "#f5d07e", "#c07ef5"]
    BG, PNL = "#0e0d1a", "#181728"
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7), facecolor=BG)
    fig.suptitle("NPU SD Endurance — Performance", color="white", fontsize=12, fontweight="bold")
    for ax in (ax1, ax2):
        ax.set_facecolor(PNL)
        ax.tick_params(colors="#aaaacc")
        ax.xaxis.label.set_color("#aaaacc")
        ax.yaxis.label.set_color("#aaaacc")
        ax.title.set_color("white")
        for sp in ax.spines.values():
            sp.set_edgecolor("#333355")
        ax.grid(True, alpha=0.12, linestyle="--", color="#555577")

    model_names = list(dict.fromkeys(e["model"] for e in timeline))
    cmap = {m: COLORS[i % len(COLORS)] for i, m in enumerate(model_names)}
    for i, e in enumerate(timeline):
        ax1.scatter(i + 1, e["elapsed"], color=cmap[e["model"]], s=18, zorder=3, alpha=0.85)
    import matplotlib.patches as mp
    ax1.legend(handles=[mp.Patch(color=cmap[m], label=m) for m in model_names],
               loc="upper right", framealpha=0.25, labelcolor="white",
               facecolor=PNL, edgecolor="#444466")
    ax1.set_title("Elapsed Time per Image", fontsize=10)
    ax1.set_xlabel("Image #")
    ax1.set_ylabel("Time (s)")

    keys   = list(by_model.keys())
    labels = [MODELS[k]["name"] for k in keys]
    speeds = [sum(by_model[k]["speeds"]) / len(by_model[k]["speeds"])
              if by_model[k]["speeds"] else 0 for k in keys]
    bars = ax2.bar(labels, speeds,
                   color=[COLORS[i % len(COLORS)] for i in range(len(keys))], alpha=0.8)
    for bar, s in zip(bars, speeds):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.002,
                 f"{s:.3f}", ha="center", va="bottom", color="white", fontsize=8)
    ax2.set_title("Average Speed by Model", fontsize=10)
    ax2.set_ylabel("it/s")
    ax2.tick_params(axis="x", labelcolor="white")

    plt.tight_layout()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    p  = RESULTS_DIR / f"chart_{ts}.png"
    plt.savefig(p, dpi=130, bbox_inches="tight", facecolor=BG)
    plt.close()
    return p

# ───────────────────────────────────────────────────
# Gradio UI callbacks
# ───────────────────────────────────────────────────
def heartbeat():
    sset("last_heartbeat", time.time())

def start_test(mode, duration_preset, custom_duration_min,
               rounds_preset, custom_rounds,
               tier, model_selection,
               prompt_text, seed_mode, fixed_seed):

    if sget("status") == "running":
        return gr.update(value="⚠ Test already running"), gr.update()

    # Parse target
    if mode == "By Duration":
        preset_sec = DURATION_PRESETS.get(duration_preset)
        if preset_sec is None:
            target_sec = int(custom_duration_min * 60)
        else:
            target_sec = preset_sec
        target_rounds = 999999
        run_mode = "duration"
    else:
        preset_r = ROUNDS_PRESETS.get(rounds_preset)
        if preset_r is None:
            target_rounds = int(custom_rounds)
        else:
            target_rounds = preset_r
        target_sec = 999999
        run_mode = "rounds"

    # Parse prompts
    prompts, warnings = validate_prompts(prompt_text)
    if not prompts:
        return gr.update(value="⚠ No valid prompts"), gr.update()

    # Model keys
    found = available_models()
    if tier in ("Lite (16 GB RAM)", "Lite"):
        keys = [k for k in found if MODELS[k]["tier"] == "lite"]
    else:
        keys = found
    if not keys:
        return gr.update(value="⚠ No models found in models/ folder"), gr.update()

    # Reset state
    with _lock:
        _state["total_ok"]    = 0
        _state["total_fail"]  = 0
        _state["images"]      = []
        _state["log_lines"]   = deque(maxlen=200)
        _state["by_model"]    = {}
        _state["timeline"]    = []
        _state["stop_flag"]   = False
        _state["last_heartbeat"] = time.time()
        _state["_diag_count"] = 0   # reset so NPU diagnostics fire again

    # Start worker
    t = threading.Thread(
        target=endurance_worker,
        args=(keys, prompts, run_mode, target_sec, target_rounds,
              seed_mode.lower().replace(" ", "_"), int(fixed_seed)),
        daemon=True
    )
    t.start()

    warn_txt = "\n".join(warnings) if warnings else ""
    info = f"Started: {len(keys)} model(s), {len(prompts)} prompts"
    if warn_txt:
        info += f"\n⚠ Warnings:\n{warn_txt}"
    return gr.update(value=f"✅  {info}"), gr.update(interactive=False)

def stop_test():
    sset("stop_flag", True)
    sset("status", "stopping")
    return gr.update(value="⏹  Stop signal sent...")

def refresh_ui():
    """Called by gr.Timer every 2 seconds."""
    with _lock:
        status    = _state["status"]
        start     = _state["start_time"]
        target_s  = _state["target_sec"]
        target_r  = _state["target_rounds"]
        mode      = _state["mode"]
        total_ok  = _state["total_ok"]
        total_fail= _state["total_fail"]
        cur_model = _state["current_model"]
        cur_prompt= _state["current_prompt"]
        cur_run   = _state["current_run"]
        avg_speed = _state["avg_speed"]
        npu_pct   = _state["npu_pct"]
        cpu_pct   = _state["cpu_pct"]
        images    = list(_state["images"])
        log_lines = list(_state["log_lines"])

    # Time / progress
    if start:
        elapsed = time.time() - start
        if mode == "duration":
            pct = min(100, elapsed / target_s * 100) if target_s > 0 else 0
            eta = max(0, target_s - elapsed)
            time_str = f"{_fmt(elapsed)} / {_fmt(target_s)}"
            prog_label = f"{pct:.1f}%  ETA {_fmt(eta)}"
        else:
            pct = min(100, cur_run / target_r * 100) if target_r > 0 else 0
            time_str = f"Run {cur_run} / {target_r}"
            prog_label = f"{pct:.1f}%  elapsed {_fmt(elapsed)}"
    else:
        pct, time_str, prog_label = 0, "--:--:-- / --:--:--", "Not started"
        elapsed = 0

    imgs_hr = (total_ok / (elapsed / 3600)) if elapsed > 60 and total_ok > 0 else 0.0
    dot_cls = {"idle":"idle","running":"running","stopping":"stopping","complete":"complete"}.get(status,"idle")

    npu_str = f"{npu_pct:.0f}%" if npu_pct > 0 else "—"
    status_html = f"""
<div class="metrics">
  <div class="m-status">
    <span class="m-dot {dot_cls}"></span>
    <span class="m-label">{status}</span>
  </div>
  <div class="m-time">{time_str}</div>
  <div class="m-progress"><div class="m-fill" style="width:{pct:.1f}%"></div></div>
  <div class="m-items">
    <div class="m-item"><span class="m-val">{total_ok}</span><span class="m-key">Images</span></div>
    <div class="m-item"><span class="m-val">{total_fail}</span><span class="m-key">Failed</span></div>
    <div class="m-item"><span class="m-val">{imgs_hr:.1f}</span><span class="m-key">img/hr</span></div>
    <div class="m-item"><span class="m-val">{avg_speed:.3f}</span><span class="m-key">it/s</span></div>
    <div class="m-item"><span class="m-val">{npu_str}</span><span class="m-key">NPU</span></div>
    <div class="m-item"><span class="m-val">{cpu_pct:.0f}%</span><span class="m-key">CPU</span></div>
  </div>
  <div class="m-cur">{cur_prompt or "Configure and press Start"}</div>
  <div class="m-model">{cur_model and f"#{cur_run}  {cur_model}" or ""}</div>
</div>"""

    log_text = "\n".join(reversed(list(log_lines)[-60:]))
    gallery  = [(img, lbl) for img, lbl in images]

    return status_html, gallery, log_text

def _fmt(sec):
    sec = int(sec)
    return f"{sec//3600:02d}:{(sec%3600)//60:02d}:{sec%60:02d}"

def on_mode_change(mode):
    if mode == "By Duration":
        return gr.update(visible=True), gr.update(visible=False)
    return gr.update(visible=False), gr.update(visible=True)

def on_duration_preset(choice):
    return gr.update(visible=(choice == "Custom"))

def on_rounds_preset(choice):
    return gr.update(visible=(choice == "Custom"))

def on_seed_mode(choice):
    return gr.update(visible=(choice in ("Fixed seed", "Fixed")))

def count_prompts_tokens(text):
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    warnings = []
    for i, line in enumerate(lines, 1):
        t = count_tokens(line)
        if t > 77:
            warnings.append(f"Line {i}: ~{t} tokens (exceeds 77 limit)")
    if warnings:
        return f"⚠ {len(lines)} prompts  —  " + "  |  ".join(warnings[:3])
    return f"✅  {len(lines)} prompts, all within 77-token limit"

def get_recommendation():
    _, total_gb, avail_gb, rec = detect_system()
    found = available_models()
    model_info = []
    for k in found:
        cfg = MODELS[k]
        model_info.append(f"{cfg['name']} ({cfg['res']})")
    models_str = ", ".join(model_info) if model_info else "None found"
    return (f"RAM : {total_gb:.1f} GB  (avail {avail_gb:.1f} GB)\n"
            f"{rec}\n"
            f"Models : {models_str}")

# ───────────────────────────────────────────────────
# Neumorphic CSS
# ───────────────────────────────────────────────────
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Cal+Sans&display=swap');

:root {
    --bg:     #ffffff;
    --bg-2:   #f9fafb;
    --bg-3:   #f3f4f6;
    --border: #e5e7eb;
    --border2:#d1d5db;
    --text:   #111827;
    --text2:  #6b7280;
    --text3:  #9ca3af;
    --acc:    #111827;
    --acc-b:  #2563eb;
    --green:  #059669;
    --amber:  #d97706;
    --red:    #dc2626;
    --r-xl:14px; --r-lg:10px; --r-md:7px;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body, .gradio-container {
    background: var(--bg) !important;
    font-family: 'Inter', system-ui, sans-serif !important;
    color: var(--text) !important; min-height: 100vh;
}
.gradio-container > .main {
    max-width: 1160px !important;
    margin: 0 auto !important;
    padding: 0 1.4rem !important;
}

/* ── Header ── */
#header {
    padding: 1.6rem 0 1.1rem;
    display: flex; align-items: center; gap: 1rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1.2rem;
}
#wordmark {
    font-family: 'Inter', sans-serif !important;
    font-size: 1.30rem !important; font-weight: 700 !important;
    color: var(--text) !important; letter-spacing: -0.03em;
}
#wordmark em { color: var(--acc-b); font-style: normal; }
#tagline {
    font-size: 0.66rem !important; font-weight: 500 !important;
    letter-spacing: 0.14em !important; text-transform: uppercase !important;
    color: var(--text3) !important;
    padding: 0.18rem 0.55rem;
    border: 1px solid var(--border);
    border-radius: 99px;
    background: var(--bg-2);
}

/* ── Panels ── */
.left-card {
    background: var(--bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r-xl) !important;
    padding: 1.3rem !important;
    margin-right: 0.6rem !important;
}
.right-card {
    background: var(--bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r-xl) !important;
    padding: 1.3rem !important;
}

/* ── Section label ── */
.sec-label {
    font-size: 0.60rem !important; font-weight: 600 !important;
    letter-spacing: 0.18em !important; text-transform: uppercase !important;
    color: var(--text3) !important; margin-bottom: 0.50rem !important;
    display: block;
}

/* ── Suppress Gradio locale labels ── */
.gradio-container .gradio-radio > .form > .label-wrap,
.gradio-container .gradio-radio > .label-wrap { display: none !important; }

/* ── Inputs ── */
.gradio-container textarea,
.gradio-container input[type=text],
.gradio-container input[type=number] {
    background: var(--bg-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r-md) !important;
    color: var(--text) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.84rem !important;
    padding: 0.56rem 0.80rem !important;
    box-shadow: none !important;
    transition: border-color 0.15s !important;
}
.gradio-container textarea:focus,
.gradio-container input:focus {
    outline: none !important;
    border-color: var(--acc-b) !important;
    background: var(--bg) !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.10) !important;
}

/* ── Labels ── */
.gradio-container label > span,
.gradio-container .label-wrap span {
    font-size: 0.60rem !important; font-weight: 600 !important;
    letter-spacing: 0.14em !important; text-transform: uppercase !important;
    color: var(--text3) !important;
}

/* ── Radio — pill style ── */
.gradio-container .gradio-radio label {
    background: var(--bg-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 99px !important;
    padding: 0.24rem 0.70rem !important;
    font-size: 0.73rem !important; font-weight: 500 !important;
    color: var(--text2) !important; cursor: pointer !important;
    box-shadow: none !important; transition: all 0.12s !important;
}
.gradio-container .gradio-radio label:has(input:checked) {
    background: var(--acc) !important;
    border-color: var(--acc) !important;
    color: #ffffff !important;
}
.gradio-container .gradio-radio label:hover:not(:has(input:checked)) {
    border-color: var(--border2) !important;
    background: var(--bg-3) !important;
}
.gradio-container .gradio-radio label span { display: none !important; }
.gradio-container .gradio-radio label input { display: none !important; }

/* ── Dropdown ── */
.gradio-container select, .gradio-container .wrap-inner {
    background: var(--bg-2) !important; border: 1px solid var(--border) !important;
    border-radius: var(--r-md) !important; color: var(--text) !important;
    padding: 0.48rem 0.75rem !important; font-size: 0.83rem !important;
    box-shadow: none !important;
}

/* ── START button ── */
#start-btn > button {
    width: 100% !important; padding: 0.72rem 0 !important;
    background: var(--acc) !important; color: #ffffff !important;
    border: none !important; border-radius: var(--r-lg) !important;
    font-size: 0.87rem !important; font-weight: 600 !important;
    letter-spacing: 0.01em !important; cursor: pointer !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.08) !important;
    transition: all 0.14s !important;
}
#start-btn > button:hover {
    background: #1f2937 !important;
    box-shadow: 0 4px 8px rgba(0,0,0,0.16) !important;
}

/* ── STOP button ── */
#stop-btn > button {
    width: 100% !important; padding: 0.48rem 0 !important;
    background: var(--bg) !important; border: 1px solid var(--border2) !important;
    border-radius: var(--r-md) !important;
    font-size: 0.75rem !important; font-weight: 500 !important;
    color: var(--text2) !important; cursor: pointer !important;
    box-shadow: none !important; transition: all 0.12s !important;
}
#stop-btn > button:hover { border-color: var(--red) !important; color: var(--red) !important; }

/* ── Report button ── */
#report-btn > button {
    width: 100% !important; padding: 0.48rem 0 !important;
    background: var(--bg-2) !important; border: 1px solid var(--border) !important;
    border-radius: var(--r-md) !important;
    font-size: 0.73rem !important; font-weight: 500 !important;
    color: var(--text2) !important; cursor: pointer !important;
    box-shadow: none !important; transition: all 0.12s !important;
}
#report-btn > button:hover { border-color: var(--acc-b) !important; color: var(--acc-b) !important; }

/* ── Gallery — blend into white ── */
.gradio-container .gallery,
.gradio-container .gallery > div,
.gradio-container [data-testid="gallery"],
.gradio-container .grid-wrap {
    background: var(--bg-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r-lg) !important;
    padding: 4px !important; box-shadow: none !important;
}

/* ── Status panel ── */
.sp {
    background: var(--bg); border: 1px solid var(--border);
    border-radius: var(--r-xl); padding: 1rem 1.3rem;
    margin-bottom: 0.7rem; font-family: 'JetBrains Mono', monospace;
}
.sp-header { display: flex; align-items: center; gap: 0.9rem; margin-bottom: 0.8rem; }
.sp-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; background: var(--text3); }
.sp-dot.running { background: var(--green); box-shadow: 0 0 0 3px rgba(5,150,105,0.15); }
.sp-dot.stopping { background: var(--amber); }
.sp-dot.complete { background: var(--acc-b); }
.sp-status { font-size: 0.62rem; font-weight: 600; letter-spacing: 0.14em; text-transform: uppercase; color: var(--text3); }
.sp-time { font-size: 0.96rem; font-weight: 500; color: var(--text); flex: 1; }
.sp-ptrack { flex: 2; height: 2px; background: var(--bg-3); border-radius: 99px; overflow: hidden; }
.sp-pfill { height: 100%; background: var(--acc); border-radius: 99px; transition: width 1s ease; }
.sp-pct { font-size: 0.72rem; color: var(--text3); min-width: 3ch; text-align: right; }
.sp-metrics { display: flex; gap: 2rem; margin-bottom: 0.6rem; padding: 0.6rem 0; border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); }
.sp-metric { display: flex; flex-direction: column; gap: 0.14rem; }
.sp-val { font-size: 1.22rem; font-weight: 700; color: var(--text); line-height: 1; }
.sp-lbl { font-size: 0.55rem; font-weight: 600; letter-spacing: 0.14em; text-transform: uppercase; color: var(--text3); }
.sp-cur { font-size: 0.69rem; color: var(--text3); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; padding-top: 0.6rem; }

/* ── Log / Report ── */
#log-box textarea, #report-box textarea {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.68rem !important; line-height: 1.62 !important;
    color: var(--text2) !important; background: var(--bg-2) !important;
    border: 1px solid var(--border) !important; box-shadow: none !important;
}
#report-box textarea { color: var(--text) !important; }
#rec-box textarea {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.71rem !important; color: var(--text2) !important;
    background: var(--bg-2) !important; border: 1px solid var(--border) !important;
    box-shadow: none !important;
}
#token-info textarea, #start-info textarea {
    font-size: 0.70rem !important; color: var(--text3) !important;
    background: transparent !important; border: none !important;
    box-shadow: none !important; padding: 0 !important;
}

/* ── Accordion ── */
.gradio-container details {
    background: var(--bg) !important; border: 1px solid var(--border) !important;
    border-radius: var(--r-lg) !important; box-shadow: none !important;
    padding: 0 0.9rem !important; margin-bottom: 0.6rem !important;
}
.gradio-container details summary {
    font-size: 0.62rem !important; font-weight: 600 !important;
    letter-spacing: 0.16em !important; text-transform: uppercase !important;
    color: var(--text3) !important; padding: 0.65rem 0 !important;
    cursor: pointer !important; list-style: none !important;
}
.gradio-container details summary::-webkit-details-marker { display: none; }

/* ── Divider ── */
.neu-div { height: 1px; background: var(--border); margin: 0.7rem 0; border: none; }

/* ── Footer ── */
#footer {
    text-align: center; padding: 0.6rem 0 0.2rem;
    font-size: 0.59rem !important; letter-spacing: 0.14em !important;
    text-transform: uppercase !important; color: var(--text3) !important;
    border-top: 1px solid var(--border); margin-top: 0.8rem;
}
#hiko-credit {
    text-align: center; padding: 0.2rem 0 1.4rem;
    font-size: 0.56rem !important; letter-spacing: 0.10em !important;
    color: var(--text3) !important; opacity: 0.45;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: var(--bg-2); }
::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 4px; }
.gradio-container .gap { gap: 0.7rem !important; }

/* Metrics vertical panel */
.metrics-col > div { height: 100% !important; }
.metrics {
    background: var(--bg-2); border: 1px solid var(--border);
    border-radius: var(--r-lg); padding: 1rem 0.9rem;
    display: flex; flex-direction: column; gap: 0.6rem;
    font-family: 'JetBrains Mono', monospace; min-height: 400px;
}
.m-status { display: flex; align-items: center; gap: 0.5rem; }
.m-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--text3); flex-shrink: 0; }
.m-dot.running { background: var(--green); box-shadow: 0 0 0 3px rgba(5,150,105,0.15); }
.m-dot.stopping { background: var(--amber); }
.m-dot.complete { background: var(--acc-b); }
.m-label { font-size: 0.58rem; font-weight: 700; letter-spacing: 0.16em; text-transform: uppercase; color: var(--text3); }
.m-time { font-size: 0.80rem; color: var(--text); font-weight: 500; }
.m-progress { height: 2px; background: var(--bg-3); border-radius: 99px; overflow: hidden; }
.m-fill { height: 100%; background: var(--acc); border-radius: 99px; transition: width 1s ease; }
.m-items { display: flex; flex-direction: column; gap: 0.75rem; flex: 1; padding: 0.55rem 0; border-top: 1px solid var(--border); }
.m-item { display: flex; flex-direction: column; gap: 0.08rem; }
.m-val { font-size: 1.32rem; font-weight: 700; color: var(--text); line-height: 1; }
.m-key { font-size: 0.52rem; font-weight: 600; letter-spacing: 0.14em; text-transform: uppercase; color: var(--text3); }
.m-cur { font-size: 0.60rem; color: var(--text3); overflow: hidden; word-break: break-all; border-top: 1px solid var(--border); padding-top: 0.5rem; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; }
.m-model { font-size: 0.62rem; color: var(--acc-b); font-weight: 600; }

/* Compact sys-info */
.sys-info { display: flex; flex-direction: column; gap: 0.22rem; padding: 0.5rem 0.7rem; background: var(--bg-2); border: 1px solid var(--border); border-radius: var(--r-md); }
.sys-row { display: flex; align-items: baseline; gap: 0.5rem; }
.sys-k { font-size: 0.55rem; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase; color: var(--text3); min-width: 3.5rem; flex-shrink: 0; }
.sys-v { font-size: 0.72rem; color: var(--text2); font-family: 'JetBrains Mono', monospace; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* Compact settings panel */
.settings-group {
    display: flex; flex-direction: column; gap: 0; 
    border: 1px solid var(--border); border-radius: var(--r-lg);
    overflow: hidden;
}
.sg-row {
    display: flex; align-items: center; gap: 0;
    border-bottom: 1px solid var(--border); padding: 0;
}
.sg-row:last-child { border-bottom: none; }
.sg-label {
    font-size: 0.58rem; font-weight: 700; letter-spacing: 0.16em;
    text-transform: uppercase; color: var(--text3);
    padding: 0.55rem 0.65rem; min-width: 52px; flex-shrink: 0;
    border-right: 1px solid var(--border); background: var(--bg-2);
}
.sg-content {
    padding: 0.42rem 0.65rem; flex: 1; min-width: 0;
}
/* Make radio groups inside sg-content horizontal and tiny */
.sg-content .gradio-container .gradio-radio > div,
.sg-content .gradio-radio > div { display: flex !important; flex-wrap: wrap !important; gap: 0.3rem !important; }
.gradio-container .form { gap: 0.7rem !important; }
"""










# ───────────────────────────────────────────────────
# Report generation
# ───────────────────────────────────────────────────
def generate_report():
    """Build a plain-text monospace performance report."""
    with _lock:
        status     = _state["status"]
        start      = _state["start_time"]
        mode       = _state["mode"]
        total_ok   = _state["total_ok"]
        total_fail = _state["total_fail"]
        by_model   = {k: dict(v) for k, v in _state["by_model"].items()}
        npu_pct    = _state["npu_pct"]

    if not start:
        return "No test data yet. Run a test first."

    elapsed   = time.time() - start
    total     = total_ok + total_fail
    ok_pct    = total_ok / total * 100 if total > 0 else 0
    imgs_hr   = total_ok / (elapsed / 3600) if elapsed > 60 and total_ok > 0 else 0

    _, gb_total, gb_avail, rec = detect_system()
    tier_str, _, _, _ = detect_system()

    W  = 60
    ln = []
    ln.append("=" * W)
    ln.append("  NPU SD ENDURANCE TEST - PERFORMANCE REPORT")
    ln.append("=" * W)
    ln.append(f"  Generated   : {datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}")
    ln.append(f"  Duration    : {_fmt(elapsed)}")
    ln.append(f"  Mode        : {mode.capitalize()}")
    ln.append(f"  Status      : {status.upper()}")
    ln.append(f"  Total runs  : {total}  (OK: {total_ok}  FAIL: {total_fail})")
    ln.append(f"  Success rate: {ok_pct:.1f}%")
    ln.append("")
    ln.append("  SYSTEM")
    ln.append(f"  {'RAM':<20}: {gb_total:.1f} GB  (avail {gb_avail:.1f} GB)")
    ln.append(f"  {'Tier':<20}: {tier_str.upper()}")
    ln.append(f"  {'NPU avg util':<20}: {npu_pct:.1f}%  (CPU avg: {_state.get('cpu_pct', 0):.1f}%)")
    ln.append("")

    if by_model:
        ln.append("  PER-MODEL RESULTS")
        SEP = "  " + chr(8212) * (W - 2)
        HDR = (f"  {'Model':<16} {'N':>4} {'Avg(s)':>7} {'Min':>6} "
               f"{'Max':>6} {'Std':>6} {'it/s':>7} {'img/hr':>7}")
        ln.append(SEP)
        ln.append(HDR)
        ln.append(SEP)

        all_times = []
        all_speeds = []
        for key, v in by_model.items():
            if not v["times"]:
                continue
            name   = MODELS[key]["name"]
            t      = v["times"]
            sp     = v["speeds"]
            avg_t  = sum(t) / len(t)
            min_t  = min(t)
            max_t  = max(t)
            std_t  = (sum((x - avg_t)**2 for x in t) / len(t)) ** 0.5
            avg_s  = sum(sp) / len(sp) if sp else 0
            img_hr = 3600 / avg_t if avg_t > 0 else 0
            all_times.extend(t)
            all_speeds.extend(sp)
            ln.append(f"  {name:<16} {len(t):>4} {avg_t:>7.2f} {min_t:>6.2f} "
                      f"{max_t:>6.2f} {std_t:>6.2f} {avg_s:>7.3f} {img_hr:>7.1f}")

        ln.append(SEP)

        # Overall row
        if all_times:
            oa  = sum(all_times) / len(all_times)
            os_ = sum(all_speeds) / len(all_speeds) if all_speeds else 0
            ln.append(f"  {'OVERALL':<16} {len(all_times):>4} {oa:>7.2f} "
                      f"{min(all_times):>6.2f} {max(all_times):>6.2f} "
                      f"{(sum((t-oa)**2 for t in all_times)/len(all_times))**0.5:>6.2f} "
                      f"{os_:>7.3f} {imgs_hr:>7.1f}")

        ln.append("")
        ln.append("  STABILITY ANALYSIS")
        ln.append(SEP)
        for key, v in by_model.items():
            if len(v["times"]) < 4:
                ln.append(f"  {MODELS[key]['name']:<20}: insufficient data (<4 runs)")
                continue
            t    = v["times"]
            h    = len(t) // 2
            f_   = sum(t[:h]) / h
            s_   = sum(t[h:]) / (len(t) - h)
            pct  = (s_ - f_) / f_ * 100
            flag = ("THROTTLING DETECTED" if pct > 5
                    else "warm-up boost" if pct < -5
                    else "STABLE")
            ln.append(f"  {MODELS[key]['name']:<20}: {flag:<22}  trend {pct:+.1f}%")

    ln.append("")
    ln.append(f"  Overall throughput : {imgs_hr:.1f} images/hr")
    ln.append("")
    ln.append("=" * W)
    ln.append("  Design by Hiko")
    ln.append("=" * W)

    report_text = "\n".join(ln)

    # Save to file
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = RESULTS_DIR / f"report_{ts}.txt"
    try:
        path.write_text(report_text, encoding="utf-8")
        report_text += f"\n\n  [Saved to {path}]"
    except Exception as e:
        report_text += f"\n\n  [Save failed: {e}]"

    return report_text

# ───────────────────────────────────────────────────
# Build UI
# ───────────────────────────────────────────────────
def build_ui():
    tier_auto, total_gb, avail_gb, rec = detect_system()
    found_models = available_models()
    models_str = ", ".join(MODELS[k]["name"] for k in found_models) or "None"
    tier_default = "Full" if tier_auto == "full" else "Lite"
    tier_label   = "Full" if tier_auto == "full" else "Lite"
    ram_line     = f"{total_gb:.0f} GB RAM  ({tier_label} tier)"

    with gr.Blocks(css=CSS, title="NPU BenchMark for AMD") as demo:

        # ── Header ──────────────────────────────────
        gr.HTML(f"""
        <div id="header">
            <span id="wordmark">NPU <em>BenchMark</em> for AMD</span>
            <span id="tagline">Ryzen AI · XDNA2+ · RyzenAI 1.7.1</span>
            <span id="tagline" style="margin-left:auto;opacity:0.6">{ram_line}</span>
        </div>""")

        with gr.Row(equal_height=True):

            # ── LEFT: Consolidated compact settings ──
            with gr.Column(scale=3, min_width=260, elem_classes="left-card"):

                # Models line (very compact)
                gr.HTML(f'<div style="font-size:0.65rem;color:var(--text3);padding:0.3rem 0 0.6rem;font-family:JetBrains Mono,monospace;line-height:1.6">{models_str}</div>')

                # ── Mode ────────────────────────────
                gr.HTML('<span class="sec-label">Test Mode</span>')
                mode_radio = gr.Radio(
                    choices=["By Duration", "By Rounds"],
                    value="By Duration", label="Mode", interactive=True
                )

                with gr.Column(visible=True) as dur_col:
                    duration_preset = gr.Radio(
                        choices=list(DURATION_PRESETS.keys()),
                        value="1 hour", label="Duration", interactive=True
                    )
                    custom_dur_min = gr.Number(
                        label="Minutes", value=60, minimum=1, maximum=1440,
                        visible=False, interactive=True
                    )

                with gr.Column(visible=False) as rnd_col:
                    rounds_preset = gr.Radio(
                        choices=list(ROUNDS_PRESETS.keys()),
                        value="100 rounds", label="Rounds", interactive=True
                    )
                    custom_rounds = gr.Number(
                        label="Count", value=100, minimum=1, maximum=99999,
                        visible=False, interactive=True
                    )

                gr.HTML('<div class="neu-div"></div>')

                # ── Tier + Seed in one row ──────────
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.HTML('<span class="sec-label">Tier</span>')
                        tier_radio = gr.Radio(
                            choices=["Lite", "Full"],
                            value=tier_default, label="Tier", interactive=True
                        )
                    with gr.Column(scale=1):
                        gr.HTML('<span class="sec-label">Seed</span>')
                        seed_mode = gr.Radio(
                            choices=["Random", "Fixed"],
                            value="Random", label="Seed mode", interactive=True
                        )

                fixed_seed_num = gr.Number(
                    label="Seed value", value=42,
                    minimum=0, maximum=2147483647,
                    visible=False, interactive=True
                )

                gr.HTML('<div class="neu-div"></div>')

                # ── Prompts (collapsed) ──────────────
                with gr.Accordion("Prompts  (60 scenes, click to edit)", open=False):
                    gr.HTML('<div style="font-size:0.65rem;color:var(--text3);margin-bottom:0.4rem">English only · max 77 tokens per line</div>')
                    prompt_box = gr.Textbox(
                        value=DEFAULT_PROMPTS, lines=6, max_lines=12,
                        label="", interactive=True
                    )
                    token_info = gr.Textbox(
                        value="60 prompts — all within 77-token limit",
                        label="", interactive=False,
                        elem_id="token-info", lines=1
                    )

                gr.HTML('<div class="neu-div"></div>')

                # ── Buttons ─────────────────────────
                start_btn  = gr.Button("▶  Start Benchmark", elem_id="start-btn")
                gr.HTML('<div style="height:0.28rem"></div>')
                stop_btn   = gr.Button("Stop", elem_id="stop-btn")
                start_info = gr.Textbox(
                    value="", label="", interactive=False,
                    lines=1, elem_id="start-info"
                )

            # ── RIGHT: Gallery + Metrics sidebar ─────
            with gr.Column(scale=8, elem_classes="right-card"):
                gr.HTML('<span class="sec-label">Generated Images (live)</span>')
                with gr.Row(equal_height=True):
                    with gr.Column(scale=8):
                        gallery = gr.Gallery(
                            label="", columns=4, rows=5,
                            height=600, object_fit="cover",
                            show_label=False
                        )
                    with gr.Column(scale=3, min_width=130, elem_classes="metrics-col"):
                        status_html = gr.HTML("""
<div class="metrics">
  <div class="m-status"><span class="m-dot idle"></span><span class="m-label">IDLE</span></div>
  <div class="m-time">--:--:-- / --:--:--</div>
  <div class="m-progress"><div class="m-fill" style="width:0%"></div></div>
  <div class="m-items">
    <div class="m-item"><span class="m-val">0</span><span class="m-key">Images</span></div>
    <div class="m-item"><span class="m-val">0</span><span class="m-key">Failed</span></div>
    <div class="m-item"><span class="m-val">0.0</span><span class="m-key">img/hr</span></div>
    <div class="m-item"><span class="m-val">0.000</span><span class="m-key">it/s</span></div>
    <div class="m-item"><span class="m-val">—</span><span class="m-key">NPU</span></div>
    <div class="m-item"><span class="m-val">0%</span><span class="m-key">CPU</span></div>
  </div>
  <div class="m-cur">Configure and press Start</div>
</div>""")

        # ── Accordions ───────────────────────────────
        with gr.Accordion("Run Log", open=False):
            log_box = gr.Textbox(
                label="", lines=10, max_lines=18,
                interactive=False, value="", elem_id="log-box"
            )

        with gr.Accordion("Performance Report", open=False):
            report_btn = gr.Button("Generate Report", elem_id="report-btn")
            report_box = gr.Textbox(
                label="", lines=20, max_lines=35,
                interactive=False, value="", elem_id="report-box"
            )

        gr.HTML('<div id="footer">NPU BenchMark for AMD  ·  Ryzen AI XDNA2+</div>')
        gr.HTML('<div id="hiko-credit">Design by Hiko</div>')

        # ── Timer ────────────────────────────────────
        timer = gr.Timer(value=2)
        timer.tick(fn=refresh_ui, outputs=[status_html, gallery, log_box])
        timer.tick(fn=heartbeat)

        # ── Events ───────────────────────────────────
        mode_radio.change(fn=on_mode_change, inputs=[mode_radio], outputs=[dur_col, rnd_col])
        duration_preset.change(fn=on_duration_preset, inputs=[duration_preset], outputs=[custom_dur_min])
        rounds_preset.change(fn=on_rounds_preset, inputs=[rounds_preset], outputs=[custom_rounds])
        seed_mode.change(fn=on_seed_mode, inputs=[seed_mode], outputs=[fixed_seed_num])
        prompt_box.change(fn=count_prompts_tokens, inputs=[prompt_box], outputs=[token_info])

        start_btn.click(
            fn=start_test,
            inputs=[mode_radio, duration_preset, custom_dur_min,
                    rounds_preset, custom_rounds,
                    tier_radio, gr.State(None),
                    prompt_box, seed_mode, fixed_seed_num],
            outputs=[start_info, prompt_box]
        )
        stop_btn.click(fn=stop_test, outputs=[start_info])
        report_btn.click(fn=generate_report, outputs=[report_box])

    return demo


# ───────────────────────────────────────────────────
# Main
# ───────────────────────────────────────────────────
def main():
    print("=" * 56)
    print("  NPU SD Endurance Test  — Gradio Edition")
    print("  AMD Ryzen AI  XDNA2+  RyzenAI 1.7.1")
    print(f"  {datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}")
    print("=" * 56)

    tier, total_gb, avail_gb, rec = detect_system()
    found = available_models()
    npu_ok = Path(XRT_SMI).exists()

    print(f"  RAM      {total_gb:.1f} GB  (avail {avail_gb:.1f} GB)")
    print(f"  Tier     {tier.upper()}  —  {rec}")
    print(f"  Models   {', '.join(MODELS[k]['name'] for k in found) or 'NONE FOUND'}")
    print(f"  xrt-smi  {'OK' if npu_ok else 'NOT FOUND'}")
    print(f"  Results  {RESULTS_DIR}")
    print(f"  URL      http://127.0.0.1:{PORT}")

    if not found:
        print("\n  [Warning] No model folders detected in:")
        print(f"  {MODELS_DIR}")
        print("  The app will launch but cannot generate images until models are added.\n")

    # Start NPU monitor
    _npu_stop.clear()
    if npu_ok:
        threading.Thread(target=_npu_thread, daemon=True).start()

    demo = build_ui()

    # Auto-open browser after short delay
    def _open():
        time.sleep(2)
        webbrowser.open(f"http://127.0.0.1:{PORT}")
    threading.Thread(target=_open, daemon=True).start()

    demo.launch(
        server_name="127.0.0.1",
        server_port=PORT,
        show_error=True,
        share=False,
        inbrowser=False,   # we handle browser open manually above
    )

    _npu_stop.set()


if __name__ == "__main__":
    main()
