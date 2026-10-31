"""効果音・BGMをすべて合成して audio.wav を作る。
使い方: python3 audio.py   （先に node render.mjs --stills 0 などで timeline.json を出力しておく）
"""
import json
import numpy as np
from scipy.signal import butter, sosfilt

SR = 44100
tl = json.load(open("timeline.json"))
DUR = tl["dur"]
N = int(DUR * SR)
L = np.zeros(N)
R = np.zeros(N)
rng = np.random.default_rng(7)


def T(sec):
    return int(sec * SR)


def add(sig, at, gain=1.0, pan=0.0):
    i = T(at)
    if i >= N:
        return
    sig = sig[: N - i] * gain
    L[i:i + len(sig)] += sig * (1 - max(0, pan))
    R[i:i + len(sig)] += sig * (1 + min(0, pan))


def env(n, a=0.005, d=0.2, curve=4.0):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d * curve / 4)
    return e


def filt(x, kind, f):
    sos = butter(2, f, btype=kind, fs=SR, output="sos")
    return sosfilt(sos, x)


def noise(sec):
    return rng.standard_normal(int(sec * SR))


def tone(freq, sec, shape="sine"):
    t = np.arange(int(sec * SR)) / SR
    ph = 2 * np.pi * np.cumsum(np.broadcast_to(freq, t.shape)) / SR if np.ndim(freq) else 2 * np.pi * freq * t
    if shape == "sine":
        return np.sin(ph)
    if shape == "saw":
        return 2 * ((ph / (2 * np.pi)) % 1) - 1
    if shape == "square":
        return np.sign(np.sin(ph))
    return np.sin(ph)


def kick(sec=0.45):
    t = np.arange(int(sec * SR)) / SR
    f = 45 + 110 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)


def boom(sec=2.5, low=32):
    t = np.arange(int(sec * SR)) / SR
    f = low + 80 * np.exp(-t * 12)
    b = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.8)
    n = filt(noise(sec), "low", 900) * np.exp(-t * 5) * 0.6
    return b + n


def snare(sec=0.25):
    t = np.arange(int(sec * SR)) / SR
    return filt(noise(sec), "high", 1800) * np.exp(-t * 18) * 0.6 + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25) * 0.4


def hat(sec=0.06):
    t = np.arange(int(sec * SR)) / SR
    return filt(noise(sec), "high", 7000) * np.exp(-t * 60)


def clang(base):
    sec = 0.5
    t = np.arange(int(sec * SR)) / SR
    s = sum(np.sin(2 * np.pi * base * r * t) * np.exp(-t * (8 + 4 * k)) / (k + 1) for k, r in enumerate([1, 2.76, 5.4, 8.93]))
    s += filt(noise(sec), "high", 3000) * np.exp(-t * 40) * 0.8
    return s


def beep(f, sec=0.12):
    t = np.arange(int(sec * SR)) / SR
    return np.sin(2 * np.pi * f * t) * np.minimum(1, (sec - t) * 60) * np.minimum(1, t * 400)


def riser(sec, f0=200, f1=3000):
    n = noise(sec)
    out = np.zeros_like(n)
    seg = 2048
    for i in range(0, len(n), seg):
        k = i / len(n)
        fc = f0 * (f1 / f0) ** k
        out[i:i + seg] = filt(n[i:i + seg], "band", [fc * 0.7, fc * 1.3])
    return out * np.linspace(0.2, 1, len(n)) ** 2


def pluck(freq, sec=2.2):
    """Karplus-Strong（琴っぽい撥弦）"""
    n = int(sec * SR)
    p = int(SR / freq)
    buf = rng.uniform(-1, 1, p)
    out = np.zeros(n)
    for i in range(n):
        out[i] = buf[i % p]
        buf[i % p] = 0.4985 * (buf[i % p] + buf[(i + 1) % p])
    return filt(out, "low", 5000) * np.minimum(1, np.arange(n) / 30)


# ---------------- 0〜38.3s：都市 ----------------
# 風切り音（落下速度に追従）
def scroll_speed(t):
    if t < 1.2: return 0
    if t < 6: return 3200 * ((t - 1.2) / 4.8) ** 1.5
    if t < 6.5: return 3200 + (260 - 3200) * (1 - (1 - (t - 6) / .5) ** 3)
    if t < 16: return 260
    if t < 17.5: return 260 + 2340 * ((t - 16) / 1.5) ** 3
    if t < 32.6: return 2600 + 900 * max(0, min(1, (t - 28) / 4.6))
    return 0


