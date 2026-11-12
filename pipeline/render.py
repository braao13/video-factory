"""Aplica as camadas (legenda, titulo, emojis, zoom, flash, progresso) sobre o base.mp4 via Remotion.

Uso: python3 pipeline/render.py <projeto.json> <pasta_do_base> [--previa] [--quadros 2,12.5,40]
  --previa   render em 540x960 (rapido, pra conferir antes do final)
  --quadros  so gera imagens desses segundos (mosaico quadros.jpg), sem renderizar o video
Saida: <pasta>/<nome>.mp4 (ou <nome>_previa.mp4 / quadros.jpg)

Bloco "camadas" do projeto.json:
  "legenda":  {"estilo": "amarela-impacto", "ajustes": {...}, "cores_palavras": {"#FF3B3B": ["medo"]}}  ou null
  "titulo":   {"estilo": "badge-amarelo", "texto": "MEDO X FESTA", "destaque": "X", "subtitulo": "...", "ate": null}
  "emojis":   [{"t": 0.18, "e": "📺"}, {"t": 2.7, "e": "😨", "x": 200, "y": 560, "dur": 1.6}]
  "zooms": [2.72, 11.78], "zoom_forca": 0.12, "flashes": [11.78], "zoom_lento": 0.05,
  "batidas": [..] ou "batidas": "auto" (detecta na musica), "pulso_forca": 0.035,
  "progresso": {"cor": "#FFE600"}
  "versus":   {"estilo": "padrao", "esquerda": {"img": "zago.jpg", "nome": "ZAGO"}, "direita": {"img": "apollo.jpg", "nome": "APOLLO"},
              "foco": "center 25%" (opcional por lado), "de": 0, "ate": null}   -> cabecalho com 2 fotos + VS; titulo desce sozinho
  "cta":      {"estilo": "cta-bufaclips", "texto": "Você concorda?", "destaque": "concorda", "duracao": 3}  (ultimos N s)
"""
import argparse, json, os, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from projeto import carregar

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REM = os.path.join(RAIZ, "remotion")


def estilo(tipo, nome, ajustes=None):
    e = json.load(open(os.path.join(RAIZ, "estilos", tipo, nome + ".json")))
    e.update(ajustes or {})
    return e


def batidas_auto(P, base_dir):
    import librosa, numpy as np
    M = P["audio"]["musica"]
    arq = M["arquivo"] if os.path.isabs(M["arquivo"]) else os.path.join(base_dir, M["arquivo"])
    y, sr = librosa.load(arq, sr=22050, mono=True, offset=M.get("inicio", 0), duration=600)
    _, b = librosa.beat.beat_track(y=y, sr=sr)
    return [round(float(x), 3) for x in librosa.frames_to_time(b, sr=sr)][::4]


def chrome():
    env = os.path.join(RAIZ, ".env.sh")
    if os.path.exists(env):
        for l in open(env):
            if "VF_CHROME=" in l: return l.split("=", 1)[1].strip().strip('"')
    return os.environ.get("VF_CHROME", "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("projeto"); ap.add_argument("pasta")
    ap.add_argument("--previa", action="store_true"); ap.add_argument("--quadros")
    a = ap.parse_args()
    P = carregar(a.projeto); base_dir = os.path.dirname(os.path.abspath(a.projeto))
    nome = P.get("nome", "projeto")
    info = json.load(open(os.path.join(a.pasta, "info.json")))
    pal = os.path.join(a.pasta, "palavras.json")
    C = dict(P.get("camadas", {}))

    if C.get("legenda"):
        L = C["legenda"]; C["legenda"] = {**L, "estilo": estilo("legenda", L["estilo"], L.get("ajustes"))}
    if C.get("titulo") and C["titulo"].get("texto"):
        T = C["titulo"]; C["titulo"] = {**T, "estilo": estilo("titulo", T["estilo"], T.get("ajustes"))}
    if C.get("cta") and C["cta"].get("texto"):
        T = C["cta"]; C["cta"] = {**T, "estilo": estilo("titulo", T["estilo"], T.get("ajustes"))}
    else:
        C.pop("cta", None)
    if C.get("titulo") and not C["titulo"].get("texto"):
        C.pop("titulo")
    V = C.get("versus")
    if V and V.get("esquerda") and V.get("direita"):
        V = {**V, "estilo": estilo("versus", V.get("estilo", "padrao"), V.get("ajustes"))}
        for lado in ("esquerda", "direita"):
            src = V[lado]["img"]; src = src if os.path.isabs(src) else os.path.join(base_dir, src)
            dst = f"{nome}_{lado}{os.path.splitext(src)[1].lower()}"
            os.makedirs(os.path.join(REM, "public"), exist_ok=True)
            shutil.copy(src, os.path.join(REM, "public", dst))
            V[lado] = {**V[lado], "img": dst}
        C["versus"] = V
        # se o titulo cair em cima do cabecalho, desce pra logo abaixo dele
        fim_cab = (V.get("y") or V["estilo"]["y"]) + V["estilo"].get("altura", 270)
        if C.get("titulo"):
            y_t = C["titulo"].get("y") or C["titulo"]["estilo"]["y"]
            if y_t < fim_cab:
                C["titulo"]["y"] = fim_cab
    else:
        C.pop("versus", None)
    if C.get("batidas") == "auto":
        C["batidas"] = batidas_auto(P, base_dir)

    os.makedirs(os.path.join(REM, "public"), exist_ok=True)
    shutil.copy(os.path.join(a.pasta, "base.mp4"), os.path.join(REM, "public", f"{nome}.mp4"))
    props = {"info": info, "video": f"{nome}.mp4", "camadas": C,
             "palavras": json.load(open(pal)) if os.path.exists(pal) else []}
    pp = os.path.abspath(os.path.join(a.pasta, "props.json"))
    json.dump(props, open(pp, "w"), ensure_ascii=False)

    base = ["npx", "remotion"]
    comum = [f"--props={pp}", f"--browser-executable={chrome()}"]
    if a.quadros:
        imgs = []
        for i, t in enumerate(a.quadros.split(",")):
            o = os.path.abspath(os.path.join(a.pasta, f"q{i}.png"))
            subprocess.run(base + ["still", "src/index.tsx", "Projeto", o, f"--frame={int(float(t) * info['fps'])}",
                                   "--scale=0.33", *comum], cwd=REM, check=True, capture_output=True)
            imgs.append(o)
        ins = sum([["-i", x] for x in imgs], [])
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", f"hstack={len(imgs)}" if len(imgs) > 1 else "null",
                        os.path.join(a.pasta, "quadros.jpg")], check=True)
        print(os.path.join(a.pasta, "quadros.jpg")); return

    out = os.path.abspath(os.path.join(a.pasta, f"{nome}{'_previa' if a.previa else ''}.mp4"))
    extra = ["--scale=0.5", "--crf=28"] if a.previa else ["--crf=20"]
    subprocess.run(base + ["render", "src/index.tsx", "Projeto", out, "--concurrency=2", *extra, *comum], cwd=REM, check=True)
    print(out)


if __name__ == "__main__":
    main()
