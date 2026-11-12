import React from 'react';
import {registerRoot, Composition} from 'remotion';
import {Template, Props} from './Template';

const Root: React.FC = () => (
  <Composition
    id="Projeto"
    component={Template}
    width={1080}
    height={1920}
    fps={30}
    durationInFrames={30}
    defaultProps={{} as Props}
    calculateMetadata={({props}) => ({
      durationInFrames: Math.max(1, Math.floor((props.info?.duracao ?? 1) * (props.info?.fps ?? 30))),
      fps: props.info?.fps ?? 30,
      width: props.info?.largura ?? 1080,
      height: props.info?.altura ?? 1920,
    })}
  />
);
registerRoot(Root);