tt = np.arange(N) / SR
spd = np.interp(tt, np.arange(0, DUR, 0.01), [scroll_speed(x) for x in np.arange(0, DUR, 0.01)]) / 3500
wind = filt(noise(DUR), "band", [250, 2500]) * (0.04 + 0.5 * spd) * (tt < 32.6)
L += wind * 0.5
R += np.roll(wind, 400) * 0.5

# 都市の低いドローン（Cマイナー系）
drone = sum(tone(f, DUR, "saw") for f in [65.4, 98.0, 77.8 * 1.003])
drone = filt(drone, "low", 400) * 0.05
drone *= np.clip(tt / 0.5, 0, 1) * (tt < 32.6)
L += drone; R += drone

# ワイヤー切断
add(clang(1400) * 1.2, 1.2, 0.7)
add(filt(noise(0.3), "high", 2000) * env(T(0.3), 0.001, 0.08), 1.2, 0.7)
add(clang(900), 1.27, 0.5, 0.4)

# ビート：1.2〜6 (128BPM)
bpm = 128; b = 60 / bpm
x = 1.2
while x < 5.95:
    add(kick(), x, 0.9)
    add(hat(), x + b / 2, 0.25, 0.3)
    x += b
add(riser(1.2, 300, 4000), 4.8, 0.25)

# スロー（解析モード）：心音 + グリッチ
add(filt(noise(0.25), "band", [500, 3000]) * np.sign(np.sin(np.arange(T(.25)) / 9)), 6.0, 0.4)
for x in np.arange(6.4, 16, 1.05):
    add(filt(kick(0.3), "low", 120), x, 1.0)
    add(filt(kick(0.3), "low", 120), x + 0.28, 0.7)
pad = sum(tone(f, 10, "sine") for f in [130.8, 155.6, 196.0, 233.1])
pad = pad * np.minimum(1, np.arange(len(pad)) / SR / 1.0) * np.minimum(1, (len(pad) / SR - np.arange(len(pad)) / SR) / .5) * 0.04
add(pad, 6.2)
for at, f in [(6.7, 1320), (9.6, 1760), (12.3, 1480)]:
    add(beep(f), at, 0.25)
    add(beep(f * 1.5), at + 0.13, 0.2)
add(riser(0.5, 800, 5000), 12.0, 0.2)
add(boom(1.8, 40), 14.5, 0.8); add(snare(0.4) * 2, 14.5, 0.8)       # 「助からない」スタンプ
# 「…ただし」
add(filt(noise(0.35), "band", [400, 4000]) * np.sign(np.sin(np.arange(T(.35)) / 5)), 16.0, 0.35)
add(boom(3.0, 30), 16.3, 1.0)
add(riser(1.2, 150, 2500), 16.3, 0.3)

