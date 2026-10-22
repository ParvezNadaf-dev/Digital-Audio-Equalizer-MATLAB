"""
Digital Audio Equalizer — 3-band DSP dashboard (Streamlit)
Run:  streamlit run app.py
"""
import io

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from scipy.io import wavfile
from scipy.signal import butter, filtfilt, freqz, welch

st.set_page_config(page_title="Digital Audio Equalizer", page_icon="🎚️", layout="wide")

# Report Table 5.2 reference values
REPORT_REF = {
    "Input RMS": 0.298721, "Output RMS": 0.416026,
    "Input peak": 0.850000, "Output peak": 1.000000,
    "Input crest factor": 2.845462, "Output crest factor": 2.403697,
}
DEFAULTS = {"bass": 6.0, "mid": 0.0, "treble": -3.0, "fc_low": 250, "fc_high": 4000, "order": 4}
COLORS = {"input": "#9aa0a6", "output": "#d97757", "bass": "#4c78a8", "mid": "#54a24b", "treble": "#b279a2"}


# ---------------------------------------------------------------- signal
@st.cache_data
def synthetic_signal(fs=44100, duration=5.0, seed=7):
    """5 s test signal: 100 Hz + 1 kHz + 8 kHz tones, slow envelope, light noise, peak 0.85."""
    t = np.arange(int(fs * duration)) / fs
    rng = np.random.default_rng(seed)
    env = 0.8 + 0.2 * np.sin(2 * np.pi * 0.5 * t)
    x = env * (0.30 * np.sin(2 * np.pi * 100 * t)
               + 0.30 * np.sin(2 * np.pi * 1000 * t)
               + 0.25 * np.sin(2 * np.pi * 8000 * t)) + 0.01 * rng.standard_normal(t.size)
    return fs, x / np.max(np.abs(x)) * 0.85


def load_wav(file_bytes):
    """Read a WAV, convert to mono float in [-1, 1] and normalize to peak 0.85."""
    fs, data = wavfile.read(io.BytesIO(file_bytes))
    if np.issubdtype(data.dtype, np.integer):
        data = data.astype(np.float64) / np.iinfo(data.dtype).max
    data = data.astype(np.float64)
    if data.ndim > 1:  # stereo -> mono
        data = data.mean(axis=1)
    peak = np.max(np.abs(data))
    return fs, (data / peak * 0.85) if peak > 0 else data


# ---------------------------------------------------------------- DSP
@st.cache_data
def split_bands(x, fs, fc_low, fc_high, order):
    bl, al = butter(order, fc_low / (fs / 2), btype="low")
    bh, ah = butter(order, fc_high / (fs / 2), btype="high")
    bass = filtfilt(bl, al, x)
    treble = filtfilt(bh, ah, x)
    mid = x - bass - treble  # residual
    return bass, mid, treble, (bl, al), (bh, ah)


def db2lin(db):
    return 10 ** (db / 20)


def rms(s):
    return float(np.sqrt(np.mean(s ** 2)))


def log_axis(fig, title="Frequency (Hz)"):
    fig.update_xaxes(type="log", range=[np.log10(20), np.log10(20000)], title=title,
                     tickvals=[20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000],
                     ticktext=["20", "50", "100", "200", "500", "1k", "2k", "5k", "10k", "20k"])


def cutoff_lines(fig, fc_low, fc_high):
    for f in (fc_low, fc_high):
        fig.add_vline(x=f, line_dash="dash", line_color="gray", opacity=0.6)


def style(fig, h=340):
    fig.update_layout(height=h, margin=dict(l=10, r=10, t=10, b=10), hovermode="x unified",
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0))
    return fig


# ---------------------------------------------------------------- sidebar
st.sidebar.title("🎚️ Equalizer controls")
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)
if st.sidebar.button("Reset to report setting"):
    for k, v in DEFAULTS.items():
        st.session_state[k] = v

g_bass = st.sidebar.slider("Bass gain (dB)", -12.0, 12.0, step=0.5, key="bass")
g_mid = st.sidebar.slider("Mid gain (dB)", -12.0, 12.0, step=0.5, key="mid")
g_treble = st.sidebar.slider("Treble gain (dB)", -12.0, 12.0, step=0.5, key="treble")

with st.sidebar.expander("Filter design"):
    fc_low = st.number_input("Bass cutoff, low-pass (Hz)", 50, 1000, step=10, key="fc_low")
    fc_high = st.number_input("Treble cutoff, high-pass (Hz)", 1000, 15000, step=100, key="fc_high")
    order = st.slider("Butterworth order", 1, 8, key="order")
    normalize = st.checkbox("Normalize output to avoid clipping", value=True)

with st.sidebar.expander("Input signal"):
    upload = st.file_uploader("Use your own WAV (optional)", type=["wav"])

if fc_low >= fc_high:
    st.error("Bass cutoff must be lower than treble cutoff.")
    st.stop()

