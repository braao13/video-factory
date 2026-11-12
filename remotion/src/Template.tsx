import React from 'react';
import {
  AbsoluteFill, OffthreadVideo, staticFile, useCurrentFrame, useVideoConfig,
  interpolate, spring, Easing, Sequence,
} from 'remotion';
import '@fontsource/montserrat/800.css';
import '@fontsource/montserrat/900.css';

// ---------- tipos ----------
type Palavra = {w: string; s: number; e: number};
type EstiloLegenda = {
  fonte: string; peso: number; tamanho: number; caixa_alta: boolean; max_palavras: number;
  cor: string; cor_ativa: string; escala_ativa: number; rotacao_ativa: number;
  contorno: number; cor_contorno: string; sombra: string;
  fundo?: string | null; raio_fundo?: number; opacidade_inativa?: number; y: number; pausa_quebra: number;
};
type EstiloTitulo = {
  tipo: 'badge' | 'balao' | 'tarja';
  fonte: string; peso: number; tamanho: number; cor: string; fundo: string; cor_destaque?: string;
  raio: number; rotacao: number; y: number; sub_tamanho?: number; sub_cor?: string; sub_fundo?: string;
};
type TextoCfg = {estilo: EstiloTitulo; texto: string; destaque?: string; subtitulo?: string; de?: number; ate?: number; y?: number};
type Emoji = {t: number; e: string; dur?: number; x?: number; y?: number; tam?: number};
export type Props = {
  info: {duracao: number; fps: number; largura: number; altura: number};
  video: string;               // caminho dentro de public/
  palavras?: Palavra[];
  camadas: {
    legenda?: {estilo: EstiloLegenda; cores_palavras?: Record<string, string[]>; y?: number} | null;
    titulo?: TextoCfg | null;
    cta?: (TextoCfg & {duracao?: number}) | null;   // texto final; aparece nos ultimos `duracao` s (padrao 3)
    emojis?: Emoji[];
    zooms?: number[]; zoom_forca?: number;
    flashes?: number[];
    zoom_lento?: number;        // ex.: 0.05 = 1 -> 1.05 ao longo do video
    batidas?: number[]; pulso_forca?: number;
    progresso?: {cor: string; altura?: number} | null;
  };
};

