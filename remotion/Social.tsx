import React from 'react';
import {AbsoluteFill, interpolate, OffthreadVideo, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

const SRC_W = 464;
const SRC_H = 688;

export const Social: React.FC<{caption: string}> = ({caption}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames, width} = useVideoConfig();

  const fade = Math.min(
    interpolate(frame, [0, 8], [0, 1], {extrapolateRight: 'clamp'}),
    interpolate(frame, [durationInFrames - 10, durationInFrames], [1, 0], {extrapolateLeft: 'clamp'}),
  );
  // slow push-in on the main frame
  const zoom = interpolate(frame, [0, durationInFrames], [1, 1.06]);
  const cap = spring({frame: frame - 24, fps, config: {damping: 14}});
  const grade = 'contrast(1.08) saturate(1.12)';
  const mainH = (width * SRC_H) / SRC_W;

  return (
    <AbsoluteFill style={{backgroundColor: '#000', opacity: fade}}>
      {/* blurred copy fills the 9:16 frame so nothing is cropped */}
      <AbsoluteFill style={{filter: `blur(40px) brightness(0.55) ${grade}`, transform: 'scale(1.4)'}}>
        <OffthreadVideo src={staticFile('source.mp4')} muted style={{width: '100%', height: '100%', objectFit: 'cover'}} />
      </AbsoluteFill>
      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
        <div style={{width, height: mainH, overflow: 'hidden', filter: grade}}>
          <OffthreadVideo
            src={staticFile('source.mp4')}
            style={{width: '100%', height: '100%', transform: `scale(${zoom})`}}
          />
        </div>
      </AbsoluteFill>
      {/* vignette */}
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, rgba(0,0,0,0.55) 100%)'}} />
      {/* caption */}
      <div
        style={{
          position: 'absolute',
          bottom: 190,
          width: '100%',
          textAlign: 'center',
          direction: 'rtl',
          fontFamily: 'sans-serif',
          fontWeight: 800,
          fontSize: 76,
          color: 'white',
          textShadow: '0 4px 24px rgba(0,0,0,0.8)',
          opacity: cap,
          transform: `translateY(${(1 - cap) * 40}px)`,
        }}
      >
        {caption}
      </div>
    </AbsoluteFill>
  );
};
