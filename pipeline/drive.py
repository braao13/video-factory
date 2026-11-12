"""Salva videos no Google Drive (pastas Editados / Originais / Modelos) com numeracao ligada.

Config: arquivo .drive.env na raiz do repo (NAO vai pro git) ou variaveis de ambiente:
  VF_DRIVE_URL=<url /exec do App da Web do drive/apps_script.gs>
  VF_DRIVE_KEY=<CHAVE definida nas propriedades do script>

Uso:
  python3 pipeline/drive.py listar
  python3 pipeline/drive.py nomes --tema "pov trabalhando" [--cortes "medo x festa|tema 2"] [--modelo]
  python3 pipeline/drive.py enviar <arquivo> --pasta editados|originais|modelos --nome "Video 03 - tema.mp4" [--substituir]

Regras de nome (ver drive.json): "Video NN - tema.mp4"; cortes = "Video NN-1 - tema.mp4"...
O proximo NN = maior numero encontrado nas 3 pastas + 1.
"""
import argparse, json, os, re, sys, unicodedata
import requests

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHUNK = 16 * 1024 * 1024  # multiplo de 256 KiB, exigido pelo upload resumable


def config():
    env = os.path.join(RAIZ, ".drive.env")
    if os.path.exists(env):
        for l in open(env):
            if "=" in l and not l.startswith("#"):
                k, v = l.strip().split("=", 1); os.environ.setdefault(k, v.strip().strip('"'))
    url, key = os.environ.get("VF_DRIVE_URL"), os.environ.get("VF_DRIVE_KEY")
    if not url or not key:
        sys.exit("Falta VF_DRIVE_URL / VF_DRIVE_KEY (crie .drive.env na raiz do repo).")
    return url, key


def chamar(acao, **kw):
    url, key = config()
    r = requests.post(url, data=json.dumps({"acao": acao, "chave": key, **kw}),
                      headers={"Content-Type": "text/plain"}, timeout=120, allow_redirects=True)
    r.raise_for_status()
    d = r.json()
    if isinstance(d, dict) and d.get("erro"):
        sys.exit("Drive: " + d["erro"])
    return d


def limpa(t):
    t = unicodedata.normalize("NFC", t.strip().lower())
    t = re.sub(r"[\\/:*?\"<>|]", "", t)
    return re.sub(r"\s+", " ", t)[:60]


def nomes(lista, tema, cortes=None, modelo=False):
    todos = " | ".join(f["nome"] for k in lista for f in lista[k])
    nums = [int(m) for m in re.findall(r"video\s+(\d+)", todos, re.I)]
    nn = f"{(max(nums) if nums else 0) + 1:02d}"
    out = {"numero": nn, "originais": f"Video {nn} - {limpa(tema)}.mp4"}
    if modelo:
        out["modelos"] = f"Video {nn} - {limpa(tema)}.mp4"
    out["editados"] = ([f"Video {nn}-{i} - {limpa(t)}.mp4" for i, t in enumerate(cortes.split("|"), 1)]
                       if cortes else [f"Video {nn} - {limpa(tema)}.mp4"])
    return out


def enviar(arquivo, pasta, nome, substituir=False):
    tam = os.path.getsize(arquivo)
    antigos = []
    if substituir:
        antigos = [f for f in chamar("listar")[pasta] if f["nome"] == nome]
    s = chamar("sessao", pasta=pasta, nome=nome, tamanho=tam, mime="video/mp4")
    if not s.get("url"):
        sys.exit(f"Nao abriu sessao de upload: {s}")
    with open(arquivo, "rb") as fh:
        ini = 0
        while ini < tam:
            parte = fh.read(CHUNK)
            fim = ini + len(parte) - 1
            r = requests.put(s["url"], data=parte, headers={"Content-Range": f"bytes {ini}-{fim}/{tam}"}, timeout=600)
            if r.status_code not in (200, 201, 308):
                sys.exit(f"Upload falhou ({r.status_code}): {r.text[:300]}")
            ini = fim + 1
            print(f"  {min(100, ini * 100 // tam)}%", flush=True)
    f = r.json()
    for a in antigos:
        chamar("lixeira", id=a["id"])
    print(json.dumps({"ok": True, "id": f.get("id"), "nome": f.get("name"), "pasta": pasta,
                      "substituidos": len(antigos)}, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("listar")
    n = sub.add_parser("nomes"); n.add_argument("--tema", required=True); n.add_argument("--cortes"); n.add_argument("--modelo", action="store_true")
    e = sub.add_parser("enviar"); e.add_argument("arquivo"); e.add_argument("--pasta", required=True, choices=["editados", "originais", "modelos"])
    e.add_argument("--nome", required=True); e.add_argument("--substituir", action="store_true")
    a = ap.parse_args()
    if a.cmd == "listar":
        print(json.dumps(chamar("listar"), ensure_ascii=False, indent=2))
    elif a.cmd == "nomes":
        print(json.dumps(nomes(chamar("listar"), a.tema, a.cortes, a.modelo), ensure_ascii=False, indent=2))
    else:
        enviar(a.arquivo, a.pasta, a.nome, a.substituir)


if __name__ == "__main__":
    main()
