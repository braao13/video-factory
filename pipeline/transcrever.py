"""Transcreve um video com marcacao de tempo por palavra.

Uso: python3 pipeline/transcrever.py <video> <saida.json> [--lang pt] [--inicio S] [--fim S]
Saida: lista de {"w": palavra, "s": inicio, "e": fim} em segundos do video original.
"""
import argparse, json, os, subprocess, tempfile, wave
import numpy as np
from faster_whisper import WhisperModel

MODELO = os.path.expanduser("~/.cache/vf-whisper-small")


def carregar_audio(video, inicio=None, fim=None):
    tmp = tempfile.mktemp(suffix=".wav")
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    if inicio is not None:
        cmd += ["-ss", str(inicio)]
    if fim is not None:
        cmd += ["-to", str(fim)] if inicio is None else ["-t", str(fim - inicio)]
    cmd += ["-i", video, "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", tmp]
    subprocess.run(cmd, check=True)
    with wave.open(tmp) as wf:
        a = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    os.remove(tmp)
    return a


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("saida")
    ap.add_argument("--lang", default="pt")
    ap.add_argument("--inicio", type=float); ap.add_argument("--fim", type=float)
    ap.add_argument("--modelo", default=MODELO)
    a = ap.parse_args()

    audio = carregar_audio(a.video, a.inicio, a.fim)
    off = a.inicio or 0.0
    m = WhisperModel(a.modelo, device="cpu", compute_type="int8", cpu_threads=os.cpu_count() or 2)
    segs, info = m.transcribe(audio, language=a.lang, word_timestamps=True, beam_size=1)
    palavras, linhas = [], []
    for s in segs:
        linhas.append(f"[{s.start + off:7.1f}] {s.text.strip()}")
        for w in s.words:
            palavras.append({"w": w.word.strip(), "s": round(w.start + off, 3), "e": round(w.end + off, 3)})
    json.dump(palavras, open(a.saida, "w"), ensure_ascii=False)
    txt = os.path.splitext(a.saida)[0] + ".txt"
    open(txt, "w").write("\n".join(linhas) + "\n")
    print(f"{len(palavras)} palavras -> {a.saida} (texto em {txt})")


if __name__ == "__main__":
    main()
