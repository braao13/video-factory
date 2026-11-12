"""Carrega um projeto.json aplicando o perfil (perfis/<nome>.json) como padrao.

O projeto sempre vence o perfil; dicionarios sao mesclados em profundidade (camadas, audio, layout...).
"""
import json, os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def mesclar(base, cima):
    out = dict(base)
    for k, v in cima.items():
        out[k] = mesclar(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def carregar(caminho):
    P = json.load(open(caminho))
    if P.get("perfil"):
        perfil = json.load(open(os.path.join(RAIZ, "perfis", P["perfil"] + ".json")))
        perfil = {k: v for k, v in perfil.items() if not k.startswith("_")}
        P = mesclar(perfil, P)
    return P
