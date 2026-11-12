---
name: "video-toolkit"
description: "Use when the user wants to make, edit, cut, caption or transcribe video in this cloud workspace. It is the engine behind /corte and /edicao and runs on the user's video-factory GitHub repo."
---

# video-toolkit: the video-factory engine

All the code lives in the private repo **braao13/video-factory**. Do not rewrite code that already exists there: every video becomes a `projetos/<nome>.json` file, and every adjustment means editing that JSON and rendering again.

## 1. Open the repo (once per session)

1. Call `add_repo` with owner `braao13`, repo `video-factory` and access `push`.
2. Clone it: `git clone --depth 1 https://github.com/braao13/video-factory /home/claude/video-factory`.
3. Call `register_repo_root` on that directory, then follow the repo's `CLAUDE.md`, which holds the rules and the order of the steps.
4. Run `cd /home/claude/video-factory && bash setup.sh` (about 1-2 min). Add `--sem-whisper` when the video has no speech.

If `add_repo` fails, tell the user the GitHub connection needs to be reconnected (claude.ai Settings, Connectors) and stop.

## 2. Pipeline (details in the repo's CLAUDE.md and docstrings)

- `pipeline/analisar.py <video> saida/<nome>/`: duration, light, saturation, volume, whether there is speech, plus a frame mosaic in `folha.jpg`.
- `pipeline/transcrever.py <video> saida/<nome>/palavras_orig.json --lang pt [--inicio --fim]`: per-word timestamps (Whisper small int8 model from npm, installed by setup.sh).
- `pipeline/base.py projetos/<nome>.json saida/<nome>/`: excerpt, silence cutting, speed, look, brightness, 9:16 layout, audio (voice, music with ducking, -14 LUFS) and caption corrections.
- `pipeline/render.py projetos/<nome>.json saida/<nome>/ [--quadros 2,15,30 | --previa]`: draws the Remotion layers (caption, title, emojis, zoom, flash, slow zoom, beat pulse, progress bar).
- Presets: `looks/` (color) and `estilos/legenda`, `estilos/titulo`. The saved files are a minimum, not a limit. Propose a new preset when a video calls for one, and save it in the repo if the user approves.
- Use the files in `projetos/` as models for the JSON.

## 3. Quick review

Use `--quadros` (a few seconds) to show the result before the final render, which takes about 3-5 min per minute of video. Send the finished video with SendUserFile.

## 4. Commit

After each delivery the user approves, commit the `projetos/<nome>.json` and any new presets, then run `git fetch origin main` and push. Videos and music never go into git.

## 5. Extra resources (only if the repo lacks the feature)

- Official Remotion guidance: `git clone --depth 1 https://github.com/remotion-dev/skills`, then read `skills/remotion-best-practices/SKILL.md` before adding a new kind of layer to the template.
- HyperFrames (prebuilt HTML blocks): `git clone --depth 1 https://github.com/heygen-com/hyperframes`, then render with `PUPPETEER_EXECUTABLE_PATH=$VF_CHROME PRODUCER_HEADLESS_SHELL_PATH=$VF_CHROME npx -y hyperframes render -o out.mp4 --workers 1 --no-browser-gpu`.
- Remotion here always needs `--browser-executable=$VF_CHROME`, because the browser download is blocked. setup.sh writes `VF_CHROME` to `.env.sh`.

## 6. Known limits here

- YouTube, Vimeo and most video sites are blocked, so yt-dlp does not work here. The user downloads the video at br.vidssave.com and attaches it.
- HuggingFace is blocked. `setup.sh` already gets the Whisper model from npm.
- Without a GPU, the final render takes minutes.

## 7. Rule

On someone else's video, never add mirroring, noise or any edit meant to dodge copyright detection.