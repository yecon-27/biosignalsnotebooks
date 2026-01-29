import sys
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def find_converted_file(base_dir: Path) -> Path:
    candidates = list(base_dir.glob("*converted.txt"))
    if not candidates:
        raise FileNotFoundError("未找到 *converted.txt 文件")
    return sorted(candidates)[-1]


def load_opensignals_txt(fp: Path):
    with fp.open("r", encoding="utf-8") as f:
        line1 = f.readline().strip()
        line2 = f.readline().strip()
        header = None
        try:
            if line2.startswith("#"):
                header = json.loads(line2[1:].strip())
        except Exception:
            header = None
    df = pd.read_csv(
        fp,
        sep=r"\s+",
        comment="#",
        header=None,
        names=["nSeq", "DI", "CH1", "CH2"],
        engine="python",
    )
    fs = None
    ch_map = {"CH1": "EDA", "CH2": "ECG"}
    if isinstance(header, dict):
        try:
            mac = list(header.keys())[0]
            fs = int(header[mac]["sampling rate"])
            sensors = header[mac].get("sensor", [])
            labels = header[mac].get("label", [])
            columns = header[mac].get("column", [])
            if sensors and labels and columns:
                # Map columns to sensor names when available
                ch_map = {labels[i]: sensors[i] for i in range(len(labels))}
        except Exception:
            pass
    return df, fs, ch_map


