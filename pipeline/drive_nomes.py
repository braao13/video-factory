"""Calcula os nomes do Drive para um novo video.

Uso: python3 pipeline/drive_nomes.py "<titulos existentes separados por |>" --tema "medo x festa" [--cortes "tema1|tema2"] [--modelo]
  Os titulos existentes vem da busca no Drive (search_files com parentId de cada pasta do drive.json).
Saida (json): numero, e o nome final de cada arquivo por pasta.
"""
import argparse, json, re, unicodedata


def limpa(t):
    t = unicodedata.normalize("NFC", t.strip().lower())
    t = re.sub(r"[\\/:*?\"<>|]", "", t)
    return re.sub(r"\s+", " ", t)[:60]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("existentes"); ap.add_argument("--tema", required=True)
    ap.add_argument("--cortes"); ap.add_argument("--modelo", action="store_true")
    a = ap.parse_args()
    nums = [int(m) for m in re.findall(r"video\s+(\d+)", a.existentes, re.I)]
    n = (max(nums) if nums else 0) + 1
    nn = f"{n:02d}"
    out = {"numero": nn, "originais": f"Video {nn} - {limpa(a.tema)}.mp4"}
    if a.modelo:
        out["modelos"] = f"Video {nn} - {limpa(a.tema)}.mp4"
    if a.cortes:
        out["editados"] = [f"Video {nn}-{i} - {limpa(t)}.mp4" for i, t in enumerate(a.cortes.split("|"), 1)]
    else:
        out["editados"] = [f"Video {nn} - {limpa(a.tema)}.mp4"]
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
