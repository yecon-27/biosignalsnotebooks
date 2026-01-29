---
title: Pilot Study 数据解析与图示说明
---

# Pilot Study 数据解析与图示说明

本报告对 pilot_study 中的 ECG（心电）与 EDA（皮电）数据进行解析，并给出关键图与可读的表格。数据源为 OpenSignals 导出文本 converted.txt（已为标准单位），采样频率 500 Hz。

## 数据来源与预处理
- 数据文件：opensignals_..._converted.txt（OpenSignals 标准格式，含头信息）
- 通道含义：
  - CH1：EDA（单位：μS）
  - CH2：ECG（单位：标准化，已转换）
- 基本处理流程：
  - 读取序列号 nSeq → 时间 t = nSeq / 500
  - ECG：R 峰检测 → RR 间期 → 瞬时心率（BPM）→ HRV 基础指标
  - EDA：SCR 峰检测 → 统计事件率与幅度等特征

## 输出目录与文件
位置：d:\biosignalsnotebooks\pilot_study\outputs

### 图像
- ECG 波形与 R 峰标注：  
  - 预览链接：[ecg_with_r_peaks.png](file:///d:/biosignalsnotebooks/pilot_study/outputs/ecg_with_r_peaks.png)
  - 展示每个心动周期的 R 峰位置，直观反映心搏节律
- 瞬时心率曲线（BPM）：  
  - 预览链接：[ecg_bpm.png](file:///d:/biosignalsnotebooks/pilot_study/outputs/ecg_bpm.png)
  - 由相邻 R 峰的 RR 间期换算得到，反映心率随时间变化
- EDA 波形与 SCR 峰标注：  
  - 预览链接：[eda_with_scr.png](file:///d:/biosignalsnotebooks/pilot_study/outputs/eda_with_scr.png)
  - 标注皮电瞬时反应（SCR）峰，有助于观察刺激或情绪反应

### 表格（CSV）
- ECG R 峰列表：[ecg_r_peaks.csv](file:///d:/biosignalsnotebooks/pilot_study/outputs/ecg_r_peaks.csv)
  - 列：
    - t_s：R 峰发生时间（秒）
    - r_amp：R 峰时的 ECG 幅值
- 心率序列（BPM）：[ecg_bpm_series.csv](file:///d:/biosignalsnotebooks/pilot_study/outputs/ecg_bpm_series.csv)
  - 列：
    - t_s：对应心率的时间（通常为后一个 R 峰时间）
    - bpm：瞬时心率（Beats Per Minute）
- HRV 指标（基础时域）：[ecg_hrv_features.csv](file:///d:/biosignalsnotebooks/pilot_study/outputs/ecg_hrv_features.csv)
  - 指标示例：
    - AvgRR_s / MinRR_s / MaxRR_s：平均/最小/最大 RR 间期（秒）
    - AvgBPM / MinBPM / MaxBPM：平均/最小/最大心率
    - SDNN_s：RR 间期标准差（时域 HRV 指标）
- EDA SCR 事件列表：[eda_scr_events.csv](file:///d:/biosignalsnotebooks/pilot_study/outputs/eda_scr_events.csv)
  - 列：
    - t_s：SCR 峰发生时间（秒）
    - amp_uS：对应峰幅值（μS，峰值-最近前谷值）
- EDA 特征汇总：[eda_features.csv](file:///d:/biosignalsnotebooks/pilot_study/outputs/eda_features.csv)
  - 指标：
    - scr_count：SCR 事件数
    - scr_rate_per_min：每分钟 SCR 事件率
    - scr_amp_mean / scr_amp_median / scr_amp_sum：幅度均值/中位/总和（μS）
    - scr_rise_time_mean：平均上升时间（秒）
- 摘要信息：[summary.json](file:///d:/biosignalsnotebooks/pilot_study/outputs/summary.json)
  - 包含采样率、R 峰数量、平均心率、SCR 数量与事件率等

## 解读建议
- ECG 与 HRV
  - ECG 图中的红点为 R 峰；密度越大，心率越高。
  - BPM 曲线可直观观察心率随时间的变化趋势；相对平稳说明心律稳定。
  - HRV 指标用于衡量心率变异性：SDNN 越大表明 RR 变化更明显；不同任务或状态会影响 HRV。
- EDA 与 SCR
  - SCR 峰代表短时皮电反应，常与刺激、情绪或认知负荷相关。
  - 事件率（每分钟）与幅度统计可以量化被试在实验过程中的反应强度与频率。
  - 注意运动伪迹和噪声可能造成假峰；解读时结合实验阶段和事件标注。

## 复现步骤
- 在仓库根目录运行：
  - `python d:\biosignalsnotebooks\pilot_study\analyze_pilot_study.py`
- 程序自动读取 converted.txt，生成上述图与 CSV 文件。

## 可选增强
- 叠加事件标注：可将 `..._EventsAnnotation.txt` 中的事件时间叠加到图上，展示刺激点或任务阶段。
- 更完整 HRV：在安装依赖后可扩展到频域（LF、HF、LF/HF）与非线性指标。
- 参数微调：可根据数据质量调整峰检测阈值（ECG/EDA 的 delta），减少伪峰。

如需把课堂的事件注释一起画到图上或想要更详细的 HRV 报告，告诉我你的具体需求与偏好，我会继续完善。 
