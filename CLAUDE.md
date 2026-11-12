# video-factory — instruções para o Claude

Sistema de edição de vídeos curtos do Abraão. Responder em português do Brasil.

## Regras
- Todo vídeo vira `projetos/<nome>.json`. Ajuste pedido pelo usuário = editar o JSON e re-renderizar, não reescrever código.
- Código novo só quando faltar um recurso; se criar, deixe genérico (parâmetro no JSON), nunca específico de um vídeo.
- Looks em `looks/`, estilos em `estilos/`. Os aprovados são base mínima, não limite: proponha novos quando o vídeo pedir, e salve como preset se o usuário aprovar.
- Medir antes de ajustar cor (`analisar.py`). Não clarear vídeo claro.
- Vídeos/músicas nunca entram no git. No projeto.json, `entrada`/`musica.arquivo` apontam para o anexo da sessão.
- Não fazer espelhamento/ruído pra driblar direitos autorais em vídeo de terceiros.
- Commit ao fim de cada entrega aprovada (projeto.json + presets novos).

## Ordem
1. `bash setup.sh` (1x por sessão; `--sem-whisper` se o vídeo não tem fala)
2. `python3 pipeline/analisar.py <video> saida/<nome>/` -> ler analise.json e folha.jpg
3. `python3 pipeline/transcrever.py <video> saida/<nome>/palavras_orig.json` (se tem fala)
4. Montar `projetos/<nome>.json` (ver exemplos em projetos/ e docstrings de base.py/render.py)
5. `python3 pipeline/base.py projetos/<nome>.json saida/<nome>/`
6. `python3 pipeline/render.py projetos/<nome>.json saida/<nome>/ --quadros 2,15,30` -> conferir
7. `python3 pipeline/render.py projetos/<nome>.json saida/<nome>/` -> entregar com SendUserFile
8. Após o ok do usuário: salvar no Drive (regras em `drive.json`).
   - `.drive.env` não está no git: peça `VF_DRIVE_URL` e `VF_DRIVE_KEY` ao usuário (ou leia das instruções do projeto) e crie o arquivo.
   - `python3 pipeline/drive.py nomes --tema "..." [--cortes "a|b"] [--modelo]` -> nomes com o número certo.
   - `python3 pipeline/drive.py enviar <arquivo> --pasta originais|modelos|editados --nome "Video NN - tema.mp4"` (ajuste de vídeo já salvo: `--substituir`).
   - Guardar `"drive": "Video NN"` no projeto.json e fazer o commit.
