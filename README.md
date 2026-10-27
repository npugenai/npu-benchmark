<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/banner-light.svg">
  <img alt="NPU Benchmark — Stable Diffusion endurance test on AMD Ryzen AI NPU" src="assets/banner-light.svg" width="100%">
</picture>

<br/>

[![AMD Ryzen AI](https://img.shields.io/badge/AMD_Ryzen_AI-XDNA2_NPU-a18cd1?style=for-the-badge&logo=amd&logoColor=white)](https://www.amd.com/en/products/processors/consumer/ryzen-ai.html)
[![RyzenAI Software](https://img.shields.io/badge/RyzenAI_SW-1.7.1-8a73b8?style=for-the-badge)](https://ryzenai.docs.amd.com/en/latest/)
[![Windows 11](https://img.shields.io/badge/Windows-11-6f5fa8?style=for-the-badge&logo=windows11&logoColor=white)](#-requirements)
[![License: MIT](https://img.shields.io/badge/License-MIT-d1c4e9?style=for-the-badge)](LICENSE)

**English** · [简体中文](README.zh-CN.md) · [日本語](README.ja.md)

**A browser-based Stable Diffusion stress test that runs _natively on the AMD Ryzen AI NPU_ —<br/>not CPU, not GPU — and tells you how fast and how stable it stays over hours.**

</div>

<!-- Screenshot slot: drop a real screenshot of a running test at assets/dashboard.png, then remove these comment markers.
<p align="center">
  <img src="assets/dashboard.png" alt="NPU Benchmark dashboard during a run" width="92%">
</p>
-->

---

## ✨ Highlights

| | |
|---|---|
| 🧠 **Real NPU inference** | Stable Diffusion runs on the XDNA2 NPU through the VitisAI execution provider |
| 🖼️ **5 SD models** | SD 1.5 · SD Turbo · SDXL Turbo · Segmind Vega · SDXL Base |
| ⏱️ **Endurance modes** | By duration (10 min → 24 h) or by rounds (10 → 1500) |
| 📈 **Live dashboard** | Real-time image gallery + images, failures, img/hr, it/s, NPU %, CPU % |
| 🌡️ **Stability analysis** | Compares early vs. late run times per model to spot throttling or memory pressure |
| 📝 **Text report** | One click — written to `endurance_results/` as `.txt`, next to auto-saved checkpoints and a performance chart |
| 🎨 **60 scene prompts** | Landscapes, cities, fantasy, sci-fi… fully editable |

---

## 🚀 Quick Start

```powershell
# 1. Get the code
git clone https://github.com/npugenai/npu-benchmark.git
cd npu-benchmark

# 2. Activate the conda environment created by the RyzenAI installer
conda activate <your-ryzenai-env>        # e.g. ryzen-ai-1.7.1

# 3. Install the dashboard dependencies
pip install -r requirements.txt

# 4. Put your model folders into ./models  (see below), then run
python npu_sd_endurance_gradio.py
```

Your browser opens **http://127.0.0.1:7862** automatically. Pick a mode, press **▶ Start Benchmark**, and watch the NPU work.

---

## 📋 Requirements

| | |
|---|---|
| **Hardware** | AMD Ryzen AI processor with an **XDNA2** NPU · 16 GB RAM minimum (32 GB for all 5 models) |
| **OS** | Windows 11 |
| **Software** | [AMD RyzenAI Software **1.7.1**](https://ryzenai.docs.amd.com/en/latest/inst.html) (earlier versions use different model formats) |
| **Models** | AMD-optimized ONNX Stable Diffusion models — [Hugging Face collection](https://huggingface.co/collections/amd/ryzen-ai-171-sd-models) |

Check that the NPU is visible:

```powershell
C:\Windows\System32\AMD\xrt-smi.exe examine
```

```text
|BDF             |Name         |
|----------------|-------------|
|[00c4:00:01.1]  |NPU Krackan  |
```

### Models

Create a `models/` folder next to the script and put each model folder inside. You don't need all five — the app detects whatever is present.

| Model | Folder name | Resolution | Steps | Tier |
|-------|-------------|------------|------:|------|
| SD 1.5 | `sd_15` | 512×512 | 20 | Lite |
| SD Turbo | `sd_turbo_bfp` | 512×512 | 1 | Lite |
| SDXL Turbo | `sdxl_turbo_bfp` | 512×512 | 1 | Full |
| Segmind Vega | `Segmind-Vega_bfp` | 1024×1024 | 20 | Full |
| SDXL Base | `sdxl-base-1.0_bfp` | 1024×1024 | 50 | Full |

```text
npu-benchmark/
├── npu_sd_endurance_gradio.py
└── models/
    ├── sd_15/
    ├── sd_turbo_bfp/
    ├── sdxl_turbo_bfp/
    ├── Segmind-Vega_bfp/
    └── sdxl-base-1.0_bfp/
```

### RyzenAI install path

The app locates the RyzenAI SD scripts and runtime through `RYZEN_AI_INSTALLATION_PATH`, which the AMD installer sets for you, and falls back to `C:\Program Files\RyzenAI\1.7.1`. If RyzenAI lives somewhere else and that variable is missing, set it to the install root before starting the app:

```powershell
# PowerShell
$env:RYZEN_AI_INSTALLATION_PATH = "D:\RyzenAI\1.7.1"
```

```bat
:: Command Prompt (cmd.exe)
set "RYZEN_AI_INSTALLATION_PATH=D:\RyzenAI\1.7.1"
```

`DD_ROOT` is passed on to the SD scripts and defaults to `<install root>\GenAI-SD`; you normally don't need to set it.

---

## 🖥️ Using the Dashboard

| Setting | Options | Default |
|---------|---------|---------|
| Mode | By Duration / By Rounds | By Duration |
| Duration | 10 min · 30 min · 1 h · 2 h · 8 h · 12 h · 24 h · Custom | 1 hour |
| Rounds | 10 · 100 · 500 · 1000 · 1500 · Custom — total images across all models | 100 |
| Tier | Lite (SD 1.5 + SD Turbo) / Full (all 5 models) | Picked from your RAM (≥ 28 GB → Full) |
| Seed | Random — a new seed for every image (1001, 1002, …, so runs are repeatable) / Fixed — the same seed for every image | Random |

**Live metrics** (refreshed every 2 s):

| Metric | Meaning |
|--------|---------|
| Images | Successful generations |
| Failed | Failed or timed-out runs |
| img/hr | Real-world throughput, including pipeline overhead |
| it/s | Steps per second, averaged over all runs and models (see [how to read the numbers](#how-to-read-the-numbers)) |
| NPU | NPU utilization from Windows performance counters |
| CPU | System CPU utilization |

NPU and CPU readings need `C:\Windows\System32\AMD\xrt-smi.exe` (installed with the NPU driver); `—` means no reading.

> [!IMPORTANT]
> Keep the dashboard tab **visible** while a test runs. The app uses the page's 2-second refresh as a heartbeat, and browsers pause it when the tab is hidden or minimized. After about 20 seconds without it — or when you press **Stop** — the test ends as soon as the image being generated is finished.

---

## 📊 Performance Report

When a test finishes, open **Performance Report → Generate Report**. Each click also saves the report to `endurance_results/report_<timestamp>.txt`.

> [!TIP]
> Duration and throughput are measured up to the moment you click, so generate the report right after the test ends.

<details>
<summary><b>Example report</b> (illustrative numbers — click to expand)</summary>

```text
============================================================
  NPU SD ENDURANCE TEST - PERFORMANCE REPORT
============================================================
  Generated   : 2026-06-03  20:45:12
  Duration    : 01:00:32
  Mode        : Duration
  Status      : COMPLETE
  Total runs  : 94  (OK: 94  FAIL: 0)
  Success rate: 100.0%

  SYSTEM
  RAM                 : 31.1 GB  (avail 14.8 GB)
  Tier                : FULL

  PER-MODEL RESULTS
  ——————————————————————————————————————————————————————————
  Model               N  Avg(s)    Min    Max    Std    it/s  img/hr
  ——————————————————————————————————————————————————————————
  SD 1.5             19   22.96  22.18  23.77   0.56   0.872   156.8
  SD Turbo           19   19.74  18.99  20.47   0.54   0.051   182.4
  SDXL Turbo         19   26.82  25.88  27.73   0.65   0.037   134.3
  Segmind Vega       19   33.45  32.39  34.55   0.76   0.598   107.6
  SDXL Base          18   93.14  91.34  95.05   1.29   0.537    38.7
  ——————————————————————————————————————————————————————————
  OVERALL            94   38.65  18.99  95.05  26.92   0.418    93.2

  STABILITY ANALYSIS
  ——————————————————————————————————————————————————————————
  SD 1.5              : STABLE                  trend +0.9%
  SD Turbo            : STABLE                  trend -0.6%
  SDXL Turbo          : STABLE                  trend +0.8%
  Segmind Vega        : STABLE                  trend +0.8%
  SDXL Base           : STABLE                  trend -0.1%

  Overall throughput : 93.2 images/hr

============================================================
  Design by Hiko
============================================================
```

</details>

**Stability analysis** compares the average time of the first half of each model's runs with the second half (at least 4 runs per model). A trend above **+5 %** means the model is slowing down — possibly thermal throttling or memory pressure.

### How to read the numbers

- **Avg(s)** — the full time for one image: process start-up, model loading, text encoding, denoising and VAE decode.
- **img/hr** — practical throughput built from those full times. For real workloads, **img/hr is what matters**.
- **it/s** — denoising steps divided by the full per-image time (or the UNet step time, when the SD script reports one). Because start-up and loading are included, SD Turbo and SDXL Turbo — which take a single step — show a tiny it/s; compare their latency instead.

### Output files

```text
endurance_results/
├── images/               # every generated image
├── report_*.txt          # written each time you click Generate Report
├── checkpoint_*.json     # about every 30 min and when a test ends
└── chart_*.png           # performance chart, when a test ends (needs matplotlib)
```

---

## 🛠️ Troubleshooting

<details>
<summary><b>“No models found in models/ folder”</b></summary>

Folder names must be spelled exactly: `sd_15` `sd_turbo_bfp` `sdxl_turbo_bfp` `Segmind-Vega_bfp` `sdxl-base-1.0_bfp`

You will also see this message if the **Lite** tier is selected but you only have Full-tier models (SDXL Turbo, Segmind Vega, SDXL Base) — switch the tier to **Full**.
</details>

<details>
<summary><b>“FAIL exit=…” in the run log</b></summary>

- **exit=2** — the SD script was not found. Check the [RyzenAI install path](#ryzenai-install-path).
- **exit=1** — the SD script started but crashed: usually the app was started outside the RyzenAI conda environment (the SD scripts run with the same Python), or a model folder is incomplete.

The script's own error output is not shown in the run log. To see it, run the SD script for that model by hand from `<install root>\GenAI-SD\test` in the same conda environment.
</details>

<details>
<summary><b>Generation is slow</b></summary>

Watch the **NPU** reading on the dashboard while an image is generated — if it stays near zero, the model is probably running on the CPU. Check the [RyzenAI install path](#ryzenai-install-path) and that the RyzenAI conda environment is active.
</details>

<details>
<summary><b>Port 7862 is already in use / the browser didn't open</b></summary>

Open http://127.0.0.1:7862 manually, or change `PORT = 7862` near the top of `npu_sd_endurance_gradio.py`.
</details>

<details>
<summary><b>Crash on SDXL Base</b></summary>

SDXL Base needs about 8 GB of RAM for its weights alone. Use the Lite tier on machines with less than 28 GB of RAM.
</details>

---

## 🗺️ Roadmap

- [x] AMD Ryzen AI · XDNA2 · Stable Diffusion endurance test
- [ ] Intel NPU
- [ ] Qualcomm Hexagon NPU

## 🤝 Contributing

Results from different machines are the most valuable contribution. Ran a benchmark? **[Share your report](https://github.com/npugenai/npu-benchmark/issues/new?template=benchmark-result.yml)** — every new device helps the community. Bug reports and pull requests are welcome too.

## 📄 License

The benchmark code is released under the [MIT License](LICENSE). The AMD RyzenAI SDK, runtime and model weights are covered by their own licenses; this repository contains no AMD binaries.

## 🙏 Acknowledgements

[AMD RyzenAI & VitisAI EP](https://ryzenai.docs.amd.com) · [Gradio](https://gradio.app) · [Segmind](https://huggingface.co/segmind/Segmind-Vega) · [Stability AI](https://huggingface.co/stabilityai)

---

<div align="center">

**If this project helps you, please give it a ⭐ — it really helps!**

<sub>Made with 💜 by <a href="https://github.com/hiko1999GenAI">hiko1999</a> · part of <a href="https://github.com/npugenai">NPU GenAI</a></sub>

</div>