# ビート：17.5〜32.6 (150BPM) + ベース
bpm = 150; b = 60 / bpm
x = 17.5; i = 0
bass_notes = [43.65, 43.65, 51.9, 38.9]
while x < 32.5:
    add(kick(), x, 0.9)
    add(hat(), x + b / 2, 0.22, -0.3)
    add(hat(), x + b / 4 * 3, 0.12, 0.3)
    if i % 2 == 1:
        add(snare(), x, 0.45)
    f = bass_notes[(i // 4) % 4]
    bs = filt(tone(f * 2, b * 0.9, "saw"), "low", 500) * env(T(b * 0.9), 0.005, 0.25)
    add(bs, x, 0.35)
    x += b; i += 1

# 三角飛びの衝突音
prev = -1
for c in tl["contacts"]:
    gap = c - prev
    prev = c
    if gap < 0.03:
        continue
    g = min(0.55, 0.12 + gap * 0.9)
    base = 700 + rng.uniform(-80, 80)
    pn = rng.uniform(-0.6, 0.6)
    add(clang(base) * 0.6, c, g, pn); add(boom(0.25, 60) * 0.5, c, g, pn)
# 高速域は連続する火花ノイズ
crackle = filt(noise(DUR), "high", 2500) * (rng.random(N) > 0.997) * 6
crack_env = np.clip((tt - 24) / 5, 0, 1) * (tt < 32.6)
L += filt(crackle, "high", 2000) * crack_env * 0.25
R += filt(np.roll(crackle, 777), "high", 2000) * crack_env * 0.25

# 警告アラーム
x = 29.3; k = 0
while x < 32.5:
    add(tone(880 if k % 2 == 0 else 660, 0.16, "square") * 0.5, x, 0.12)
    x += 0.17; k += 1
add(riser(3.3, 200, 6000), 29.3, 0.45)

# ホワイトアウト
add(boom(2.0, 28), 32.6, 1.1)
add(filt(noise(1.5), "high", 3000) * np.exp(-np.arange(T(1.5)) / SR * 3), 32.6, 0.4)

# 流星の落下音（ピッチ下降のヒュー）
sec = 3.5
t = np.arange(T(sec)) / SR
whistle = np.sin(2 * np.pi * np.cumsum(1800 - 1200 * (t / sec)) / SR) * (t / sec) ** 2 * 0.25
add(whistle, 32.8, 0.6); add(riser(sec, 400, 2500) * 0.8, 32.8, 0.6)
# 着水：ドーン + バシャー + ジュワァ（湯けむり）
add(boom(2.5, 35), 36.3, 1.2)
splash = filt(noise(1.2), "band", [500, 6000]) * env(T(1.2), 0.002, 0.35)
add(splash, 36.3, 0.8)
sz = filt(noise(2.0), "high", 4500) * np.exp(-np.arange(T(2.0)) / SR * 1.2) * (1 + 0.5 * rng.random(T(2.0)))
add(sz, 36.45, 0.35)

# ---------------- 38.3〜38.8s：無音 ----------------
L[T(38.3):T(38.8)] *= 0
R[T(38.3):T(38.8)] *= 0
# 38.3 以降に食い込んだ都市の音を切る（着水の余韻はフェード）
fade = np.ones(N)
fade[T(37.6):T(38.3)] = np.linspace(1, 0, T(38.3) - T(37.6))
fade[T(38.3):] = 0
L *= fade; R *= fade

# ---------------- 38.8〜52s：露天風呂 ----------------
on = (tt >= 38.8) * np.clip((tt - 38.8) / 1.5, 0, 1) * np.clip((DUR - tt) / 1.5, 0, 1)
water = filt(noise(DUR), "band", [600, 3500])
water *= 0.5 + 0.5 * np.abs(filt(noise(DUR), "low", 6))  # ちょろちょろ感
L += water * on * 0.05
R += np.roll(water, 999) * on * 0.05
# 鈴虫
for x in np.arange(39.4, 51.5, 0.9):
    for j in range(3):
        ch = tone(4300, 0.05) * np.sin(np.linspace(0, np.pi, T(0.05)))
        add(ch, x + j * 0.07 + rng.uniform(0, .05), 0.03, 0.6)


# ししおどし「コーン」
def kon():
    sec = 1.6
    t = np.arange(T(sec)) / SR
    s = (np.sin(2 * np.pi * 520 * t) * np.exp(-t * 14) + 0.6 * np.sin(2 * np.pi * 1310 * t) * np.exp(-t * 22)
         + 0.3 * np.sin(2 * np.pi * 260 * t) * np.exp(-t * 9))
    s += filt(noise(sec), "band", [800, 3000]) * np.exp(-t * 80) * 0.5
    # 簡易リバーブ
    out = s.copy()
    for d, g in [(0.071, .35), (0.113, .28), (0.167, .2), (0.241, .14), (0.33, .09)]:
        out[T(d):] += s[:len(s) - T(d)] * g
    return out


for k in [39.6, 45.4, 51.2]:
    add(filt(noise(0.6), "band", [900, 2500]) * np.linspace(0, 1, T(0.6)) * 0.15, k - 0.6, 0.6)  # 水が溜まる音
    add(kon(), k, 0.55, 0.35)

# 琴（都節音階 D Eb G A Bb）
scale = [293.7, 311.1, 392.0, 440.0, 466.2, 587.3, 622.3]
melody = [(40.4, 5), (41.0, 3), (41.6, 2), (42.6, 4), (43.4, 0),
          (44.6, 6), (45.0, 5), (45.6, 3), (46.4, 4), (47.4, 2), (48.0, 0),
          (49.2, 5), (49.6, 4), (50.0, 3), (50.6, 1), (51.0, 0)]
for at, n in melody:
    add(pluck(scale[n] / 2, 2.4), at, 0.32, rng.uniform(-0.3, 0.3))
add(pluck(146.8 / 2, 3.0), 40.4, 0.25)
add(pluck(146.8 / 2, 3.0), 49.2, 0.25)

L[T(38.8):] *= 1.9
R[T(38.8):] *= 1.9

# ---------------- 書き出し ----------------
mix = np.stack([L, R], 1)
mix = np.tanh(mix * 1.1)
mix /= np.max(np.abs(mix)) * 1.05
import wave
with wave.open("audio.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype("<i2").tobytes())
print("wrote audio.wav", mix.shape[0] / SR, "sec")
