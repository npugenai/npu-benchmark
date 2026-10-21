<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/banner-light.svg">
  <img alt="NPU Benchmark —— 在 AMD Ryzen AI NPU 上运行的 Stable Diffusion 耐久测试" src="assets/banner-light.svg" width="100%">
</picture>

<br/>

[![AMD Ryzen AI](https://img.shields.io/badge/AMD_Ryzen_AI-XDNA2_NPU-a18cd1?style=for-the-badge&logo=amd&logoColor=white)](https://www.amd.com/en/products/processors/consumer/ryzen-ai.html)
[![RyzenAI Software](https://img.shields.io/badge/RyzenAI_SW-1.7.1-8a73b8?style=for-the-badge)](https://ryzenai.docs.amd.com/en/latest/)
[![Windows 11](https://img.shields.io/badge/Windows-11-6f5fa8?style=for-the-badge&logo=windows11&logoColor=white)](#-环境要求)
[![License: MIT](https://img.shields.io/badge/License-MIT-d1c4e9?style=for-the-badge)](LICENSE)

[English](README.md) · **简体中文** · [日本語](README.ja.md)

**一款基于浏览器的 Stable Diffusion 压力测试工具，_原生运行在 AMD Ryzen AI NPU 上_——<br/>不是 CPU，也不是 GPU——并告诉你它在连续数小时的运行中能跑多快、有多稳。**

</div>

<!-- 截图占位：把测试运行时的真实截图放到 assets/dashboard.png，然后删除这些注释标记。
<p align="center">
  <img src="assets/dashboard.png" alt="运行中的 NPU Benchmark 仪表盘" width="92%">
</p>
-->

---

## ✨ 功能亮点

| | |
|---|---|
| 🧠 **真正的 NPU 推理** | Stable Diffusion 通过 VitisAI 执行提供程序（Execution Provider）运行在 XDNA2 NPU 上 |
| 🖼️ **5 个 SD 模型** | SD 1.5 · SD Turbo · SDXL Turbo · Segmind Vega · SDXL Base |
| ⏱️ **耐久测试模式** | 按时长（10 分钟 → 24 小时）或按轮数（10 → 1500 轮） |
| 📈 **实时仪表盘** | 实时图片墙 + 图片数、失败数、img/hr、it/s、NPU %、CPU % |
| 🌡️ **稳定性分析** | 按模型对比前期与后期的运行耗时，帮你发现降频或内存压力问题 |
| 📝 **文本报告** | 一键生成——自动保存为 `.txt` 文件 |
| 🎨 **60 个场景提示词** | 风景、城市、奇幻、科幻……全部可自由编辑 |

---

## 🚀 快速开始

```powershell
# 1. 获取代码
git clone https://github.com/npugenai/npu-benchmark.git
cd npu-benchmark

# 2. 激活 RyzenAI 安装程序创建的 conda 环境
conda activate <your-ryzenai-env>        # 例如 ryzen-ai-1.7.1

# 3. 安装仪表盘所需的依赖
pip install -r requirements.txt

# 4. 把模型文件夹放进 ./models（见下文），然后运行
python npu_sd_endurance_gradio.py
```

浏览器会自动打开 **http://127.0.0.1:7862** 页面。选择一种模式，点击 **▶ Start Benchmark**（开始测试），然后就可以看着 NPU 干活了。

---

## 📋 环境要求

| | |
|---|---|
| **硬件** | 搭载 **XDNA2** NPU 的 AMD Ryzen AI 处理器 · 内存至少 16 GB（运行全部 5 个模型需要 32 GB） |
| **操作系统** | Windows 11 |
| **软件** | [AMD RyzenAI Software **1.7.1**](https://ryzenai.docs.amd.com/en/latest/inst.html)（更早的版本使用不同的模型格式） |
| **模型** | 经 AMD 优化的 ONNX Stable Diffusion 模型——[Hugging Face 合集](https://huggingface.co/collections/amd/ryzen-ai-171-sd-models) |

确认系统能识别到 NPU：

```powershell
C:\Windows\System32\AMD\xrt-smi.exe examine
```

```text
|BDF             |Name         |
|----------------|-------------|
|[00c4:00:01.1]  |NPU Krackan  |
```

### 模型

在脚本所在目录下新建一个 `models/` 文件夹，把各个模型文件夹放进去。不必五个都准备齐全——程序会自动检测现有的模型。

| 模型 | 文件夹名 | 分辨率 | 步数 | 档位 |
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

### RyzenAI 安装路径

程序会通过 `RYZEN_AI_INSTALLATION_PATH`（由 AMD 安装程序设置）查找 RyzenAI，找不到时回退到 `C:\Program Files\RyzenAI\1.7.1`。如果你的 RyzenAI 装在其他位置，请把 `DD_ROOT` 指向 `GenAI-SD` 文件夹：

```powershell
# PowerShell
$env:DD_ROOT = "D:\RyzenAI\1.7.1\GenAI-SD"
```

```bat
:: 命令提示符 (cmd.exe)
set "DD_ROOT=D:\RyzenAI\1.7.1\GenAI-SD"
```

---

## 🖥️ 使用仪表盘

| 设置项 | 选项 | 默认值 |
|---------|---------|---------|
| Mode（模式） | By Duration（按时长）/ By Rounds（按轮数） | By Duration |
| Duration（时长） | 10 min · 30 min · 1 h · 2 h · 8 h · 12 h · 24 h · Custom（自定义） | 1 hour |
| Rounds（轮数） | 10 · 100 · 500 · 1000 · 1500 · Custom（自定义） | 100 |
| Tier（档位） | Lite（SD 1.5 + SD Turbo）/ Full（全部 5 个模型） | 根据内存容量自动选择（≥ 28 GB → Full） |
| Seed（种子） | Random（用于压力测试）/ Fixed（用于可复现的对比测试） | Random |

**实时指标**（每 2 秒刷新一次）：

| 指标 | 含义 |
|--------|---------|
| Images | 成功生成的图片数 |
| Failed | 失败或超时的运行次数 |
| img/hr | 实际吞吐量，包含流水线开销 |
| it/s | 去噪速度，取各次运行的平均值 |
| NPU | NPU 占用率，数据来自 Windows 性能计数器 |
| CPU | 系统 CPU 占用率 |

> [!IMPORTANT]
> 测试运行期间，请保持仪表盘所在的标签页处于**可见**状态。程序把页面每 2 秒一次的刷新当作心跳信号，而当标签页被隐藏或最小化时，浏览器会暂停这一刷新——心跳中断约 20 秒后，测试就会停止。点击 **Stop** 或关闭标签页同样会结束测试。

---

## 📊 性能报告

任何时候都可以打开 **Performance Report → Generate Report**（性能报告 → 生成报告）。报告同时也会保存到 `endurance_results/report_<timestamp>.txt`。

<details>
<summary><b>报告示例</b>（点击展开）</summary>

```text
============================================================
  NPU SD ENDURANCE TEST - PERFORMANCE REPORT
============================================================
  Generated   : 2026-06-03  20:45:12
  Duration    : 01:00:00
  Mode        : Duration
  Status      : COMPLETE
  Total runs  : 87  (OK: 87  FAIL: 0)
  Success rate: 100.0%

  PER-MODEL RESULTS
  ────────────────────────────────────────────────────────
  Model             N   Avg(s)    Min    Max    Std   it/s  img/hr
  SD 1.5           20    22.97  22.10  24.50   0.62  0.871   156.7
  SD Turbo         20    19.72  18.90  21.30   0.58  0.051   182.5
  SDXL Turbo       17    26.82  25.50  28.10   0.72  0.037   134.2
  Segmind Vega     17    33.46  32.00  35.20   0.84  0.598   107.6
  SDXL Base        13    93.19  91.00  96.50   1.43  0.537    38.6

  STABILITY ANALYSIS
  ────────────────────────────────────────────────────────
  SD 1.5              : STABLE                trend +0.3%
  SD Turbo            : STABLE                trend +1.1%
  SDXL Turbo          : STABLE                trend -0.8%
  Segmind Vega        : STABLE                trend +0.5%
  SDXL Base           : STABLE                trend +1.2%

  Overall throughput : 87.3 images/hr
============================================================
```

</details>

**稳定性分析**会把每个模型前半段运行的平均耗时与后半段进行对比。如果趋势值（trend）超过 **+5 %**，说明该模型正在变慢——可能是过热降频或内存压力所致。

### 如何解读这些数据

- **it/s**——每个去噪步骤在 NPU 上的运行速度。
- **img/hr**——实际吞吐量，包含 CLIP 文本编码、VAE 解码以及进程启动的耗时。对于真实的工作负载，**真正重要的是 img/hr**。
- SD Turbo 和 SDXL Turbo 只需一步，所以它们的 it/s 看起来非常小——这时应该看总延迟。

---

## 🛠️ 故障排查

<details>
<summary><b>“No models found in models/ folder”</b></summary>

文件夹名称必须完全一致（区分大小写）：`sd_15` `sd_turbo_bfp` `sdxl_turbo_bfp` `Segmind-Vega_bfp` `sdxl-base-1.0_bfp`
</details>

<details>
<summary><b>运行日志中出现 “FAIL exit=1”</b></summary>

说明找不到或无法启动 SD 脚本。请确认：已安装 RyzenAI 1.7.1；已激活 RyzenAI 的 conda 环境；如果使用的是非默认安装路径，`DD_ROOT` 已指向 `GenAI-SD` 文件夹（参见 [RyzenAI 安装路径](#ryzenai-安装路径)）。
</details>

<details>
<summary><b>生成速度很慢</b></summary>

检查是否启用了 VitisAI EP：运行日志中应显示 `unet(NPU)`。如果没有，模型可能回退到了 CPU 上运行——请检查上文的安装路径。
</details>

<details>
<summary><b>端口 7862 已被占用 / 浏览器没有打开</b></summary>

手动打开 http://127.0.0.1:7862 即可；或者修改 `npu_sd_endurance_gradio.py` 开头附近的 `PORT = 7862`。
</details>

<details>
<summary><b>运行 SDXL Base 时崩溃</b></summary>

仅 SDXL Base 的权重就需要大约 8 GB 内存。内存小于 28 GB 的机器请使用 Lite 档位。
</details>

---

## 🗺️ 路线图

- [x] AMD Ryzen AI · XDNA2 · Stable Diffusion 耐久测试
- [ ] Intel NPU
- [ ] Qualcomm Hexagon NPU

## 🤝 参与贡献

来自不同机器的测试结果是最有价值的贡献。跑过基准测试了吗？快来 **[分享你的报告](https://github.com/npugenai/npu-benchmark/issues/new?template=benchmark-result.yml)** 吧——每多一台新设备，都是对社区的帮助。同样欢迎提交 Bug 报告和 Pull Request。

## 📄 许可证

本基准测试代码基于 [MIT 许可证](LICENSE) 发布。AMD RyzenAI SDK、运行时以及模型权重均受其各自的许可证约束；本仓库不包含任何 AMD 二进制文件。

## 🙏 致谢

[AMD RyzenAI & VitisAI EP](https://ryzenai.docs.amd.com) · [Gradio](https://gradio.app) · [Segmind](https://huggingface.co/segmind/Segmind-Vega) · [Stability AI](https://huggingface.co/stabilityai)

---

<div align="center">

**如果这个项目对你有帮助，请点个 ⭐ 支持一下——这真的很有帮助！**

<sub>由 <a href="https://github.com/hiko1999GenAI">hiko1999</a> 用 💜 打造 · <a href="https://github.com/npugenai">NPU GenAI</a> 项目的一部分</sub>

</div>