def detect_ecg_r_peaks(ecg: np.ndarray, fs: int):
    # 直接加载 vendored peakdelta 模块进行峰检测
    import importlib.util
    mod_path = Path(__file__).resolve().parents[1] / "biosignalsnotebooks" / "biosignalsnotebooks" / "external_packages" / "novainstrumentation" / "peakdelta.py"
    spec = importlib.util.spec_from_file_location("peakdelta", str(mod_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    ecg_std = float(np.std(ecg))
    delta = max(0.02, 1.5 * ecg_std)
    maxtab, _ = mod.peakdelta(ecg.astype(float), delta)
    r_idx = np.array([i for i, v in maxtab], dtype=int)
    r_amp = ecg[r_idx] if len(r_idx) else np.array([], dtype=float)
    return r_idx, r_amp


def compute_hrv(ecg: np.ndarray, fs: int):
    r_idx, _ = detect_ecg_r_peaks(ecg, fs)
    if len(r_idx) < 2:
        return {}
    rr = np.diff(r_idx) / fs
    bpm = 60.0 / rr
    return {
        "AvgRR_s": float(np.mean(rr)),
        "MinRR_s": float(np.min(rr)),
        "MaxRR_s": float(np.max(rr)),
        "AvgBPM": float(np.mean(bpm)),
        "MinBPM": float(np.min(bpm)),
        "MaxBPM": float(np.max(bpm)),
        "SDNN_s": float(np.std(rr)),
    }


def detect_eda_scr(eda: np.ndarray, fs: int):
    import importlib.util
    mod_path = Path(__file__).resolve().parents[1] / "biosignalsnotebooks" / "biosignalsnotebooks" / "external_packages" / "novainstrumentation" / "peakdelta.py"
    spec = importlib.util.spec_from_file_location("peakdelta", str(mod_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    x = eda.astype(float)
    mad = np.median(np.abs(x - np.median(x)))
    delta = max(0.02, 3.0 * mad)
    maxtab, mintab = mod.peakdelta(x, delta)
    peaks_all = np.array([i for i, v in maxtab], dtype=int)
    valleys_all = np.array([i for i, v in mintab], dtype=int)
    # 计算SCR事件幅度（峰-最近前谷），并保持索引对齐
    aligned_peaks = []
    amplitudes = []
    rise_time = []
    valley_idx = 0
    for p in peaks_all:
        while valley_idx + 1 < len(valleys_all) and valleys_all[valley_idx + 1] < p:
            valley_idx += 1
        if valley_idx < len(valleys_all) and valleys_all[valley_idx] < p:
            v = valleys_all[valley_idx]
            amp = x[p] - x[v]
            if amp > 0:
                aligned_peaks.append(p)
                amplitudes.append(amp)
                rise_time.append((p - v) / fs)
    aligned_peaks = np.array(aligned_peaks, dtype=int)
    amplitudes = np.array(amplitudes, dtype=float)
    rise_time = np.array(rise_time, dtype=float)
    features = {
        "scr_count": int(len(aligned_peaks)),
        "scr_rate_per_min": float(len(amplitudes) / (len(x) / fs) * 60.0),
        "scr_amp_mean": float(np.mean(amplitudes)) if len(amplitudes) else 0.0,
        "scr_amp_median": float(np.median(amplitudes)) if len(amplitudes) else 0.0,
        "scr_amp_sum": float(np.sum(amplitudes)) if len(amplitudes) else 0.0,
        "scr_rise_time_mean": float(np.mean(rise_time)) if len(rise_time) else 0.0,
    }
    return aligned_peaks, amplitudes, features


def plot_ecg_with_r_peaks(t: np.ndarray, ecg: np.ndarray, r_idx: np.ndarray, out: Path):
    plt.figure(figsize=(12, 4))
    plt.plot(t, ecg, lw=0.8, color="steelblue")
    if len(r_idx):
        plt.scatter(t[r_idx], ecg[r_idx], color="crimson", s=12)
    plt.xlabel("Time (s)")
    plt.ylabel("ECG")
    plt.title("ECG with R-peaks")
    plt.tight_layout()
    plt.savefig(str(out), dpi=150)
    plt.close()


def plot_hr(t_rr: np.ndarray, bpm: np.ndarray, out: Path):
    plt.figure(figsize=(12, 3.5))
    plt.plot(t_rr, bpm, color="darkgreen", lw=1.0)
    plt.xlabel("Time (s)")
    plt.ylabel("BPM")
    plt.title("Instantaneous Heart Rate")
    plt.tight_layout()
    plt.savefig(str(out), dpi=150)
    plt.close()


def plot_eda_with_scr(t: np.ndarray, eda: np.ndarray, scr_idx: np.ndarray, out: Path):
    plt.figure(figsize=(12, 4))
    plt.plot(t, eda, lw=0.8, color="orange")
    if len(scr_idx):
        plt.scatter(t[scr_idx], eda[scr_idx], color="purple", s=12)
    plt.xlabel("Time (s)")
    plt.ylabel("EDA (μS)")
    plt.title("EDA with SCR peaks")
    plt.tight_layout()
    plt.savefig(str(out), dpi=150)
    plt.close()


def main():
    base_dir = Path(__file__).resolve().parent
    out_dir = base_dir / "outputs"
    out_dir.mkdir(exist_ok=True)

    fp = find_converted_file(base_dir)
    df, fs, ch_map = load_opensignals_txt(fp)
    if fs is None:
        fs = 500
    t = df["nSeq"].to_numpy() / fs
    eda = df["CH1"].to_numpy().astype(float)
    ecg = df["CH2"].to_numpy().astype(float)

    r_idx, r_amp = detect_ecg_r_peaks(ecg, fs)
    # RR与BPM
    bpm_t = np.array([], dtype=float)
    bpm_v = np.array([], dtype=float)
    if len(r_idx) >= 2:
        rr = np.diff(r_idx) / fs
        bpm_v = 60.0 / rr
        bpm_t = t[r_idx[1:]]

    hrv = compute_hrv(ecg, fs)

    scr_idx, scr_amp, eda_feat = detect_eda_scr(eda, fs)

    # 保存结果CSV
    pd.DataFrame({"t_s": t[r_idx], "r_amp": r_amp}).to_csv(out_dir / "ecg_r_peaks.csv", index=False)
    pd.DataFrame({"t_s": bpm_t, "bpm": bpm_v}).to_csv(out_dir / "ecg_bpm_series.csv", index=False)
    pd.DataFrame([hrv]).to_csv(out_dir / "ecg_hrv_features.csv", index=False)
    pd.DataFrame({"t_s": t[scr_idx], "amp_uS": scr_amp}).to_csv(out_dir / "eda_scr_events.csv", index=False)
    pd.DataFrame([eda_feat]).to_csv(out_dir / "eda_features.csv", index=False)

    # 绘图
    plot_ecg_with_r_peaks(t, ecg, r_idx, out_dir / "ecg_with_r_peaks.png")
    print(str(out_dir / "ecg_with_r_peaks.png"))
    if len(bpm_t):
        plot_hr(bpm_t, bpm_v, out_dir / "ecg_bpm.png")
        print(str(out_dir / "ecg_bpm.png"))
    plot_eda_with_scr(t, eda, scr_idx, out_dir / "eda_with_scr.png")
    print(str(out_dir / "eda_with_scr.png"))

    summary = {
        "fs": fs,
        "ecg_r_peaks_count": int(len(r_idx)),
        "ecg_bpm_avg": float(np.mean(bpm_v)) if len(bpm_v) else None,
        "eda_scr_count": int(eda_feat.get("scr_count", 0)),
        "eda_scr_rate_per_min": float(eda_feat.get("scr_rate_per_min", 0.0)),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print("分析完成")
    print(f"输出目录: {out_dir}")


if __name__ == "__main__":
    main()
