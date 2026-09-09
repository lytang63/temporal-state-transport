# 🎬 Temporal State Transport (TST)

<div align="center">

[English](README.md) · [中文](README.zh-CN.md)

### *先诊断时间注意力，再将其传输回平衡状态。* ✨

[![Best Paper Award](https://img.shields.io/badge/Best_Paper_Award-ICML_2026_F2S-D4AF37?style=for-the-badge)](https://openreview.net/forum?id=YIqjb9fi7o)
[![Oral Presentation](https://img.shields.io/badge/Oral_Presentation-ICML_2026_F2S-2F6FEB?style=for-the-badge)](https://openreview.net/forum?id=YIqjb9fi7o)

🏆 **Best Paper Award** · 🎤 **Oral Presentation**<br>
**ICML 2026 Workshop on From Frames to Stories (F2S): Toward Reliable, Controllable and Trustworthy Long-Horizon Video Generation**

[![ICML 2026](https://img.shields.io/badge/ICML-2026-red?style=flat-square)](https://icml.cc/virtual/2026/76614)
[![Paper](https://img.shields.io/badge/Paper-OpenReview-orange?style=flat-square)](https://openreview.net/forum?id=YIqjb9fi7o)
[![arXiv](https://img.shields.io/badge/arXiv-2609.08505-b31b1b?style=flat-square)](https://arxiv.org/abs/2609.08505)
[![Code](https://img.shields.io/badge/Code-GitHub-black?style=flat-square)](https://github.com/lytang63/temporal-state-transport)
[![License](https://img.shields.io/badge/📜_License-MIT-green?style=flat-square)](LICENSE)

[**快速开始**](#-快速开始) · [**安装**](#️-安装) · [**示例**](#-tst-的两项核心能力) · [**论文**](https://openreview.net/forum?id=YIqjb9fi7o) · [**arXiv**](https://arxiv.org/abs/2609.08505)

</div>

---

## 🤔 这项工作解决什么问题？

你是否注意到，视频生成模型有时会让物体**诡异变形**、细节**逐渐糊成一团**，或者运动看起来“不太对”？这通常是因为时间注意力失去了平衡：它可能过度碎片化，也可能过度混合。

**TST** 在推理阶段直接诊断并校正这种失衡。不需要训练、不需要微调，也不需要修改模型权重；只需一次轻量干预，就能让生成视频更加连贯、细节更丰富、物理行为更可信。🎯

### 💡 核心洞见

时间不一致**并不只是因为跨帧交互不足**。时间注意力可能沿着两个相反方向失效：

- 🧩 **碎片化传输**：帧之间彼此孤立，外观和细节随时间漂移。
- 🌪️ **过度混合传输**：时间差异被抹平，导致运动不合理、物理结构崩坏。

因此，盲目增强时间注意力可能改善一种失效模式，却加重另一种模式。TST 遵循“**先诊断，再校正**”的原则：

- 🔍 **Spectral Tension** 判断时间失衡的方向与严重程度。
- 🩺 **Spectral Transport Homeostasis** 将异常的注意力状态有选择地拉回平衡区域。
- ⚡ **无需训练、即插即用**，可以在推理时增强现有视频扩散模型。
- 🎛️ **一个核心控制参数**，配合层级与时间步自适应调度，保持部署简单。

<div align="center">
<img src="assets/concept.jpg" alt="TST Method Overview" width="95%">
<br>
<em>TST 概念图：Spectral Tension 诊断与 Spectral Transport Homeostasis 校正</em>
</div>

---

## 🚀 一句话总结

我们提出两个核心思想：

- 🔍 **Spectral Tension**：判断时间注意力是否处于平衡状态的诊断信号。
- 🩺 **Spectral Transport Homeostasis**：针对异常时间状态的无需训练校正方法。

**最终效果？** 在不进行训练的情况下，提升时间一致性、细节丰富度和物理合理性。🎉

---

## ✨ TST 的两项核心能力

### 🎨 核心能力 #1：更忠实的细节与更真实的结构

TST 能够保持随时间变化仍然可信的细粒度外观与真实结构。

<div align="center">

#### 🍞 面包师揉面
*面粉、手部动作和面团纹理在整个视频中保持清晰稳定*

<img src="assets/gifs/sample-01_comparison.gif" width="90%">

---

#### 🏖️ 海滩上的女孩
*沙堡细节、玩具颜色和海浪运动保持更自然的外观*

<img src="assets/gifs/sample-06_comparison.gif" width="90%">

---

#### 🤖 机械臂组装
*电路板细节、火花与机械结构保持清晰规整*

<img src="assets/gifs/sample-09_comparison.gif" width="90%">

---

#### 🛸 太空探测器飞行
*行星环、引擎光和闪烁碎片保持稳定一致*

<img src="assets/gifs/sample-12_comparison.gif" width="90%">

---

#### 🐦 喷泉边的蓝色小鸟
*水面波纹、羽毛细节和花朵运动更加细腻*

<img src="assets/gifs/sample-13_comparison.gif" width="90%">

---

#### 🎻 小提琴演奏
*运弓动作、衣物褶皱和头发动态保持真实*

<img src="assets/gifs/sample-15_comparison.gif" width="90%">

---

#### 🏍️ 霓虹隧道中的动漫骑手
*霓虹反射、运动模糊和隧道光效更加稳定*

<img src="assets/gifs/sample-16_comparison.gif" width="90%">

</div>

<details>
<summary><b>💡 这里发生了什么？</b></summary>

没有 TST 时，时间注意力可能变得**碎片化**：每一帧过度关注自身，使细节独立漂移。TST 通过负值的 Spectral Tension 识别这种状态，并施加校正以恢复跨帧一致性。

**主要改善：**
- 🎯 更稳定的物体边界
- 🌊 更连贯的光照与水下光影
- 🎨 更一致的纹理与材质
- ✨ 更好地保留面粉、粒子和反射等细粒度细节

</details>

---

### ⚡ 核心能力 #2：更合理的物理与运动逻辑

TST 校正时间注意力，恢复连贯的物理行为与自然运动。

<div align="center">

#### 🐕 小狗接飞盘
*身体关节运动和轨迹更加自然，也更符合物理规律*

<img src="assets/gifs/sample-02_comparison.gif" width="90%">

---

#### 🐉 巨龙盘绕石桥
*龙须、鬃毛、雾气与龙身盘绕遵循更自然的运动规律*

<img src="assets/gifs/sample-07_comparison.gif" width="90%">

---

#### 🧗 冰壁攀登
*冰镐敲击、身体重心转移和雪尘运动更加真实*

<img src="assets/gifs/sample-08_comparison.gif" width="90%">

---

#### 🧪 操作全息分子的科学家
*全息图旋转、粒子轨迹和手部动作保持合理*

<img src="assets/gifs/sample-10_comparison.gif" width="90%">

---

#### 🛼 大厅滑行的女孩
*地面反射、围巾动态和人物旋转更加协调*

<img src="assets/gifs/sample-14_comparison.gif" width="90%">

---

#### ⚔️ 竹林中的动漫剑士
*剑光、雨滴、衣袖和竹林运动保持稳定一致*

<img src="assets/gifs/sample-17_comparison.gif" width="90%">

</div>

<details>
<summary><b>💡 这里发生了什么？</b></summary>

没有 TST 时，时间注意力可能变得**过度混合**：不同帧被过于激进地混在一起，产生不可能的运动。TST 通过正值的 Spectral Tension 识别这种状态，并锐化注意力以恢复运动连贯性。

**主要改善：**
- 💪 更自然的身体关节与姿态变化
- 🎯 更平滑的运动轨迹
- 💧 更真实的水、烟雾和火焰动态
- ⚖️ 更好的跨帧物理一致性

</details>

---

## 🎯 TST 为什么有效？

传统方法通常盲目增强跨帧注意力，而 TST 会先判断当前状态：

```
🔍 第一步：诊断
   ├─ 计算 Spectral Tension = H_row - H_vn（归一化）
   ├─ 负值？→ 碎片化传输（细节漂移）
   └─ 正值？→ 过度混合热点（物理失真）

🩺 第二步：校正
   ├─ 施加自适应调制：scale = 1 + τ * Q
   ├─ Q 结合时间混合比例与谱质量
   ├─ 在不同层级与扩散时间步自动调度
   └─ 保留已经处于平衡状态的注意力 ✨
```

---

## 🛠️ 安装

```bash
# 克隆仓库
git clone https://github.com/lytang63/temporal-state-transport.git
cd temporal-state-transport

# 安装依赖
pip install -r requirements.txt
```

**环境要求**：Python 3.8+、PyTorch 2.0+、CUDA GPU。

---

## 🎮 快速开始

### 方式一：Python API（只需 3 行代码！）

```python
import torch
from diffusers import WanPipeline
from tst import inject_tst_for_wan, set_tst_tau, enable_tst

# 加载视频生成 pipeline
pipe = WanPipeline.from_pretrained("path/to/Wan2.2-14B")
pipe.to("cuda")

# 🎯 注入 TST（实际上只需要 3 行！）
inject_tst_for_wan(pipe.transformer)
set_tst_tau(0.2)  # τ = 0.2 是论文推荐值
enable_tst()

# 像平常一样生成视频！
video = pipe(
    prompt="A cat walks on the grass, realistic",
    height=480,
    width=832,
    num_frames=81,
).frames[0]
```

### 方式二：命令行

```bash
python inference.py \
    --model-dir path/to/Wan2.2-14B \
    --prompt "A cat walks on the grass, realistic" \
    --tst-tau 0.2 \
    --output output.mp4
```

**就是这么简单！** 🎉

---

## 🎛️ 你只需要调一个超参数

TST 只有一个主要控制参数：`tau`（τ）。

<div align="center">

| τ 数值 | 效果 | 适用场景 |
|:-------:|:-------|:------------|
| **0.1** | 🔸 轻微校正 | 基线视频已经不错，只需要润色 |
| **0.2** | ✅ **推荐** | 大多数场景（论文设置） |
| **0.3** | 🔥 强校正 | 时间注意力失真较严重 |
| **0.0** | ❌ 关闭 | 基线对照 |

</div>

```python
set_tst_tau(0.2)  # 建议从这里开始，再按需调整！
```

**小建议**：针对不同 prompt 尝试不同的 τ。更大的数值会带来更强的校正，但如果基线本身已经很好，也可能引入伪影。

---

## 🧪 工作原理（简要数学说明）

对于每一个时间自注意力层：

**1. 计算注意力统计量：**
```python
row_entropy = -Σ A·log(A)        # 局部弥散度
vn_entropy = -Σ λ·log(λ)         # 谱多样性（特征值）
```

**2. 计算质量因子：**
```python
temporal_alpha = 1 - diag(A)     # 跨帧混合比例
spectral_q = H_vn * (1 - H_vn)   # 抛物线质量因子（平衡状态附近最高）
Q = temporal_alpha * spectral_q   # 综合质量
```

**3. 施加自适应调制：**
```python
scale = 1 + τ_effective * Q      # ← 核心操作！✨
output = output * scale
```

调制是**自适应**的：注意力越失衡，校正越明显；状态越健康，干预越弱。不同层级与时间步的调度会自动完成。🎯

<details>
<summary><b>想了解更多细节？📚</b></summary>

- **层级调度**：中间 Transformer 层会获得更强的调制（余弦调度：`0.5 - 0.5*cos(π*l/L)`）。
- **时间步调度**：扩散早期时间步会获得更强的调制（余弦调度：`0.5 + 0.5*cos(π*t/T)`）。
- **谱分析**：Von Neumann entropy 捕捉注意力 Gram 矩阵 `A·A^T` 的特征值分布。
- **稳态校正**：抛物线质量因子 `H*(1-H)` 在 `H=0.5` 附近达到峰值，为中等平衡状态提供最大校正。

完整数学推导与消融实验请参阅论文。

</details>

---

## 📊 模型支持

目前已经测试并支持：

<div align="center">

| 模型 | 规模 | 分辨率 | 状态 |
|:------|:----:|:-----------|:------:|
| **Wan2.2** | 5B | 480p、720p | ✅ |
| **Wan2.2** | 14B | 480p、720p | ✅ |
| CogVideoX | - | - | 🔜 即将支持 |
| HunyuanVideo | - | - | 🔜 即将支持 |

</div>

---

## 🎨 项目结构

```
TST/
├── 🎯 tst/                    # 核心模块
│   ├── __init__.py           # 模块导出
│   ├── core.py               # TST 算法实现
│   ├── globals.py            # 配置与状态
│   ├── instrumentation.py    # 调度用调用跟踪
│   └── models/
│       └── wan.py            # Wan2.2 集成
├── 🚀 inference.py            # 命令行接口
├── 📖 example.py              # 快速开始示例
├── 📋 requirements.txt        # 依赖
├── 📚 README.md               # 英文说明
├── 📚 README.zh-CN.md         # 中文说明
├── 🎥 assets/gifs/            # 13 个对比 GIF
└── 🧪 test_tst.py             # 测试脚本
```

---

## 📈 性能

TST 只带来极小的额外开销：

<div align="center">

| 指标 | 基线 | 使用 TST | 提升 |
|:-------|:--------:|:--------:|:-----------:|
| 时间一致性 | 0.82 | 0.91 | **+11%** ⬆️ |
| 物理合理性 | 0.75 | 0.88 | **+17%** ⬆️ |
| 细节保留 | 0.79 | 0.89 | **+13%** ⬆️ |
| 推理时间 | 33s | 34s | -3% ⬇️ |

</div>

*结果基于 Wan2.2-5B、20 个采样步、81 帧、480p 分辨率。*

---

## 🤝 引用

如果 TST 对你的研究或项目有所帮助，欢迎引用：

```bibtex
@misc{tang2026temporalstatetransportvideo,
  title={Temporal State Transport in Video Generation: Diagnosing and Correcting Spectral Imbalance},
  author={Luyao Tang and Bingjun Luo and Dong Yi and Jialin Guo and Haoning Xi and Cheng Chen and Yizhou Yu and Chaoqi Chen},
  year={2026},
  eprint={2609.08505},
  archivePrefix={arXiv},
  primaryClass={cs.CV},
  url={https://arxiv.org/abs/2609.08505},
}
```

---

## 📜 许可证

本项目基于 [MIT License](LICENSE) 发布。

---

## 🙏 致谢

本项目基于以下开源工作构建：

- 🤗 Hugging Face 的 [Diffusers](https://github.com/huggingface/diffusers)
- 🎬 腾讯 [Wan2.2](https://github.com/TencentQQGYLab/Wan) 视频生成模型
- 特别感谢开源社区！💙

---

## 💬 问题与支持

<div align="center">

| 我想要…… | 去哪里？ |
|:-------------|:------------|
| 🐛 报告问题 | [提交 Issue](https://github.com/lytang63/temporal-state-transport/issues) |
| 💡 建议功能 | [发起 Discussion](https://github.com/lytang63/temporal-state-transport/discussions) |
| 🎥 查看更多示例 | [浏览对比视频](#-tst-的两项核心能力) |
| 📚 阅读论文 | [OpenReview](https://openreview.net/forum?id=YIqjb9fi7o) · [arXiv](https://arxiv.org/abs/2609.08505) |
| 💬 与我们交流 | [Discussions](https://github.com/lytang63/temporal-state-transport/discussions) |

</div>

---

<div align="center">

### Made with ❤️ by the TST team

**如果觉得项目有帮助，欢迎给仓库点一个 ⭐！**

</div>
