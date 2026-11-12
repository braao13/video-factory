"""Gera o video-base de um projeto: trecho, corte de silencio, velocidade, cor, layout 9:16 e audio.

Uso: python3 pipeline/base.py <projeto.json> <pasta_saida>
Saida: base.mp4, palavras.json (tempos remapeados para o video final, se o projeto tiver "palavras"),
       info.json (duracao final, trechos mantidos).
As camadas (legenda, titulo, emojis...) ficam por conta do Remotion (remotion/), que le o mesmo projeto.json.

Campos do projeto.json usados aqui (todos opcionais exceto "entrada"):
  entrada        caminho do video
  trecho         [inicio, fim] em segundos do original
  velocidade     1.0 = normal (ex.: 1.75)
  silencio       {"ativo": true, "db": -30, "min": 0.15, "margem": 0.06}
  look           nome de um arquivo em looks/ (sem .json)
  ajuste_brilho  % (ex.: -12 = 12% mais escuro)
  layout         {"tipo": "fundo-desfocado", "crop_cx": 630, "crop_largura": 560, "y": 300}
                 {"tipo": "tela-cheia", "crop_cx": null}   (preenche 9:16 cortando as laterais)
  saida          {"largura": 1080, "altura": 1920, "fps": 30}
  audio          {"original": true, "musica": {"arquivo": "...", "inicio": 10, "volume_db": 0, "ducking": true},
                  "lufs": -14, "limpar_voz": false}
  palavras       caminho do json do transcrever.py
"""
import json, os, re, subprocess, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def probe(video):
    p = json.loads(subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", video],
                                  capture_output=True, text=True).stdout)
    v = next(s for s in p["streams"] if s["codec_type"] == "video")
    return float(p["format"]["duration"]), v["width"], v["height"], any(s["codec_type"] == "audio" for s in p["streams"])


def filtro_look(nome, ajuste_brilho=0):
    partes = []
    if nome:
        lk = json.load(open(os.path.join(RAIZ, "looks", nome + ".json")))
        if lk.get("eq"):
            partes.append("eq=" + ":".join(f"{k}={v}" for k, v in lk["eq"].items()))
        if lk.get("curves"):
            partes.append("curves=" + lk["curves"])
        if lk.get("temperatura"):
            partes.append(f"colortemperature=temperature={lk['temperatura']['k']}:mix={lk['temperatura'].get('mix', 0.5)}")
        if lk.get("nitidez"):
            partes.append(f"unsharp=5:5:{lk['nitidez']}:5:5:0.0")
    if ajuste_brilho:
        f = 1 + ajuste_brilho / 100
        partes.append(f"colorchannelmixer=rr={f:.3f}:gg={f:.3f}:bb={f:.3f}")
    return ",".join(partes)


