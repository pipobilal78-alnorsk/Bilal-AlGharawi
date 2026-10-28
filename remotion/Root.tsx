import React from 'react';
import {Composition} from 'remotion';
import {Intro} from './Intro';
import {Social} from './Social';

export const Root: React.FC = () => {
  return (
    <>
    <Composition
      id="Social"
      component={Social}
      durationInFrames={145}
      fps={24}
      width={1080}
      height={1920}
      defaultProps={{caption: 'هدوء ما قبل الغروب'}}
    />
    <Composition
      id="Intro"
      component={Intro}
      durationInFrames={150}
      fps={30}
      width={1280}
      height={720}
    />
    </>
  );
};