const limpa = (t: string) => t.toLowerCase().replace(/[.,?!;:"]/g, '');

// ---------- legenda ----------
function paginar(ws: Palavra[], max: number, pausa: number): Palavra[][] {
  const pages: Palavra[][] = [];
  let cur: Palavra[] = [];
  ws.forEach((w, i) => {
    cur.push(w);
    const nx = ws[i + 1];
    const gap = nx ? nx.s - w.e : 9;
    if (cur.length >= max || /[.,?!]$/.test(w.w) || gap > pausa) { pages.push(cur); cur = []; }
  });
  if (cur.length) pages.push(cur);
  return pages;
}

const Legenda: React.FC<{ws: Palavra[]; cfg: NonNullable<Props['camadas']['legenda']>}> = ({ws, cfg}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = f / fps;
  const E = cfg.estilo;
  const pages = React.useMemo(() => paginar(ws, E.max_palavras, E.pausa_quebra), [ws, E.max_palavras, E.pausa_quebra]);
  const corFixa = React.useMemo(() => {
    const m: Record<string, string> = {};
    Object.entries(cfg.cores_palavras ?? {}).forEach(([cor, lista]) => lista.forEach((p) => (m[limpa(p)] = cor)));
    return m;
  }, [cfg.cores_palavras]);
  const page = pages.find((pg, i) => {
    const fim = pages[i + 1] ? pages[i + 1][0].s : pg[pg.length - 1].e + 0.4;
    return t >= pg[0].s && t < fim;
  });
  if (!page) return null;
  const pin = spring({frame: f - Math.round(page[0].s * fps), fps, config: {damping: 12, stiffness: 220}});
  return (
    <div style={{position: 'absolute', top: cfg.y ?? E.y, width: '100%', display: 'flex', justifyContent: 'center',
      padding: '0 60px', boxSizing: 'border-box', transform: `scale(${0.85 + 0.15 * pin})`}}>
      <div style={{display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: `0 ${Math.round(E.tamanho * 0.4)}px`,
        background: E.fundo ?? 'transparent', borderRadius: E.raio_fundo ?? 0, padding: E.fundo ? '10px 28px' : 0}}>
        {page.map((w, i) => {
          const ativa = t >= w.s && (i === page.length - 1 || t < page[i + 1].s);
          const fixa = corFixa[limpa(w.w)];
          const txt = (E.caixa_alta ? w.w.toUpperCase() : w.w).replace(/[,.]$/, '');
          return (
            <span key={i} style={{
              display: 'inline-block', fontFamily: E.fonte, fontWeight: E.peso, fontSize: E.tamanho, lineHeight: 1.15,
              color: ativa ? (fixa ?? E.cor_ativa) : (fixa ?? E.cor),
              opacity: ativa ? 1 : (E.opacidade_inativa ?? 1),
              transform: ativa ? `scale(${E.escala_ativa}) rotate(${E.rotacao_ativa}deg)` : 'none',
              WebkitTextStroke: E.contorno ? `${E.contorno}px ${E.cor_contorno}` : undefined,
              paintOrder: 'stroke fill', textShadow: E.sombra,
            }}>{txt}</span>
          );
        })}
      </div>
    </div>
  );
};

// ---------- titulo ----------
const Titulo: React.FC<{cfg: TextoCfg}> = ({cfg}) => {
  const f0 = useCurrentFrame();
  const {fps} = useVideoConfig();
  const E = cfg.estilo;
  const f = f0 - Math.round((cfg.de ?? 0) * fps);
  const tin = spring({frame: f - 4, fps, config: {damping: 13, stiffness: 160}});
  const out = cfg.ate ? interpolate(f0 / fps, [cfg.ate - 0.25, cfg.ate], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}) : 1;
  if (f < 0) return null;
  const partes = cfg.destaque ? cfg.texto.split(cfg.destaque) : [cfg.texto];
  const caixa: React.CSSProperties = {
    display: 'inline-block', background: E.fundo, color: E.cor, fontFamily: E.fonte, fontWeight: E.peso,
    fontSize: E.tamanho, lineHeight: 1.2, padding: '14px 34px', borderRadius: E.raio, textAlign: 'center',
    transform: `rotate(${E.rotacao}deg)`, boxShadow: '0 10px 30px rgba(0,0,0,.3)', maxWidth: 880,
  };
  if (E.tipo === 'tarja') Object.assign(caixa, {width: '100%', maxWidth: 'none', borderRadius: 0, boxSizing: 'border-box', transform: 'none'});
  return (
    <div style={{position: 'absolute', top: cfg.y ?? E.y, width: '100%', textAlign: 'center', opacity: tin * out,
      transform: `translateY(${(1 - tin) * (E.tipo === 'badge' ? -160 : 40)}px)`}}>
      <div style={caixa}>
        {partes.map((p, i) => (
          <React.Fragment key={i}>
            {p}
            {i < partes.length - 1 && <span style={{color: E.cor_destaque ?? E.cor}}>{cfg.destaque}</span>}
          </React.Fragment>
        ))}
      </div>
      {cfg.subtitulo && (
        <div style={{marginTop: 14}}>
          <span style={{background: E.sub_fundo ?? '#111', color: E.sub_cor ?? 'white', fontFamily: E.fonte, fontWeight: 800,
            fontSize: E.sub_tamanho ?? 46, padding: '8px 24px', borderRadius: 12}}>{cfg.subtitulo}</span>
        </div>
      )}
    </div>
  );
};

// ---------- emoji ----------
const Sticker: React.FC<Required<Pick<Emoji, 'e' | 'x' | 'y' | 'dur' | 'tam'>> & {r: number}> = ({e, x, y, dur, tam, r}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const pop = spring({frame: f, fps, config: {damping: 9, stiffness: 180}});
  const out = interpolate(f, [dur * fps - 6, dur * fps], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <div style={{position: 'absolute', left: x - tam / 2, top: y - tam / 2 + Math.sin(f / 6) * 8, width: tam, height: tam,
      fontSize: tam * 0.77, lineHeight: `${tam}px`, textAlign: 'center', fontFamily: 'Noto Color Emoji',
      transform: `scale(${pop * out}) rotate(${r + Math.sin(f / 9) * 4}deg)`, filter: 'drop-shadow(0 10px 18px rgba(0,0,0,.45))'}}>{e}</div>
  );
};

// ---------- composicao ----------
export const Template: React.FC<Props> = ({video, palavras = [], camadas: C}) => {
  const f = useCurrentFrame();
  const {fps, durationInFrames, width} = useVideoConfig();
  const t = f / fps;

  const pico = (lista: number[] | undefined, a: number, b: number, c: number) =>
    Math.max(0, ...(lista ?? []).map((p) => interpolate(t, [p - a, p + b, p + c], [0, 1, 0],
      {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)})));
  const zoom = (1 + (C.zoom_forca ?? 0.12) * pico(C.zooms, 0, 0.08, 0.7))
    * (1 + (C.pulso_forca ?? 0.035) * pico(C.batidas, 0, 0.06, 0.45))
    * interpolate(f, [0, durationInFrames], [1, 1 + (C.zoom_lento ?? 0)]);
  const flash = 0.85 * pico(C.flashes, 0.04, 0, 0.25);

  return (
    <AbsoluteFill style={{backgroundColor: 'black'}}>
      <AbsoluteFill style={{transform: `scale(${zoom})`, transformOrigin: '50% 40%'}}>
        <OffthreadVideo src={staticFile(video)} />
      </AbsoluteFill>

      {C.titulo && <Titulo cfg={C.titulo} />}
      {C.cta && <Titulo cfg={{...C.cta, de: C.cta.de ?? Math.max(0, durationInFrames / fps - (C.cta.duracao ?? 3))}} />}

      {(C.emojis ?? []).map((em, i) => (
        <Sequence key={i} from={Math.round(em.t * fps)} durationInFrames={Math.round((em.dur ?? 1.8) * fps)}>
          <Sticker e={em.e} dur={em.dur ?? 1.8} tam={em.tam ?? 220}
            x={em.x ?? (i % 2 === 0 ? width - 210 : 210)} y={em.y ?? 540} r={i % 2 === 0 ? 10 : -10} />
        </Sequence>
      ))}

      {C.legenda && palavras.length > 0 && <Legenda ws={palavras} cfg={C.legenda} />}

      <AbsoluteFill style={{backgroundColor: 'white', opacity: flash}} />

      {C.progresso && (
        <div style={{position: 'absolute', bottom: 0, left: 0, height: C.progresso.altura ?? 12,
          width: `${(f / durationInFrames) * 100}%`, background: C.progresso.cor}} />
      )}
    </AbsoluteFill>
  );
};
