# Methodology

1. Generate or load a discrete-time audio signal x[n] sampled at Fs = 44,100 Hz.
2. Convert stereo input to mono for simplified analysis and normalize it.
3. Design fourth-order Butterworth low-pass and high-pass filters with nominal cutoffs at 250 Hz and 4 kHz.
4. Extract bass with the low-pass filter and treble with the high-pass filter. Define the midrange as the residual x[n] - bass[n] - treble[n], so the three branches sum to the original signal before gain changes.
5. Convert gains in dB to linear amplitude gains using G = 10^(dB/20).
6. Form y_raw[n] = G_b*bass[n] + G_m*mid[n] + G_t*treble[n].
7. If needed, scale the output to prevent peak clipping.
8. Calculate RMS and peak amplitudes; plot waveform, spectrum and filter responses.
9. Save the equalized audio and figures. Listen to original and equalized signals at a safe volume.

## Flowchart
See `results/flowchart.png`.

## Design values
Sampling frequency: 44.1 kHz. Bass cutoff: 250 Hz. Treble cutoff: 4 kHz. Gains: bass +6 dB, mid 0 dB, treble -3 dB. These are demonstration values and can be changed.
