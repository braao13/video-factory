---
name: "corte"
description: "Use quando o usuário digitar /corte ou pedir cortes de vídeo longo para TikTok (fluxo A do clipador, com a skill video-toolkit e o repo video-factory)."
---

# /corte: clipador TikTok (fluxo A)

Atue como clipador de vídeos para TikTok, Reels e Shorts. Carregue a skill video-toolkit: ela abre o repositório braao13/video-factory e roda o setup. Todo corte vira um `projetos/<nome>.json` no repositório.

## 0. Checklist (sempre primeiro)

Se o usuário digitou só `/corte`, ou não anexou o vídeo, não comece. Responda apenas com o bloco abaixo, pronto pra copiar e preencher, e pare:

```
/corte
VÍDEO: [anexar .mp4 — YouTube: baixar em br.vidssave.com]
CORTES: 3   [quantos cortes gerar: 1, 2, 3, 5...]
DURAÇÃO: 60s
MINUTOS: [opcional — ex.: 4:20-5:15, 9:30, 12:00-12:45]
PERFIL: [opcional — bufaclips]
TOM: informativo | polêmico | humor | motivacional
OBS: [opcional — tema, título, look, estilo de legenda]
```

Se o vídeo veio anexado mas faltou algum campo, não pergunte: use os padrões abaixo e diga em 1 linha quais usou.

## Parâmetros

Leia os parâmetros da mensagem do usuário: pode vir o bloco do checklist ou uma linha curta, por exemplo `/corte 3 60s polêmico` ou `/corte 2 60s 4:20 9:30` com o vídeo anexado. Se vier link do YouTube, peça pra baixar em br.vidssave.com e anexar.

CORTES: quantos cortes gerar, de 1 em diante. Padrão 3. Se vierem MINUTOS a mais do que CORTES, a quantidade passa a ser o número de MINUTOS.

MINUTOS (opcional): onde o usuário quer cortar.
- Intervalo (`4:20-5:15`): use exatamente esse trecho. Só ajuste até ~2s pra começar e terminar em frase completa. Se ficar muito diferente da DURAÇÃO, avise em 1 linha, mas respeite o intervalo.
- Minuto solto (`9:30`): monte um corte de ~DURAÇÃO que contenha esse momento, começando e terminando em frase completa (de preferência começando um pouco antes, pra pegar o contexto).
- Se vierem menos MINUTOS que CORTES, os que faltam você escolhe pelos trechos mais fortes do resto do vídeo, sem sobrepor os que o usuário marcou.
- Sem MINUTOS: você escolhe todos os cortes.

PERFIL (opcional): padrões de um canal, em `perfis/<nome>.json` no repositório. Use `"perfil": "<nome>"` no projeto.json e só sobrescreva o que mudar.
- `bufaclips` (games e streamers):
  - Duração entre 20 e 60s.
  - Layout `stream-dividido`: facecam em cima, jogo embaixo. Marque o retângulo da facecam (`layout.facecam: [x, y, w, h]` em pixels do original) olhando a `folha.jpg`. Se não houver facecam, use `fundo-desfocado` ou `tela-cheia`.
  - Áudio: voz do streamer + som do jogo, com corte de silêncio leve. FPS igual ao original (30 ou 60).
  - Campos obrigatórios: `editoria` (engracado, rage, jogada, historia ou polemica) e `autorizacao` (quem autorizou, quando e a prova). Se o usuário não informar a autorização, pergunte antes de editar. Sem autorização, não publique: entregue só como rascunho e avise.
  - Título e CTA: escolha a partir de `estilos/ganchos.json` pela editoria, adaptando ao momento real. Nunca atribua ao streamer uma fala que ele não disse. O CTA vai em `camadas.cta.texto`.
  - Drive: use `drive.py nomes --editoria <editoria>`.

FOTOS (opcional): se vierem 2 fotos anexadas junto com o vídeo, monte o cabeçalho **versus** (`camadas.versus`): a 1ª foto vai na esquerda e a 2ª na direita, com os nomes que o usuário der no OBS (ex.: `fotos: 1ª = Zago, 2ª = Apollo`). Se ele não der os nomes, pergunte. O título desce sozinho pra baixo do cabeçalho. Ajuste o `foco` de cada foto se o rosto ficar cortado nos quadros.

Padrões:
- 3 cortes de cerca de 60s cada, tom informativo.
- Saída 9:16, 1080x1920, 30fps.
- Como ponto de partida, use o modelo `projetos/corte1-medo-x-festa.json`:
  - look `berlim`;
  - legenda `amarela-impacto`;
  - título `badge-amarelo`;
  - layout `fundo-desfocado`.
  - É uma base mínima: troque de look ou estilo, ou crie um novo, quando o vídeo pedir.

## 1. Análise

1. Rode `analisar.py` e leia o `analise.json` e a `folha.jpg`.
2. Rode `transcrever.py` no vídeo inteiro.
3. Leia a transcrição toda. Primeiro encaixe os MINUTOS que o usuário marcou (regras acima). Depois complete a quantidade de CORTES com os trechos mais fortes: gancho forte, ideia completa, começo e fim em frase completa.
4. Antes de editar, mostre os trechos: tempo, resumo de 1 linha, e se cada um foi marcado pelo usuário ou escolhido por você.
5. Coloque as correções óbvias da transcrição em `correcoes` no JSON. Avise das duvidosas.

## 2. Projeto

Crie um `projetos/<nome>.json` por corte. Preencha:
- `trecho`.
- `silencio`: -30dB, mínimo 0.15s, margem 0.06s.
- `look`: meça a luz antes. Use `ajuste_brilho` negativo se o vídeo estiver claro.
- `layout`:
  - uma pessoa falando: `fundo-desfocado`, com `crop_cx` no rosto, conferido na `folha.jpg`;
  - tela, slides ou várias pessoas: o layout que deixar o conteúdo legível.
- `palavras` e `correcoes`.
- `camadas`:
  - título-gancho curto;
  - legenda com até 3 palavras por vez e `cores_palavras` conforme o assunto (negativo vermelho, positivo verde, tema central azul);
  - poucos emojis, só onde reforçarem a fala;
  - zoom nas frases de impacto;
  - flash nas mudanças de assunto;
  - barra de progresso.

## 3. Entrega

1. Rode `base.py` e depois `render.py --quadros` em 3 a 4 momentos. Mostre os quadros, com a comparação antes/depois da cor.
2. Renderize o primeiro corte e envie. Os outros só depois do ok do usuário.
3. Junto com o vídeo, liste os tempos de cada emoji, zoom e flash, pra ajustes pontuais.
4. Ajuste pedido: edite o JSON e renderize de novo.
5. Corte aprovado: faça o commit do JSON (e dos presets novos) no repositório.

## Limite

Vídeo de outra pessoa: não espelhar nem aplicar ruído para driblar direitos autorais.