import { useState } from 'react';
import { MangaBubble, ComicSFX, CharacterExpression, useCharacterExpression, ComicPanel, OnomatopoeiaPanel, SpeedLines } from '../components/manga';
import { Send, Sparkles, Heart } from 'lucide-react';

export default function MangaChatDemo() {
  const [messages, setMessages] = useState([
    { id: 1, sender: 'user' as const, text: "Hey there! I'm so excited to chat! 😊✨" },
    { id: 2, sender: 'companion' as const, text: "Hello! I'm absolutely thrilled to see you too! What would you like to talk about?" },
    { id: 3, sender: 'user' as const, text: "Can you teach me how to code?" },
    { id: 4, sender: 'companion' as const, text: "Of course! Programming is amazing! Let's start with Python! 🚀" },
    { id: 5, sender: 'user' as const, text: "This is frustrating! I can't figure it out! 😠" },
    { id: 6, sender: 'companion' as const, text: "Don't worry, it's totally normal to feel this way! Let's break it down together. 🤝" },
    { id: 7, sender: 'user' as const, text: "I'm feeling so nervous about this test... what if I fail? 😰" },
    { id: 8, sender: 'companion' as const, text: "You've got this! You're going to do amazing! I believe in you! 💪" },
  ]);

  const [input, setInput] = useState("");

  const handleSend = () => {
    if (input.trim()) {
      setMessages([...messages, { id: messages.length + 1, sender: 'user' as const, text: input }]);
      setInput("");
    }
  };

  return (
    <div className="flex-1 flex flex-col bg-zinc-950 text-zinc-50 min-h-screen">
      {/* Header */}
      <header className="px-6 py-4 border-b border-zinc-800/50 bg-zinc-950/80 backdrop-blur-xl">
        <h1 className="text-2xl font-bold text-center">🎨 Manga-Style Chat Demo</h1>
        <p className="text-sm text-zinc-400 text-center mt-1">Emotion detection, speech bubbles, and SFX in action!</p>
      </header>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map((msg) => {
          const isUser = msg.sender === 'user';
          const emotion = isUser ? 'happy' : detectEmotion(msg.text);

          return (
            <div key={msg.id} className={cn("flex w-full", isUser ? "justify-end" : "justify-start")}>
              <div className={cn("flex max-w-[80%] items-end gap-3", isUser ? "flex-row-reverse" : "flex-row")}>
                {!isUser && (
                  <div className="flex flex-col items-end gap-1">
                    <CharacterExpression emotion={emotion} size="sm" blinkInterval={4000} />
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-xs font-bold">
                      AI
                    </div>
                  </div>
                )}

                <MangaBubble
                  direction={isUser ? "right" : "left"}
                  size="md"
                  emotion={emotion}
                  tailColor={isUser ? "#8B5CF6" : "#9333EA"}
                >
                  <div className="relative">
                    <p className="text-[15px] leading-relaxed">{msg.text}</p>

                    {/* SFX for excited emotions */}
                    {!isUser && emotion === 'excited' && (
                      <ComicSFX type="ZAP" position="top-right" delay={0.3} />
                    )}

                    {/* SFX for angry emotions */}
                    {!isUser && emotion === 'angry' && (
                      <ComicSFX type="THUD" position="top-left" delay={0.2} />
                    )}

                    {/* SFX for worried emotions */}
                    {!isUser && emotion === 'worried' && (
                      <ComicSFX type="SWISH" position="top-right" delay={0.4} />
                    )}

                    {/* SFX for shock emotions */}
                    {!isUser && emotion === 'shock' && (
                      <ComicSFX type="FLASH" position="bottom-left" delay={0.2} />
                    )}
                  </div>
                </MangaBubble>

                {isUser && (
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center text-xs font-bold">
                    You
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Input Area */}
      <div className="p-4 bg-zinc-950/80 backdrop-blur-xl border-t border-zinc-800/50">
        <div className="max-w-4xl mx-auto relative">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Type a message... Try: 'I'm so happy!', 'This is annoying!', 'I'm nervous!'"
              className="flex-1 bg-zinc-900 border border-zinc-800 rounded-2xl px-4 py-3 text-[15px] text-zinc-200 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
            <button
              onClick={handleSend}
              className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold rounded-2xl hover:from-purple-500 hover:to-pink-500 transition-all flex items-center gap-2"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
          <p className="text-center mt-2 text-xs text-zinc-600">
            Try messages with emojis like: "I'm so happy!", "This is frustrating!", "I'm nervous!", "Wow! Amazing!"
          </p>
        </div>
      </div>
    </div>
  );
}

function detectEmotion(text: string): 'happy' | 'angry' | 'worried' | 'shock' | 'excited' {
  const lowerText = text.toLowerCase();

  if (lowerText.includes('happy') || lowerText.includes('love') || lowerText.includes('amazing') || lowerText.includes('great')) {
    return 'excited';
  }

  if (lowerText.includes('frustrated') || lowerText.includes('annoyed') || lowerText.includes('hate') || lowerText.includes('stupid')) {
    return 'angry';
  }

  if (lowerText.includes('nervous') || lowerText.includes('scared') || lowerText.includes('worried') || lowerText.includes('afraid')) {
    return 'worried';
  }

  if (lowerText.includes('surprised') || lowerText.includes('shock') || lowerText.includes('what') || lowerText.includes('huh')) {
    return 'shock';
  }

  return 'happy';
}
