import { loadFont } from "@remotion/fonts";
import { staticFile } from "remotion";

/** Approved production palette. */
export const C = {
  teal: "#258F83",
  tealLight: "#3DB5A6",
  tealDark: "#1B6C63",
  orange: "#F07836",
  orangeLight: "#FFA266",
  yellow: "#E8B844",
  navy: "#182438",
  navyDeep: "#0E1626",
  navyMid: "#22324D",
  white: "#FFFFFF",
  gold: "#FFD447",
  goldDeep: "#C9961C",
  amber: "#FFB43A",
  amberCore: "#FFF1B8",
  steel: "#6E7F96",
  steelLight: "#A3B2C6",
  steelDark: "#46556B",
  red: "#E8433A",
  redDark: "#A3241D",
  cash: "#5DBB73",
  cashDark: "#3B8A50",
  pink: "#FF6FA0",
  purple: "#7B5CE0",
} as const;

export const FONT_DISPLAY = "Luckiest Guy";
export const FONT_CAPTION = "Montserrat";

let fontsLoaded = false;
export const ensureFonts = () => {
  if (fontsLoaded) return;
  fontsLoaded = true;
  loadFont({ family: FONT_DISPLAY, url: staticFile("fonts/luckiest-guy-latin-400-normal.woff2"), weight: "400" });
  loadFont({ family: FONT_CAPTION, url: staticFile("fonts/montserrat-latin-900-normal.woff2"), weight: "900" });
};
