import { useState, useEffect } from 'react';
import { MangaBubble, ComicSFX, CharacterExpression, ComicPanel, OnomatopoeiaPanel, SpeedLines, WordBubble } from './index';

export default function MangaDemo() {
  const [emotion, setEmotion] = useState<'happy' | 'calm' | 'angry'>('calm');
  const [showSFX, setShowSFX] = useState(false);
  const [showPanel, setShowPanel] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setShowSFX(true), 500);
    return () => clearTimeout(timer);
  }, [emotion]);

  const messages = [
    {
      text: "Hey there! I'm so happy to see you today! 🎉",
      emotion: 'happy' as const,
    },
    {
      text: "That sounds like a great plan! Let's do it! ✨",
      emotion: 'excited' as const,
    },
    {
      text: "I'm feeling a bit worried about this...",
      emotion: 'worried' as const,
    },
  ];

  return (
    <div className="p-8 bg-zinc-950 min-h-screen text-zinc-50">
      <div className="max-w-4xl mx-auto">
        {/* Title */}
        <h1 className="text-4xl font-bold mb-8 text-center manga-text manga-text-bold">
          🎨 Manga-Style Chat Demo 🎨
        </h1>

        {/* Emotion Selector */}
        <div className="mb-8 flex justify-center gap-4 flex-wrap">
          {['happy', 'calm', 'angry'].map((e) => (
            <button
              key={e}
              onClick={() => setEmotion(e as any)}
              className={`px-6 py-3 rounded-xl font-bold transition-all ${
                emotion === e
                  ? 'bg-white text-zinc-900 transform scale-105'
                  : 'bg-zinc-800 hover:bg-zinc-700'
              }`}
            >
              {e.charAt(0).toUpperCase() + e.slice(1)}
            </button>
          ))}
        </div>

        {/* Character Display */}
        <div className="flex items-center justify-center gap-6 mb-8">
          <CharacterExpression emotion={emotion} size="lg" />
          <span className="text-xl manga-text manga-text-handwritten">
            {emotion === 'happy' ? '😊 Happy!' : emotion === 'angry' ? '😠 Angry!' : '😌 Calm!'}
          </span>
        </div>

        {/* Speech Bubbles Demo */}
        <div className="space-y-6 mb-12">
          <h2 className="text-2xl font-bold mb-4">Speech Bubbles</h2>

          <div className="flex items-start gap-4">
            <MangaBubble direction="left" emotion={emotion}>
              "I'm feeling {emotion} today!"
            </MangaBubble>
            <MangaBubble direction="right" emotion="happy" tailColor="#FBBF24">
              "Great to hear! Let's chat! 😊"
            </MangaBubble>
          </div>

          <div className="flex items-start gap-4">
            <MangaBubble direction="left" emotion="calm" size="sm">
              "Just a calm message..."
            </MangaBubble>
            <MangaBubble direction="right" emotion="happy" size="lg">
              "This is a large bubble! Very exciting! 🎉"
            </MangaBubble>
          </div>
        </div>

        {/* Sound Effects Demo */}
        <div className="space-y-6 mb-12">
          <h2 className="text-2xl font-bold mb-4">Sound Effects</h2>

          <div className="bg-zinc-900 rounded-2xl p-8 relative overflow-hidden min-h-[200px]">
            <SpeedLines />

            <ComicSFX type={emotion === 'angry' ? 'THUD' : 'TING'} position="top-right" />
            <ComicSFX type="ZAP" position="bottom-left" delay={0.3} />

            <div className="relative z-10 flex items-center justify-center">
              <MangaBubble direction="center" emotion={emotion} size="lg">
                <span className="text-2xl">{emotion === 'happy' ? '🎉' : emotion === 'angry' ? '💥' : '✨'}</span>
                <p className="mt-2">
                  {emotion === 'happy' && "Sound effects are playing! BAM! POW!"}
                  {emotion === 'angry' && "ANGRY MODE ACTIVATED! THUD! BAM!"}
                  {emotion === 'calm' && "Calm vibes only... TING..."}
                </p>
              </MangaBubble>
            </div>
          </div>
        </div>

        {/* Comic Panel Demo */}
        <div className="space-y-6 mb-12">
          <h2 className="text-2xl font-bold mb-4">Comic Panels</h2>

          <ComicPanel layout="single">
            <div className="p-6">
              <h3 className="text-xl font-bold mb-2">Single Panel</h3>
              <p className="text-zinc-300">
                This is a full-width panel with rounded corners and comic styling.
              </p>
            </div>
          </ComicPanel>

          <div className="grid grid-cols-2 gap-6">
            <ComicPanel layout="horizontal">
              <div className="p-4">
                <h4 className="font-bold text-sm mb-2">Panel 1</h4>
                <p className="text-xs">Horizontal layout</p>
              </div>
            </ComicPanel>

            <ComicPanel layout="vertical">
              <div className="p-4">
                <h4 className="font-bold text-sm mb-2">Panel 2</h4>
                <p className="text-xs">Vertical layout</p>
              </div>
            </ComicPanel>
          </div>

          <ComicPanel layout="single" number={1}>
            <div className="p-6 bg-zinc-100 dark:bg-zinc-800 rounded-xl">
              <h3 className="font-bold text-lg mb-2">Panel #1</h3>
              <p className="text-sm">
                This panel has a numbered badge in the corner.
              </p>
            </div>
          </ComicPanel>
        </div>

        {/* Onomatopoeia Demo */}
        <div className="space-y-6 mb-12">
          <h2 className="text-2xl font-bold mb-4">Onomatopoeia</h2>

          <div className="grid grid-cols-2 gap-6">
            <ComicPanel layout="horizontal">
              <div className="p-6 flex flex-col items-center justify-center relative">
                <OnomatopoeiaPanel text="POW!" color="#EF4444" size="lg" overlay />
                <p className="mt-4 text-sm text-center">
                  Impact effect on panel
                </p>
              </div>
            </ComicPanel>

            <ComicPanel layout="vertical">
              <div className="p-6 flex flex-col items-center justify-center relative">
                <OnomatopoeiaPanel text="BAM!" color="#F59E0B" size="lg" overlay />
                <p className="mt-4 text-sm text-center">
                  Another impact effect
                </p>
              </div>
            </ComicPanel>
          </div>

          <div className="bg-zinc-900 rounded-2xl p-8 relative overflow-hidden min-h-[200px]">
            <SpeedLines />
            <ComicSFX type="SWISH" position="top-right" />
            <ComicSFX type="WHOOSH" position="bottom-left" delay={0.4} />

            <div className="relative z-10 flex items-center justify-center">
              <MangaBubble direction="center" emotion="calm" size="lg">
                <span className="text-4xl">💨</span>
                <p className="mt-2">
                  Speed lines and swoosh effects!
                </p>
              </MangaBubble>
            </div>
          </div>
        </div>

        {/* Word Bubbles Demo */}
        <div className="space-y-6 mb-12">
          <h2 className="text-2xl font-bold mb-4">Word Bubbles</h2>

          <div className="relative bg-zinc-900 rounded-2xl p-8 h-[200px]">
            <WordBubble position="top" bgColor="#FFFFFF" textColor="#1F2937">
              Narrator: This is a word bubble at the top!
            </WordBubble>

            <WordBubble position="bottom" bgColor="#F3E8FF" textColor="#7C3AED">
              Character: And this is a bubble at the bottom!
            </WordBubble>

            <WordBubble position="left" bgColor="#DBEAFE" textColor="#1E40AF">
              Character: Left side bubble!
            </WordBubble>

            <WordBubble position="right" bgColor="#DCFCE7" textColor="#166534">
              Character: Right side bubble!
            </WordBubble>

            <WordBubble position="corner" bgColor="#FEE2E2" textColor="#991B1B">
              Storyteller
            </WordBubble>
          </div>
        </div>

        {/* Character Emotions Demo */}
        <div className="space-y-6">
          <h2 className="text-2xl font-bold mb-4">Character Expressions</h2>

          <div className="grid grid-cols-4 gap-4">
            {['happy', 'sad', 'angry', 'shock'].map((e) => (
              <ComicPanel key={e} layout="horizontal" number={1}>
                <div className="p-4 flex flex-col items-center justify-center gap-2">
                  <CharacterExpression emotion={e as any} size="lg" />
                  <span className="text-xs font-bold capitalize">{e}</span>
                </div>
              </ComicPanel>
            ))}
          </div>

          <div className="grid grid-cols-4 gap-4">
            {['calm', 'excited', 'worried', 'embarrassed'].map((e) => (
              <ComicPanel key={e} layout="horizontal" number={1}>
                <div className="p-4 flex flex-col items-center justify-center gap-2">
                  <CharacterExpression emotion={e as any} size="lg" />
                  <span className="text-xs font-bold capitalize">{e}</span>
                </div>
              </ComicPanel>
            ))}
          </div>
        </div>

        {/* Animation Control */}
        <div className="mt-12 text-center">
          <button
            onClick={() => setShowPanel(!showPanel)}
            className="px-8 py-4 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold rounded-xl hover:from-purple-500 hover:to-pink-500 transition-all transform hover:scale-105"
          >
            {showPanel ? 'Hide Demo' : 'Show Full Demo Panel'}
          </button>

          {showPanel && (
            <ComicPanel number={0} layout="single" className="mt-8">
              <div className="p-8 text-center">
                <h3 className="text-3xl font-bold mb-4 manga-text manga-text-bold">
                  🎭 Manga Chat Integration Ready! 🎭
                </h3>
                <p className="text-lg mb-6">
                  All manga components are working! You can now integrate them into your Chat.tsx component.
                </p>
                <div className="flex justify-center gap-4 flex-wrap">
                  <MangaBubble direction="left" emotion="happy">
                    "Ready to start!"
                  </MangaBubble>
                  <ComicSFX type="TING" position="top-right" />
                </div>
              </div>
            </ComicPanel>
          )}
        </div>

        <div className="mt-12 text-center text-zinc-500">
          <p>🎨 Explore all manga features and create amazing chat experiences!</p>
        </div>
      </div>
    </div>
  );
}
