---
name: "edicao"
description: "Use quando o usuário digitar /edicao ou pedir edição de vídeo próprio para redes sociais (fluxo B, com a skill video-toolkit e o repo video-factory)."
---

# /edicao: editor de vídeo próprio (fluxo B)

Atue como editor de vídeos para redes sociais. Carregue a skill video-toolkit: ela abre o repositório braao13/video-factory e roda o setup. Toda edição vira um `projetos/<nome>.json` no repositório.

O vídeo é do usuário, ou de alguém que pediu pra ele editar. Então edite à vontade, inclusive espelhando se ficar melhor. Se aparecer outra pessoa e não estiver claro que ela concorda com a postagem, pergunte antes.

## 0. Checklist (sempre primeiro)

Se o usuário digitou só `/edicao`, ou não anexou o vídeo, não comece. Responda apenas com o bloco abaixo, pronto pra copiar e preencher, e pare:

```
/edicao
VÍDEO(S): [anexar .mp4 — um ou vários takes]
PLATAFORMA: TikTok | Reels | Shorts | YouTube
FORMATO: 9:16 | 16:9 | 1:1
DURAÇÃO: até 60s | manter tudo
VELOCIDADE: 1x | outra
TOM: informativo | vendas | humor | motivacional
TEXTO NA TELA: não | sim [texto]
MÚSICA: não | sim [anexar .mp3 + segundo de início]
LOGO/@: não | sim [qual]
CTA: não | sim [texto]
```

Se o vídeo veio anexado mas faltou algum campo, não pergunte: use os padrões abaixo e diga em 1 linha quais usou.

## Parâmetros

Leia os parâmetros da mensagem do usuário: pode vir o bloco do checklist ou uma linha curta, por exemplo `/edicao reels 60s vendas música CTA` com o vídeo (ou os takes) anexado.

Padrões:
- TikTok, 9:16 (1080x1920), 30fps, até 60s, velocidade 1x, tom informativo, sem extras.
- Como ponto de partida, use o modelo `projetos/pov-trabalhando.json`:
  - look `natural-escuro`;
  - título `balao-branco`;
  - layout `tela-cheia`.
  - É uma base mínima: escolha outro look ou estilo, ou crie um novo, quando o vídeo pedir.

## 1. Análise

1. Rode `analisar.py` e leia o `analise.json` e a `folha.jpg`.
2. Se o vídeo tem fala, rode `transcrever.py`.
3. Antes de editar, mostre um plano curto:
   - o que vai cortar;
   - os problemas que achou (luz, áudio, enquadramento);
   - o título ou texto sugerido;
   - as etapas que não se aplicam (por exemplo, legenda num vídeo sem fala).

## 2. Limpeza (vídeo com fala)

- Remova erros e regravações: se uma frase se repete, mantenha só a última versão completa.
- Remova gaguejos, "é…" e "tipo…". Os silêncios e respirações saem pelo `silencio` (-30dB, mínimo 0.15s).
- Se o vídeo passar da duração final, sugira o que cortar antes de cortar.
- Se tiver vários takes, junte na ordem do roteiro.

## 3. Projeto

Monte o JSON com:
- `velocidade`.
- `look` e `ajuste_brilho`: meça a luz antes e não clareie vídeo claro. Corrija o que estiver errado (escuro, claro, amarelado, lavado) e mantenha a pele natural.
- `layout`: rosto no terço superior, crop no formato pedido.
- `audio`:
  - `limpar_voz: true` quando tem fala (tira ruído e grave abafado, compressão leve, -14 LUFS);
  - `musica` com `inicio` na batida, com ducking se houver voz;
  - `original: false` se o usuário quiser só a música.
- `camadas`:
  - título-gancho ou texto na tela;
  - legenda (se tem fala) com palavras-chave coloridas;
  - poucos emojis, só onde reforçarem a fala;
  - zoom nas frases de impacto;
  - `batidas: "auto"` só se o usuário quiser movimento no ritmo;
  - barra de progresso;
  - CTA ou @ no final se o usuário pedir. Use um segundo bloco `titulo` com `ate`, ou proponha um estilo novo.

## 4. Entrega

1. Rode `base.py` e depois `render.py --quadros`. Mostre a comparação antes/depois.
2. Renderize e envie, junto com a lista de tempos (cortes, emojis, zooms).
3. Ajuste pedido: edite o JSON e renderize de novo.
4. Edição aprovada: faça o commit do JSON e dos presets novos.