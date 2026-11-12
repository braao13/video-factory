"""Raio-x rapido de um video antes de editar.

Uso: python3 pipeline/analisar.py <video> <pasta_saida>
Gera: analise.json (duracao, resolucao, fps, brilho, saturacao, volume, se tem fala)
      folha.jpg (mosaico de quadros pra ver enquadramento e luz)
"""
import json, os, re, subprocess, sys



def main():
    video, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    p = json.loads(subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", video],
                                  capture_output=True, text=True).stdout)
    v = next(s for s in p["streams"] if s["codec_type"] == "video")
    tem_audio = any(s["codec_type"] == "audio" for s in p["streams"])
    dur = float(p["format"]["duration"])
    num, den = v["r_frame_rate"].split("/")

    # brilho e saturacao medios em 6 pontos
    ys, ss = [], []
    for i in range(6):
        t = dur * (i + 0.5) / 6
        r = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", video, "-frames:v", "1",
                            "-vf", "signalstats,metadata=print:file=-", "-f", "null", "-"], capture_output=True, text=True).stdout
        y = re.search(r"YAVG=([\d.]+)", r); s = re.search(r"SATAVG=([\d.]+)", r)
        if y: ys.append(float(y.group(1)))
        if s: ss.append(float(s.group(1)))

    vol = {}
    if tem_audio:
        r = subprocess.run(["ffmpeg", "-i", video, "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True).stderr
        for k in ("mean_volume", "max_volume"):
            m = re.search(k + r": ([-\d.]+) dB", r)
            if m: vol[k] = float(m.group(1))
        r = subprocess.run(["ffmpeg", "-i", video, "-af", "silencedetect=noise=-35dB:d=0.5", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
        sil = sum(float(x) for x in re.findall(r"silence_duration: ([\d.]+)", r))
        vol["fracao_silencio"] = round(sil / dur, 2)

    brilho = round(sum(ys) / len(ys), 1) if ys else None
    a = {
        "duracao": round(dur, 2), "largura": v["width"], "altura": v["height"],
        "fps": round(int(num) / int(den), 2), "tem_audio": tem_audio, **vol,
        "brilho_yavg": brilho, "saturacao_satavg": round(sum(ss) / len(ss), 1) if ss else None,
        "dica_brilho": None if brilho is None else ("claro: nao clarear" if brilho > 150 else "escuro: pode clarear" if brilho < 90 else "normal"),
        "dica_fala": None if not tem_audio else ("provavelmente sem fala" if vol.get("mean_volume", 0) < -38 or vol.get("fracao_silencio", 0) > 0.8 else "tem fala"),
    }
    json.dump(a, open(os.path.join(out, "analise.json"), "w"), indent=2, ensure_ascii=False)

    n = 12
    passo = max(dur / n, 0.5)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-vf",
                    f"fps=1/{passo:.3f},scale=-1:300,tile=6x2", "-frames:v", "1", os.path.join(out, "folha.jpg")])
    print(json.dumps(a, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
