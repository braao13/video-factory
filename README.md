# video-factory

Sistema de edição de vídeo curto (TikTok / Reels / Shorts) operado pelo Claude.
Cada vídeo vira um `projeto.json`; o código fica aqui e não é reescrito a cada conversa.

## Fluxo

```
bash setup.sh                                   # 1x por sessão (~1-2 min)
python3 pipeline/analisar.py video.mp4 saida/   # raio-x: luz, fala, mosaico de quadros
python3 pipeline/transcrever.py video.mp4 saida/palavras.json --lang pt
# monta projetos/<nome>.json
python3 pipeline/base.py projetos/<nome>.json saida/<nome>/   # trecho, silêncio, velocidade, cor, layout, áudio
# camadas (legenda, título, emojis, zoom...) -> remotion/   [bloco 2]
```

## Pastas

| Pasta | O que tem |
|---|---|
| `pipeline/` | scripts Python + FFmpeg |
| `looks/` | presets de cor (ver `looks/LEIAME.md`) |
| `estilos/` | presets de legenda, título, emojis [bloco 2] |
| `remotion/` | template de camadas que lê o projeto.json [bloco 2] |
| `projetos/` | um .json por vídeo editado (histórico, reabrir e ajustar) |

Vídeos e músicas NÃO entram no repositório (vêm por anexo).
