import { B, keys, ease } from "../lib/anim";
import { COURSE } from "./CourseWorld";

/** Bolt's x position along the course, 3s–14.55s (running phase). */
export const runX = (t: number) =>
  keys(t, [
    [B.launch, 540],
    [8.0, 1150, ease.inQuad],
    [B.hammer1Duck, 1650, ease.linear],
    [B.jumpTakeoff, 2300, ease.linear],
    [B.jumpLand, 3000, ease.linear],
    [B.hammer2NearMiss, 3600, ease.linear],
    [B.bridgeStep, 4500, ease.linear],
    [B.slip, 4690, ease.outQuad],
  ]);

/** Follow-camera used by the running scenes (lead room ahead of Bolt). */
export const followCam = (t: number) => ({ x: runX(t) + 190, y: 1010, zoom: 1.05 });

/** Hang position when Bolt grabs the final-platform lip with his right hand. */
export const HANG = { x: COURSE.final[0] - 58, y: COURSE.finalTop + 245 };
