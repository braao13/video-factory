# Estilos de camada

`legenda/` e `titulo/`: presets lidos pelo `pipeline/render.py`.
No projeto.json, use pelo nome do arquivo (sem .json) e, se quiser, sobrescreva campos com `ajustes`:

```json
"legenda": {"estilo": "amarela-impacto", "ajustes": {"tamanho": 80}, "cores_palavras": {"#FF3B3B": ["medo"]}}
```

Para criar um estilo novo: copie um arquivo, troque o nome e os valores.
