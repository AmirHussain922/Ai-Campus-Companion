import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { episodeDetails } from "./storyData";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function getPersonalizedEpisodeDetails(episodeId: string, baseName: string, customName: string) {
  const details = episodeDetails[episodeId];
  if (!details) return null;
  
  if (!customName || baseName === customName) {
    return details;
  }

  const replaceName = (text: string) => text.split(baseName).join(customName);

  return {
    scenario: replaceName(details.scenario),
    backstory: replaceName(details.backstory),
    narration: replaceName(details.narration)
  };
}

export const companionColorClasses = {
  blue: {
    bg: "bg-blue-500",
    bgLight: "bg-blue-500/10",
    text: "text-blue-500",
    border: "border-blue-500/30",
    ring: "group-hover:ring-blue-500/50",
    glow: "shadow-[0_0_15px_rgba(59,130,246,0.3)]",
    glowStrong: "shadow-[0_0_30px_rgba(59,130,246,0.5)]",
  },
  pink: {
    bg: "bg-pink-500",
    bgLight: "bg-pink-500/10",
    text: "text-pink-500",
    border: "border-pink-500/30",
    ring: "group-hover:ring-pink-500/50",
    glow: "shadow-[0_0_15px_rgba(236,72,153,0.3)]",
    glowStrong: "shadow-[0_0_30px_rgba(236,72,153,0.5)]",
  },
  purple: {
    bg: "bg-purple-500",
    bgLight: "bg-purple-500/10",
    text: "text-purple-500",
    border: "border-purple-500/30",
    ring: "group-hover:ring-purple-500/50",
    glow: "shadow-[0_0_15px_rgba(168,85,247,0.3)]",
    glowStrong: "shadow-[0_0_30px_rgba(168,85,247,0.5)]",
  },
  red: {
    bg: "bg-rose-500",
    bgLight: "bg-rose-500/10",
    text: "text-rose-500",
    border: "border-rose-500/30",
    ring: "group-hover:ring-rose-500/50",
    glow: "shadow-[0_0_15px_rgba(244,63,94,0.3)]",
    glowStrong: "shadow-[0_0_30px_rgba(244,63,94,0.5)]",
  },
  cyan: {
    bg: "bg-cyan-500",
    bgLight: "bg-cyan-500/10",
    text: "text-cyan-500",
    border: "border-cyan-500/30",
    ring: "group-hover:ring-cyan-500/50",
    glow: "shadow-[0_0_15px_rgba(6,182,212,0.3)]",
    glowStrong: "shadow-[0_0_30px_rgba(6,182,212,0.5)]",
  }
};
