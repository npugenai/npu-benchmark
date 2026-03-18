<div align="center">

<svg width="800" height="120" viewBox="0 0 800 120" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#1a1625"/>
      <stop offset="100%" style="stop-color:#2d2a47"/>
    </linearGradient>
    <linearGradient id="tg" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#a18cd1"/>
      <stop offset="100%" style="stop-color:#d1c4e9"/>
    </linearGradient>
  </defs>
  <rect width="800" height="120" rx="16" fill="url(#bg)"/>
  <rect width="800" height="120" rx="16" fill="none" stroke="#a18cd1" stroke-width="1" stroke-opacity="0.3"/>
  <text x="400" y="52" font-family="Segoe UI, Arial, sans-serif" font-size="30" font-weight="800" fill="url(#tg)" text-anchor="middle">NPU Benchmark</text>
  <text x="400" y="85" font-family="Segoe UI, Arial, sans-serif" font-size="14" fill="#b0bec5" text-anchor="middle">Universal NPU Performance Testing — AMD · Intel · Qualcomm · MediaTek</text>
</svg>

<br/>

[![Website](https://img.shields.io/badge/🌐_npubenchmark.org-a18cd1?style=for-the-badge&logoColor=white)](https://www.npubenchmark.org)
[![Community](https://img.shields.io/badge/💜_npugenai.com-8a73b8?style=for-the-badge&logoColor=white)](https://www.npugenai.com)
[![License](https://img.shields.io/badge/License-Source_Available-d1c4e9?style=for-the-badge)](#license)
[![Platform](https://img.shields.io/badge/Platform-Windows_11-0078d4?style=for-the-badge&logo=windows&logoColor=white)](#)

</div>

---

## What is NPU Benchmark?

**NPU Benchmark** is the first cross-platform NPU performance testing tool that compares AMD XDNA, Intel NPU, Qualcomm Hexagon, and MediaTek APU using a unified scoring methodology — based on real AI workloads, not synthetic scores.

---

## Supported Platforms

| Vendor | Architecture | Devices | Status |
|---|---|---|---|
| **AMD** | XDNA 2 / XDNA 3 | Ryzen AI Max+ 395, Ryzen AI 9 HX 370, Ryzen AI 7 350 | ✅ Fully Supported |
| **Intel** | NPU 3 / NPU 4 | Core Ultra 9 288V, Core Ultra 7 268V, Core Ultra 7 165H | ✅ Fully Supported |
| **Qualcomm** | Hexagon NPU | Snapdragon X Elite X1E-84, X Plus X1P-64 | 🔶 Beta |
| **MediaTek** | APU 790 | Dimensity 9400, Kompanio 920 | 🔜 Coming Soon |

---

## Benchmark Suite

| Test | Workload | Precision |
|---|---|---|
| LLM Inference | Phi-3.5 Mini, LLaMA 3.2 | INT4, INT8 |
| Image Generation | Stable Diffusion XL Turbo | FP16 |
| Speech Recognition | Whisper Large v3 | INT8 |
| Document AI | Layout analysis, OCR | INT8 |

---

## Key Features

- ⚡ **Unified cross-platform score** — one number to compare any NPU
- 🧠 **Real AI workloads** — not synthetic matrix ops
- 🎯 **Multi-precision** — INT4, INT8, FP16, BF16
- 📊 **Global leaderboard** — submit and compare at [npubenchmark.org/leaderboard](https://www.npubenchmark.org/leaderboard.html)
- 🔓 **Open methodology** — fully documented, reproducible results

---

## System Requirements

| | AMD | Intel | Qualcomm |
|---|---|---|---|
| OS | Windows 11 24H2+ | Windows 11 23H2+ | Windows 11 ARM 24H2+ |
| Driver | Adrenalin 24.12+ | NPU Driver 32.0.100+ | QNN SDK 2.28+ |
| RAM | 16 GB DDR5 | 16 GB DDR5 | 16 GB LPDDR5X |
| Runtime | ONNX RT 1.19+ | OpenVINO 2024.5+ | QNN Runtime 2.28+ |

---

## Download

> 🚧 **Currently in final testing — releasing 2025 Q3**

Visit **[npubenchmark.org/download](https://www.npubenchmark.org/download.html)** to join the waitlist and get notified on launch day.

---

## Global Leaderboard

Top results from the community:

| Rank | Device | Score | TOPS |
|---|---|---|---|
| 🥇 1 | AMD Ryzen AI Max+ 395 | 1156 | 55 |
| 🥈 2 | Snapdragon X Elite X1E-84 | 1089 | 45 |
| 🥉 3 | AMD Ryzen AI 9 HX 370 | 1024 | 50 |
| 4 | Intel Core Ultra 9 288V | 987 | 48 |
| 5 | AMD Ryzen AI 7 350 | 986 | 38 |

→ Full leaderboard at [npubenchmark.org/leaderboard](https://www.npubenchmark.org/leaderboard.html)

---

## License

This project is licensed under the **NPU Benchmark Source Available License**.  
Free for personal and non-commercial use. Commercial use requires written permission.

© 2025 HIKO1999 GenAI Co., Ltd. — [hiko1999@hiko1999.com](mailto:hiko1999@hiko1999.com)

---

<div align="center">
<sub>Part of the <a href="https://www.npugenai.com">NPU GenAI Developer Community</a> · Built with 💜</sub>
</div>
