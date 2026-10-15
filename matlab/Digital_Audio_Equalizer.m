%% DIGITAL AUDIO EQUALIZER USING MATLAB
% Three-band equalizer: bass, midrange residual, and treble.
% Requires Signal Processing Toolbox (butter, filtfilt, freqz).
% Put synthetic_input.wav in the dataset folder or choose your own WAV file.

clc; clear; close all;

%% 1. Load input audio
inputFile = fullfile('..','dataset','synthetic_input.wav');
if isfile(inputFile)
    [x, Fs] = audioread(inputFile);
else
    Fs = 44100;
    t = (0:1/Fs:5-1/Fs)';
    x = 0.50*sin(2*pi*100*t) + ...
        0.30*sin(2*pi*1000*t) + ...
        0.20*sin(2*pi*8000*t);
    x = x / max(abs(x));
end

% Convert stereo to mono for analysis
if size(x,2) > 1
    x = mean(x,2);
end
x = x / (max(abs(x)) + eps);
N = length(x);
t = (0:N-1)'/Fs;
nyquist = Fs/2;

%% 2. Filter design
bassCutoff = min(250, 0.8*nyquist);
trebleCutoff = min(4000, 0.9*nyquist);
if trebleCutoff <= bassCutoff
    error('Sampling rate is too low for the selected frequency bands.');
end

[bBass,aBass] = butter(4, bassCutoff/nyquist, 'low');
[bTreble,aTreble] = butter(4, trebleCutoff/nyquist, 'high');

%% 3. Split signal into three bands
bass = filtfilt(bBass,aBass,x);
treble = filtfilt(bTreble,aTreble,x);
% Residual mid band makes the three bands sum to the original signal
% before gain adjustment (apart from numerical precision).
mid = x - bass - treble;

%% 4. Set gains (change these values to experiment)
bassGain_dB = 6;       % boost bass
midGain_dB = 0;        % unchanged midrange
trebleGain_dB = -3;    % reduce treble

gBass = 10^(bassGain_dB/20);
gMid = 10^(midGain_dB/20);
gTreble = 10^(trebleGain_dB/20);

%% 5. Apply gains and combine bands
yRaw = gBass*bass + gMid*mid + gTreble*treble;
% Avoid clipping while retaining the relative band balance
y = yRaw / max(1, max(abs(yRaw)));

%% 6. Calculate measurements
rmsInput = sqrt(mean(x.^2));
rmsOutput = sqrt(mean(y.^2));
peakInput = max(abs(x));
peakOutput = max(abs(y));

fprintf('\nDIGITAL AUDIO EQUALIZER RESULTS\n');
fprintf('Sampling rate: %d Hz\n', Fs);
fprintf('Duration: %.3f seconds\n', N/Fs);
fprintf('Bass / Mid / Treble gains: %.1f / %.1f / %.1f dB\n', ...
    bassGain_dB, midGain_dB, trebleGain_dB);
fprintf('Input RMS: %.6f\n', rmsInput);
fprintf('Output RMS: %.6f\n', rmsOutput);
fprintf('Input peak: %.6f\n', peakInput);
fprintf('Output peak: %.6f\n', peakOutput);

%% 7. Plot waveform comparison
nShow = min(N, round(0.05*Fs));
figure('Name','Waveform Comparison');
plot(t(1:nShow),x(1:nShow),'DisplayName','Original'); hold on;
plot(t(1:nShow),y(1:nShow),'DisplayName','Equalized');
xlabel('Time (s)'); ylabel('Amplitude');
title('Original vs Equalized Audio (first 50 ms)');
legend; grid on;

%% 8. Plot frequency spectrum
nfft = 2^nextpow2(N);
X = fft(x,nfft);
Y = fft(y,nfft);
f = (0:nfft/2)'*Fs/nfft;
figure('Name','Frequency Spectrum');
plot(f,20*log10(abs(X(1:nfft/2+1))+eps), ...
    'DisplayName','Original'); hold on;
plot(f,20*log10(abs(Y(1:nfft/2+1))+eps), ...
    'DisplayName','Equalized');
xlabel('Frequency (Hz)'); ylabel('Magnitude (dB, relative)');
title('Original vs Equalized Frequency Spectrum');
legend; grid on; xlim([0 nyquist]);

%% 9. Plot filter responses
figure('Name','Filter Responses');
freqz(bBass,aBass,2048,Fs);
title('Bass Low-Pass Butterworth Filter');

figure('Name','Treble Filter Response');
freqz(bTreble,aTreble,2048,Fs);
title('Treble High-Pass Butterworth Filter');

%% 10. Save results
outFile = fullfile('..','dataset','equalized_output_matlab.wav');
audiowrite(outFile,y,Fs);
save(fullfile('..','results','equalizer_results.mat'), ...
    'Fs','bassGain_dB','midGain_dB','trebleGain_dB', ...
    'rmsInput','rmsOutput','peakInput','peakOutput');

disp(['Saved equalized audio to: ', outFile]);
% Uncomment to listen:
% sound(y,Fs);
