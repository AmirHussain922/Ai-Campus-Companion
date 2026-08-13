// Manga Components
export { MangaBubble } from './MangaBubble';
export type { MangaBubbleProps } from './MangaBubble';

export { ComicSFX, ZoomEffect, ShakeEffect, FlashEffect } from './ComicSFX';
export type { SFXType, ComicSFXProps } from './ComicSFX';

export {
  CharacterExpression,
  useCharacterExpression,
  useBlink,
} from './CharacterExpression';
export type { Emotion, CharacterExpressionProps } from './CharacterExpression';

export {
  ComicPanel,
  WordBubble,
  OnomatopoeiaPanel,
  SpeedLines,
} from './ComicPanel';
export type {
  ComicPanelProps,
  WordBubbleProps,
  OnomatopoeiaPanelProps,
  SpeedLinesProps,
} from './ComicPanel';

// Manga Theme
export * from './manga-theme.css';