def trechos_com_fala(video, a, b, cfg):
    r = subprocess.run(["ffmpeg", "-ss", str(a), "-t", str(b - a), "-i", video, "-af",
                        f"silencedetect=noise={cfg.get('db', -30)}dB:d={cfg.get('min', 0.15)}", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    ev = re.findall(r"silence_(start|end): ([\d.]+)", r)
    sil, ini = [], None
    for k, v in ev:
        if k == "start": ini = float(v)
        elif ini is not None: sil.append((ini, float(v))); ini = None
    if ini is not None: sil.append((ini, b - a))
    m = cfg.get("margem", 0.06)
    keep, t = [], 0.0
    for s, e in sil:
        s2, e2 = s + m, e - m
        if e2 - s2 < 0.08: continue
        if s2 > t: keep.append([t, s2])
        t = e2
    if t < b - a: keep.append([t, b - a])
    return [[round(x + a, 3), round(y + a, 3)] for x, y in keep if y - x > 0.12]


def atempo(v):
    fs = []
    while v > 2.0: fs.append("atempo=2.0"); v /= 2.0
    while v < 0.5: fs.append("atempo=0.5"); v /= 0.5
    fs.append(f"atempo={v:.4f}")
    return ",".join(fs)


def main():
    proj_path, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    P = json.load(open(proj_path))
    base_dir = os.path.dirname(os.path.abspath(proj_path))
    rel = lambda p: p if os.path.isabs(p) else os.path.join(base_dir, p)
    video = rel(P["entrada"])
    dur, W, H, tem_audio = probe(video)
    a, b = P.get("trecho") or [0, dur]
    vel = float(P.get("velocidade", 1.0))
    S = P.get("saida", {}); OW, OH, FPS = S.get("largura", 1080), S.get("altura", 1920), S.get("fps", 30)
    A = P.get("audio", {}); usa_original = A.get("original", True) and tem_audio
    sil = P.get("silencio", {"ativo": usa_original})

    segs = trechos_com_fala(video, a, b, sil) if (sil.get("ativo") and tem_audio) else [[a, b]]
    pre = max(0.0, a - 2)  # input seeking para nao decodificar o video inteiro
    fc = []
    for i, (s, e) in enumerate(segs):
        fc.append(f"[0:v]trim={s - pre:.3f}:{e - pre:.3f},setpts=PTS-STARTPTS[v{i}]")
        if usa_original:
            d = e - s
            fc.append(f"[0:a]atrim={s - pre:.3f}:{e - pre:.3f},asetpts=PTS-STARTPTS,"
                      f"afade=t=in:d=0.015,afade=t=out:st={max(d - 0.015, 0):.3f}:d=0.015[a{i}]")
    n = len(segs)
    if usa_original:
        fc.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[cv][ca]")
    else:
        fc.append("".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[cv]")

    look = filtro_look(P.get("look"), P.get("ajuste_brilho", 0))
    vchain = f"[cv]setpts=PTS/{vel},fps={FPS}" + (f",{look}" if look else "")
    L = P.get("layout", {"tipo": "tela-cheia"})
    if L["tipo"] == "fundo-desfocado":
        cw = L.get("crop_largura", min(W, int(H * 0.78)))
        cx = L.get("crop_cx") or W // 2
        x = max(0, min(W - cw, int(cx - cw / 2)))
        fg_h = int(H * OW / cw) // 2 * 2
        y = L.get("y", max(0, (OH - fg_h) // 2))
        fc.append(f"{vchain},split[x][y]")
        fc.append(f"[x]scale={OW}:{OH}:force_original_aspect_ratio=increase,crop={OW}:{OH},boxblur=30:2,eq=brightness=-0.18[bg]")
        fc.append(f"[y]crop={cw}:{H}:{x}:0,scale={OW}:{fg_h}:flags=lanczos[fg]")
        fc.append(f"[bg][fg]overlay=0:{y}[v]")
    else:
        cx = L.get("crop_cx")
        if cx is None:
            fc.append(f"{vchain},scale={OW}:{OH}:force_original_aspect_ratio=increase:flags=lanczos,crop={OW}:{OH}[v]")
        else:
            sc = OH / H; nw = int(W * sc) // 2 * 2
            x = max(0, min(nw - OW, int(cx * sc - OW / 2)))
            fc.append(f"{vchain},scale={nw}:{OH}:flags=lanczos,crop={OW}:{OH}:{x}:0[v]")

    final = sum(e - s for s, e in segs) / vel
    inputs = ["-ss", str(pre), "-i", video]
    lufs = A.get("lufs", -14)
    vozf = "highpass=f=80,afftdn=nf=-25,acompressor=threshold=-18dB:ratio=3:attack=5:release=120" if A.get("limpar_voz") else ""
    M = A.get("musica")
    amap = None
    if usa_original:
        fc.append(f"[ca]{atempo(vel) if vel != 1 else 'anull'}" + (f",{vozf}" if vozf else "") + "[voz]")
    if M:
        inputs += ["-ss", str(M.get("inicio", 0)), "-i", rel(M["arquivo"])]
        vol = M.get("volume_db", -16 if usa_original else 0)
        fc.append(f"[1:a]atrim=0:{final:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.3,"
                  f"afade=t=out:st={max(final - 1.8, 0):.3f}:d=1.8,volume={vol}dB[mus]")
        if usa_original and M.get("ducking", True):
            fc.append("[voz]asplit[voz1][sc]")
            fc.append("[mus][sc]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[musd]")
            fc.append(f"[voz1][musd]amix=inputs=2:duration=first:normalize=0,loudnorm=I={lufs}:TP=-1.5[aout]")
        elif usa_original:
            fc.append(f"[voz][mus]amix=inputs=2:duration=first:normalize=0,loudnorm=I={lufs}:TP=-1.5[aout]")
        else:
            fc.append(f"[mus]loudnorm=I={lufs}:TP=-1.5[aout]")
        amap = "[aout]"
    elif usa_original:
        fc.append(f"[voz]loudnorm=I={lufs}:TP=-1.5:LRA=9[aout]")
        amap = "[aout]"

    cmd = ["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(fc), "-map", "[v]"]
    if amap: cmd += ["-map", amap, "-c:a", "aac", "-b:a", "192k", "-ar", "48000"]
    cmd += ["-t", f"{final:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", os.path.join(out, "base.mp4")]
    subprocess.run(cmd, check=True)

    if P.get("palavras"):
        ws = json.load(open(rel(P["palavras"])))
        novo, off = [], 0.0
        for s, e in segs:
            for w in ws:
                mid = (w["s"] + w["e"]) / 2
                if s <= mid < e:
                    novo.append({"w": w["w"], "s": round((max(w["s"], s) - s + off) / vel, 3),
                                 "e": round((min(w["e"], e) - s + off) / vel, 3)})
            off += e - s
        for c in P.get("correcoes", []):  # [{"de": "x", "para": "y", "t": 15.8 (opcional, tempo final)}]
            for w in novo:
                if w["w"] == c["de"] and ("t" not in c or abs(w["s"] - c["t"]) < 0.3):
                    w["w"] = c["para"]
        json.dump(novo, open(os.path.join(out, "palavras.json"), "w"), ensure_ascii=False)

    info = {"duracao": round(final, 3), "trechos": segs, "fps": FPS, "largura": OW, "altura": OH,
            "removido_s": round((b - a) - sum(e - s for s, e in segs), 2)}
    json.dump(info, open(os.path.join(out, "info.json"), "w"), indent=2)
    print(json.dumps(info))


if __name__ == "__main__":
    main()