# ---------------------------------------------------------------- compute
if upload is not None:
    fs, x = load_wav(upload.getvalue())
    src = f"Uploaded file: {upload.name}"
else:
    fs, x = synthetic_signal()
    src = "Synthetic test signal (100 Hz + 1 kHz + 8 kHz)"
if fc_high >= fs / 2:
    st.error(f"Treble cutoff must be below Nyquist ({fs/2:.0f} Hz).")
    st.stop()

bass, mid, treble, (bl, al), (bh, ah) = split_bands(x, fs, fc_low, fc_high, order)
G = {"bass": db2lin(g_bass), "mid": db2lin(g_mid), "treble": db2lin(g_treble)}
y_raw = G["bass"] * bass + G["mid"] * mid + G["treble"] * treble
raw_peak = float(np.max(np.abs(y_raw)))
y = y_raw / raw_peak if (normalize and raw_peak > 1) else y_raw

# Effective (filtfilt => squared) responses and overall EQ curve
f_axis = np.logspace(np.log10(20), np.log10(min(20000, fs / 2 * 0.999)), 600)
_, hl = freqz(bl, al, worN=f_axis, fs=fs)
_, hh = freqz(bh, ah, worN=f_axis, fs=fs)
L, Hh = np.abs(hl) ** 2, np.abs(hh) ** 2
M = 1 - L - Hh
H_eq = G["bass"] * L + G["mid"] * M + G["treble"] * Hh

# ---------------------------------------------------------------- header
st.title("Digital audio equalizer — 3-band DSP dashboard")
st.caption(f"{src} · fs = {fs:,} Hz · {x.size/fs:.2f} s · {x.size:,} samples · "
           f"{order}th-order Butterworth, filtfilt (zero phase)")

tone_freqs = {"100 Hz (bass)": 100.0, "1 kHz (mid)": 1000.0, "8 kHz (treble)": 8000.0}
_, tl = freqz(bl, al, worN=list(tone_freqs.values()), fs=fs)
_, th = freqz(bh, ah, worN=list(tone_freqs.values()), fs=fs)
tone_db = 20 * np.log10(np.maximum(1e-12, G["bass"] * np.abs(tl) ** 2
                                   + G["mid"] * (1 - np.abs(tl) ** 2 - np.abs(th) ** 2)
                                   + G["treble"] * np.abs(th) ** 2))

c = st.columns(5)
for col, (name, d) in zip(c[:3], zip(tone_freqs, tone_db)):
    col.metric(f"{name} level change", f"{d:+.2f} dB")
c[3].metric("Output RMS", f"{rms(y):.4f}", f"{20*np.log10(rms(y)/rms(x)):+.2f} dB vs input")
c[4].metric("Peak before normalization", f"{raw_peak:.3f}",
            "would clip" if raw_peak > 1 else "within ±1",
            delta_color="inverse" if raw_peak > 1 else "normal")

# ---------------------------------------------------------------- audio
a1, a2, a3 = st.columns([1, 1, 1])
a1.markdown("**Input**")
a1.audio(x.astype(np.float32), sample_rate=fs)
a2.markdown("**Equalized output**")
a2.audio(y.astype(np.float32), sample_rate=fs)
buf = io.BytesIO()
wavfile.write(buf, fs, (np.clip(y, -1, 1) * 32767).astype(np.int16))
a3.markdown("**Save**")
a3.download_button("Download equalized WAV", buf.getvalue(), "equalized_output.wav", "audio/wav")

tab_f, tab_t, tab_m = st.tabs(["Frequency domain", "Time domain", "Measurements"])

# ---------------------------------------------------------------- frequency
with tab_f:
    l, r = st.columns(2)
    with l:
        st.subheader("Equalizer gain curve")
        st.caption("Gb·L(f) + Gm·(1−L−H) + Gt·H(f). Dashed lines are the cutoffs.")
        fig = go.Figure(go.Scatter(x=f_axis, y=20 * np.log10(np.maximum(H_eq, 1e-12)),
                                   name="Gain", line=dict(color=COLORS["output"], width=2.5)))
        log_axis(fig); cutoff_lines(fig, fc_low, fc_high)
        fig.update_yaxes(title="Gain (dB)", range=[min(-13, g_bass, g_mid, g_treble) - 1,
                                                   max(13, g_bass, g_mid, g_treble) + 1])
        st.plotly_chart(style(fig), width="stretch")
    with r:
        st.subheader("How the filters split the signal")
        st.caption("Power share per band. With filtfilt each band is 0.5 (−6 dB) at its cutoff; the three add to 1.")
        fig = go.Figure()
        for nm, v in (("bass", L), ("mid", M), ("treble", Hh)):
            fig.add_trace(go.Scatter(x=f_axis, y=v, name=nm.capitalize(), line=dict(color=COLORS[nm], width=2.5)))
        log_axis(fig); cutoff_lines(fig, fc_low, fc_high)
        fig.update_yaxes(title="Share of power", range=[-0.05, 1.05])
        st.plotly_chart(style(fig), width="stretch")

    st.subheader("Spectrum: input vs equalized output")
    st.caption("Welch power spectrum, 0 dB = strongest input peak.")
    fw, Px = welch(x, fs, nperseg=16384)
    _, Py = welch(y, fs, nperseg=16384)
    ref = Px.max()
    keep = (fw >= 20) & (fw <= 20000)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=fw[keep], y=10 * np.log10(Px[keep] / ref + 1e-20), name="Input",
                             line=dict(color=COLORS["input"], width=1.5)))
    fig.add_trace(go.Scatter(x=fw[keep], y=10 * np.log10(Py[keep] / ref + 1e-20), name="Output",
                             line=dict(color=COLORS["output"], width=1.5)))
    log_axis(fig); cutoff_lines(fig, fc_low, fc_high)
    fig.update_yaxes(title="Power (dB)", range=[-110, 10])
    st.plotly_chart(style(fig, 380), width="stretch")

