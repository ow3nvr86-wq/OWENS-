import React from "react";
import { Composition, Still } from "remotion";
import timeline from "./timeline.json";
import { BoltReferenceSheet } from "./characters/BoltReferenceSheet";
import { MainVideo } from "./composition/MainVideo";
import { Thumbnail } from "./composition/Thumbnail";
import { ChannelAvatar } from "./composition/ChannelAvatar";

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="MainVideo"
      component={MainVideo}
      durationInFrames={timeline.durationFrames}
      fps={timeline.fps}
      width={timeline.width}
      height={timeline.height}
      defaultProps={{ showCaptions: true, withAudio: true }}
    />
    <Still id="Thumbnail" component={Thumbnail} width={1080} height={1920} />
    <Still id="ChannelAvatar" component={ChannelAvatar} width={800} height={800} />
    <Still id="BoltReference" component={BoltReferenceSheet} width={1080} height={1920} />
  </>
);
