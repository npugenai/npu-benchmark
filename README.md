# NPU BenchMark for AMD

> A browser-based Stable Diffusion stress test and benchmark tool for AMD Ryzen AI NPU (XDNA2).  
> Real NPU-accelerated image generation benchmark — not CPU, not GPU.

**Design by Hiko**

---

## What This Is

This tool runs Stable Diffusion **natively on the AMD Ryzen AI NPU** via the VitisAI execution provider, measuring real inference throughput, stability, and performance over time.

**Tested on:**
- AMD Ryzen AI 9 HX 370 (Krackan Point, XDNA2, 51 TOPS)
- RyzenAI Software 1.7.1
- Windows 11

---

## Features

- **5 SD models** — SD 1.5, SD Turbo, SDXL Turbo, Segmind Vega, SDXL Base
- **2 test modes** — By Duration (10 min → 24 hr) or By Rounds (10 → 1500)
- **60 diverse scene prompts** — covers landscapes, cityscapes, fantasy, sci-fi, and more
- **Live browser dashboard** — real-time image gallery + metrics sidebar
- **Metrics** — Images generated, failures, img/hr, it/s, CPU%
- **Performance report** — plain-text monospace output, auto-saved as `.txt`
- **Stability analysis** — detects thermal throttling trends per model
- **Auto browser launch** — opens `http://127.0.0.1:7862` on start
- **Heartbeat detection** — closing the browser tab stops the test

---

## Prerequisites

### 1. Hardware

- AMD Ryzen AI processor with **XDNA2 NPU**
  - Strix Point (Ryzen AI 300 series)
  - Krackan Point (Ryzen AI 300 series)

- Minimum 16 GB RAM (32 GB recommended for Full tier with all 5 models)

### 2. AMD RyzenAI Software 1.7.1

Download and install from the AMD developer portal:

```
https://ryzenai.docs.amd.com/en/latest/inst.html
```

The installer sets up the conda environment (`xdna171`) and all required DLLs automatically.

> **Note:** RyzenAI 1.7.1 is required. Earlier versions (1.6, 1.5) use different model formats and are not compatible.

### 3. SD Models (ONNX format for NPU)

You need AMD-optimized ONNX model folders. These are separate from standard HuggingFace checkpoints.

| Model | Folder name | Resolution | Steps | Tier |
|-------|-------------|------------|-------|------|
| SD 1.5 | `sd_15` | 512×512 | 20 | Lite |
| SD Turbo | `sd_turbo_bfp` | 512×512 | 1 | Lite |
| SDXL Turbo | `sdxl_turbo_bfp` | 512×512 | 1 | Full |
| Segmind Vega | `Segmind-Vega_bfp` | 1024×1024 | 20 | Full |
| SDXL Base | `sdxl-base-1.0_bfp` | 1024×1024 | 50 | Full |

Model download links and instructions are available in the official AMD RyzenAI SD guide:
```
https://ryzenai.docs.amd.com/en/latest/sd_model_zoo.html
```

---

## Installation

### Step 1 — Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/npu-benchmark-amd.git
cd npu-benchmark-amd
```

### Step 2 — Place your models

Create a `models/` folder inside the project and put each model folder inside it:

```
npu-benchmark-amd/
├── npu_sd_endurance_gradio.py
├── README.md
└── models/
    ├── sd_15/
    ├── sd_turbo_bfp/
    ├── sdxl_turbo_bfp/
    ├── Segmind-Vega_bfp/
    └── sdxl-base-1.0_bfp/
```

You don't need all 5 models. The app auto-detects which folders are present.

### Step 3 — Verify your RyzenAI install

Open a terminal and check:

```powershell
conda activate xdna171
python -c "import onnxruntime; print(onnxruntime.__version__)"
C:\Windows\System32\AMD\xrt-smi.exe examine
```

You should see your NPU listed under **Device(s) Present**, e.g.:
```
|BDF             |Name         |
|----------------|-------------|
|[00c4:00:01.1]  |NPU Krackan  |
```

---

## Running the Benchmark

### Quick start

```powershell
conda activate xdna171
set DD_ROOT=C:\Program Files\RyzenAI\1.7.1\GenAI-SD
cd C:\path\to\npu-benchmark-amd
python npu_sd_endurance_gradio.py
```

A browser window opens automatically at `http://127.0.0.1:7862`.

