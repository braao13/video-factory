#!/usr/bin/env bash
# Instala tudo que o video-factory precisa. Uso: bash setup.sh [--sem-remotion] [--sem-whisper]
set -e
VF_DIR="$(cd "$(dirname "$0")" && pwd)"
SEM_REMOTION=0; SEM_WHISPER=0
for a in "$@"; do
  case $a in --sem-remotion) SEM_REMOTION=1;; --sem-whisper) SEM_WHISPER=1;; esac
done

echo "== ffmpeg"; ffmpeg -version | head -1

echo "== python"
pip install --break-system-packages -q faster-whisper librosa Pillow 2>&1 | grep -v -i warning || true

if [ $SEM_WHISPER = 0 ]; then
  echo "== modelo whisper (small int8, via npm porque o HuggingFace e bloqueado)"
  M="$HOME/.cache/vf-whisper-small"
  if [ ! -f "$M/model.bin" ]; then
    T=$(mktemp -d); mkdir -p "$M"
    ( cd "$T" && for i in 0 1 2 3; do npm pack @skillninja/shortmovie-telop-model-p$i --silent >/dev/null; done
      for f in *.tgz; do mkdir -p "x/${f%.tgz}"; tar -xzf "$f" -C "x/${f%.tgz}"; done )
    P="$T/x/skillninja-shortmovie-telop-model-p"
    cat ${P}0-1.0.0/package/model.bin.part0 ${P}1-1.0.0/package/model.bin.part1 \
        ${P}2-1.0.0/package/model.bin.part2 ${P}3-1.0.0/package/model.bin.part3 > "$M/model.bin"
    cp ${P}0-1.0.0/package/{tokenizer.json,vocabulary.json,config.json,preprocessor_config.json} "$M/"
    rm -rf "$T"
  fi
  echo "ca732cb1379efc49417d028465f543d83a39de2c61f3027678de103dc404ce73  $M/model.bin" | sha256sum -c -
fi

if [ $SEM_REMOTION = 0 ]; then
  echo "== remotion"
  ( cd "$VF_DIR/remotion" && npm install --silent --no-audit --no-fund )
fi

CHROME=$(ls /opt/pw-browsers/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell 2>/dev/null | head -1 || true)
[ -z "$CHROME" ] && CHROME=$(command -v chromium || command -v google-chrome || true)
echo "export VF_CHROME=\"$CHROME\"" > "$VF_DIR/.env.sh"
echo "== ok. Chrome: ${CHROME:-NAO ENCONTRADO}"
