# Digital Audio Equalizer Using MATLAB

## Overview
A three-band educational digital audio equalizer. It splits a signal into bass, midrange residual, and treble components, applies independent gains in dB, recombines the bands, and saves plots and output audio.

## Contents
- `matlab/Digital_Audio_Equalizer.m` — MATLAB source.
- `dataset/synthetic_input.wav` — 5-second, 44.1 kHz synthetic audio.
- `dataset/synthetic_input.csv` — time/amplitude samples.
- `dataset/processed_signals.csv` — Python reference processing signals.
- `dataset/equalized_output_reference.wav` — illustrative equalized output.
- `results/` — figures, flowchart, and measured Python reference metrics.
- `report/` — project report in DOCX and PDF.
- `docs/` — methodology and reference notes.

## Run in MATLAB
1. Extract the ZIP.
2. Open MATLAB and set the current folder to the project root.
3. Open `matlab/Digital_Audio_Equalizer.m` and click Run.
4. The script reads `dataset/synthetic_input.wav` and writes the MATLAB output into `dataset/`.
5. Required MATLAB functions: `audioread`, `audiowrite`, `butter`, `filtfilt`, `freqz`. The last three require Signal Processing Toolbox.

## Gain settings
- Bass: +6 dB
- Midrange: 0 dB
- Treble: -3 dB

Gain conversion: `linearGain = 10^(gain_dB/20)`.

## Dataset
The synthetic audio contains tones at 100 Hz, 1 kHz, and 8 kHz with a slowly varying amplitude envelope and low-level Gaussian noise. It is synthetic test data, not a real-world music recording.

## Important interpretation note
The graphs and metrics in `results/` are reference results generated with Python's SciPy implementation of the same filter concept. MATLAB results can differ slightly due to numerical implementation. Re-run the MATLAB script and use its printed values for the final submitted results.

## Research references
1. S. J. Orfanidis, “High-Order Digital Parametric Equalizer Design,” Journal of the Audio Engineering Society, vol. 53, no. 11, pp. 1026–1046, 2005. https://aes.org/publications/elibrary-page/?id=13397
2. MathWorks, “Equalization,” MATLAB & Simulink Documentation. https://www.mathworks.com/help/audio/ug/equalization.html
3. MathWorks, “Graphic Equalization,” MATLAB & Simulink Documentation. https://www.mathworks.com/help/audio/ug/graphic-equalization.html