### If your RyzenAI is installed to a different path

```powershell
set DD_ROOT=D:\RyzenAI\1.7.1\GenAI-SD
```

### Running in the background (PowerShell)

```powershell
Start-Process python -ArgumentList "npu_sd_endurance_gradio.py" -WindowStyle Minimized
```

---

## Using the Dashboard

### Left panel — Settings

| Setting | Options | Default |
|---------|---------|---------|
| Mode | By Duration / By Rounds | By Duration |
| Duration | 10 min / 30 min / 1 hr / 2 hr / 8 hr / 12 hr / 24 hr / Custom | 1 hour |
| Rounds | 10 / 100 / 500 / 1000 / 1500 / Custom | 100 rounds |
| Tier | Lite (SD 1.5 + SD Turbo) / Full (all 5 models) | Auto-detected by RAM |
| Seed | Random / Fixed | Random |

**System Info** shows your RAM and auto-recommends a tier based on available memory:
- ≥ 28 GB → Full tier (all 5 models)
- < 28 GB → Lite tier (SD 1.5 and SD Turbo only)

**Scene Prompts** are collapsed by default. Click to expand and edit — one prompt per line, English only, max 77 tokens per line. A token counter validates your prompts in real time.

**Seed** controls the noise pattern:
- **Random** — different image every run (best for endurance/stress testing)
- **Fixed** — same noise pattern every run (best for reproducibility comparisons)

### Right panel — Live Gallery + Metrics

The gallery shows generated images in real time. The metrics sidebar updates every 2 seconds:

| Metric | Description |
|--------|-------------|
| Images | Total successful generations |
| Failed | Count of failed or timed-out runs |
| img/hr | Practical throughput (images per hour) |
| it/s | Inference speed (iterations per second, averaged across all runs) |
| CPU% | System CPU utilization (polled via psutil) |

A dark placeholder tile with a spinning circle means a generation is in progress.

### Stopping the test

Click **Stop** in the dashboard, or simply **close the browser tab** — the app detects the disconnection via heartbeat and stops automatically within ~20 seconds.

---

## Performance Report

After the test finishes (or at any point), expand the **Performance Report** section and click **Generate Report**.

Example output:

```
============================================================
  NPU SD ENDURANCE TEST - PERFORMANCE REPORT
============================================================
  Generated   : 2026-06-03  20:45:12
  Duration    : 01:00:00
  Mode        : Duration
  Status      : COMPLETE
  Total runs  : 87  (OK: 87  FAIL: 0)
  Success rate: 100.0%

  SYSTEM
  RAM                 : 31.1 GB  (avail 14.8 GB)
  Tier                : FULL

  PER-MODEL RESULTS
  ────────────────────────────────────────────────────────
  Model             N   Avg(s)    Min    Max    Std   it/s  img/hr
  SD 1.5           20    22.97  22.10  24.50   0.62  0.871   156.7
  SD Turbo         20    19.72  18.90  21.30   0.58  0.051   182.5
  SDXL Turbo       17    26.82  25.50  28.10   0.72  0.037   134.2
  Segmind Vega     17    33.46  32.00  35.20   0.84  0.598   107.6
  SDXL Base        13    93.19  91.00  96.50   1.43  0.537    38.6
  ────────────────────────────────────────────────────────

  STABILITY ANALYSIS
  ────────────────────────────────────────────────────────
  SD 1.5              : STABLE                trend +0.3%
  SD Turbo            : STABLE                trend +1.1%
  SDXL Turbo          : STABLE                trend -0.8%
  Segmind Vega        : STABLE                trend +0.5%
  SDXL Base           : STABLE                trend +1.2%

  Overall throughput : 87.3 images/hr

============================================================
  Design by Hiko
============================================================
```