# ---------------------------------------------------------------- time
with tab_t:
    dur = x.size / fs
    win_ms = st.slider("Window length (ms)", 5, 200, 25)
    start = st.slider("Window start (s)", 0.0, max(0.0, dur - win_ms / 1000), min(2.0, dur / 2), 0.01)
    s0 = int(start * fs); s1 = min(x.size, s0 + int(win_ms / 1000 * fs))
    t_ms = (np.arange(s0, s1) - s0) / fs * 1000

    l, r = st.columns(2)
    with l:
        st.subheader("Waveform: input vs output")
        st.caption("Red dashed lines mark ±1 (clipping limit).")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=t_ms, y=x[s0:s1], name="Input", line=dict(color=COLORS["input"], width=1.3)))
        fig.add_trace(go.Scatter(x=t_ms, y=y[s0:s1], name="Output", line=dict(color=COLORS["output"], width=1.3)))
        for v in (1, -1):
            fig.add_hline(y=v, line_dash="dash", line_color="red", opacity=0.5)
        fig.update_xaxes(title="Time (ms)"); fig.update_yaxes(title="Amplitude")
        st.plotly_chart(style(fig), width="stretch")
    with r:
        st.subheader("Separated bands, after gain")
        st.caption("Bass (low-pass), mid (residual), treble (high-pass), each × its gain.")
        fig = go.Figure()
        for nm, sig in (("bass", bass), ("mid", mid), ("treble", treble)):
            fig.add_trace(go.Scatter(x=t_ms, y=G[nm] * sig[s0:s1], name=nm.capitalize(),
                                     line=dict(color=COLORS[nm], width=1.3)))
        fig.update_xaxes(title="Time (ms)"); fig.update_yaxes(title="Amplitude")
        st.plotly_chart(style(fig), width="stretch")

# ---------------------------------------------------------------- measurements
with tab_m:
    l, r = st.columns(2)
    with l:
        st.subheader("System setup")
        st.dataframe(pd.DataFrame([
            ("Sampling rate", f"{fs:,}", "Hz"), ("Duration", f"{x.size/fs:.3f}", "s"),
            ("Samples", f"{x.size:,}", ""), ("Filter order", str(order), ""),
            ("Bass cutoff (low-pass)", str(fc_low), "Hz"), ("Treble cutoff (high-pass)", str(fc_high), "Hz"),
            ("Bass gain", f"{g_bass:+.1f} (× {G['bass']:.3f})", "dB"),
            ("Mid gain", f"{g_mid:+.1f} (× {G['mid']:.3f})", "dB"),
            ("Treble gain", f"{g_treble:+.1f} (× {G['treble']:.3f})", "dB"),
        ], columns=["Parameter", "Value", "Unit"]), hide_index=True, width="stretch")
    with r:
        st.subheader("This run vs report (Table 5.2)")
        ours = {
            "Input RMS": rms(x), "Output RMS": rms(y),
            "Input peak": float(np.max(np.abs(x))), "Output peak": float(np.max(np.abs(y))),
            "Input crest factor": float(np.max(np.abs(x))) / rms(x),
            "Output crest factor": float(np.max(np.abs(y))) / rms(y),
        }
        st.dataframe(pd.DataFrame({"Metric": list(ours),
                                   "This run": [round(v, 6) for v in ours.values()],
                                   "Report": [REPORT_REF[k] for k in ours]}),
                     hide_index=True, width="stretch")
        err = float(np.max(np.abs(bass + mid + treble - x)))
        st.caption(f"Reconstruction check: max |bass + mid + treble − input| = {err:.2e}. "
                   "Report values only match at +6 / 0 / −3 dB, 250 Hz / 4 kHz, order 4.")
