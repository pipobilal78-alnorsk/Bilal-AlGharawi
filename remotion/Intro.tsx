import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';

export const Intro: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();

  const title = spring({frame, fps, config: {damping: 12}});
  const subtitle = interpolate(frame, [40, 70], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const fadeOut = interpolate(frame, [durationInFrames - 20, durationInFrames], [1, 0], {extrapolateLeft: 'clamp'});
  const bg = interpolate(frame, [0, durationInFrames], [0, 60]);

  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(${135 + bg}deg, #0f766e, #1e3a8a)`,
        justifyContent: 'center',
        alignItems: 'center',
        fontFamily: 'sans-serif',
        color: 'white',
        direction: 'rtl',
        opacity: fadeOut,
      }}
    >
      <div style={{fontSize: 110, fontWeight: 800, transform: `scale(${title})`}}>دليل الكويت الشامل</div>
      <div style={{fontSize: 44, marginTop: 24, opacity: subtitle, transform: `translateY(${(1 - subtitle) * 30}px)`}}>
        اكتشف الكويت
      </div>
    </AbsoluteFill>
  );
};
