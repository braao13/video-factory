# Looks de cor

Cada arquivo e um preset de cor aplicado pelo `pipeline/base.py`.
- `eq`: contrast / saturation / gamma / brightness do filtro eq do FFmpeg (1.0 = sem mudanca).
- `temperatura.k`: MENOR = mais quente (laranja), MAIOR = mais frio (azul). 6500 = neutro. `mix` = intensidade (0-1).
- `curves`: string do filtro curves do FFmpeg (opcional).
- `nitidez`: forca do unsharp (0 = desligado).

Ajuste fino por projeto: `ajuste_brilho` no projeto.json (ex.: -12 = 12% mais escuro).
Para criar um look novo: copie um arquivo, mude o nome e os valores.