The report is also auto-saved to `endurance_results/report_TIMESTAMP.txt`.

**Stability analysis** compares the first half vs the second half of each model's run times. A trend above +5% means the model is slowing down (possible thermal throttling or memory pressure).

---

## Results Reference

### What is "good" performance?

Based on testing on Ryzen AI 9 HX 370 (XDNA2, 51 TOPS):

| Model | Expected avg(s) | Expected it/s |
|-------|----------------|---------------|
| SD 1.5 | ~23 s | ~0.87 it/s |
| SD Turbo | ~20 s | N/A (1-step) |
| SDXL Turbo | ~27 s | N/A (1-step) |
| Segmind Vega | ~33 s | ~0.60 it/s |
| SDXL Base | ~93 s | ~0.54 it/s |

> Note: SD Turbo and SDXL Turbo are 1-step models. Their `it/s` values are misleadingly low — total latency is the meaningful metric.

### Understanding throughput vs latency

- **it/s** measures how fast each individual denoising step runs on the NPU
- **img/hr** measures real-world throughput including pipeline overhead (VAE encode/decode, CLIP encoding, process launch)
- For production use cases, **img/hr is what matters**

---

## Project Structure

```
npu-benchmark-amd/
├── npu_sd_endurance_gradio.py   # Main benchmark app
├── README.md
├── models/                      # Place your ONNX model folders here
│   ├── sd_15/
│   ├── sd_turbo_bfp/
│   ├── sdxl_turbo_bfp/
│   ├── Segmind-Vega_bfp/
│   └── sdxl-base-1.0_bfp/
└── endurance_results/           # Auto-created on first run
    ├── images/                  # Generated PNG files
    ├── report_*.txt             # Performance reports
    └── checkpoint_*.json        # Auto-saved checkpoints (every 30 min)
```

---

## Troubleshooting

### "No models found in models/ folder"

Check that your model folder names match exactly (case-sensitive):
```
sd_15  sd_turbo_bfp  sdxl_turbo_bfp  Segmind-Vega_bfp  sdxl-base-1.0_bfp
```

### "FAIL exit=1" in the log

Usually means `DD_ROOT` is not set. Make sure to run:
```powershell
set DD_ROOT=C:\Program Files\RyzenAI\1.7.1\GenAI-SD
```

Or set it permanently in Windows Environment Variables.

### Browser doesn't open automatically

Navigate manually to `http://127.0.0.1:7862`

### Port 7862 already in use

Edit the `PORT = 7862` constant at the top of `npu_sd_endurance_gradio.py` to any free port.

### Generation times seem slow

Check that VitisAI EP is being used. You should see `unet(NPU)` in the run log. If not, the model may be falling back to CPU/DirectML — ensure `DD_ROOT` is set correctly.

### App crashes on SDXL Base

SDXL Base requires ~8 GB RAM for model weights alone. Use Lite tier if you have less than 28 GB total RAM.

---

## Why This Exists

AMD Ryzen AI NPUs support native Stable Diffusion inference via the VitisAI execution provider. This tool was built to measure and verify that capability — tracking NPU image generation throughput, stability, and thermal behavior across extended endurance runs.

---

## License

The benchmark code (`npu_sd_endurance_gradio.py`) is released under the **MIT License**.

The AMD RyzenAI SDK, runtime DLLs, and SD model weights are subject to their own respective licenses. This repository does not include any AMD proprietary binaries.

---

## Acknowledgements

- AMD RyzenAI SDK and VitisAI EP team
- [Gradio](https://gradio.app) for the browser UI framework
- [Segmind](https://huggingface.co/segmind/Segmind-Vega) for the Vega model
- StabilityAI for SD 1.5, SD Turbo, SDXL

---

*Design by Hiko — tested on AMD Ryzen AI 9 HX 370 (XDNA2, 51 TOPS)*
