import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { episodeDetails } from './storyData';
import { getPersonalizedEpisodeDetails } from './utils';

// Scenario abandonment penalty
const SCENARIO_PENALTY = -3;

export type CompanionColor = 'blue' | 'pink' | 'purple' | 'red' | 'cyan';

export interface StoryEpisode {
  id: string;
  title: string;
  description: string;
  unlockLevel: number;
  unlocked: boolean;
  scenario?: string;
  backstory?: string;
  narration?: string;
}

export interface Companion {
  id: string;
  name: string;
  age: number;
  relationship: string;
  story: string;
  personality: string;
  color: CompanionColor;
  traits: string[];
  theme: string;
  avatarUrl: string;
  level: number;
  xp: number;
  nextLevelXp: number;
  pendingLevelUp?: boolean;
  relationshipPoints?: number;
  relationshipStage?: string;
  tier?: 'trainable' | 'demo';
  activeScenarioId?: string;
  activeScenarioTitle?: string;
  activeScenarioUserMessages?: number;
  episodes: StoryEpisode[];
  description: string;
}

export interface Message {
  id: string;
  companionId: string;
  sender: 'user' | 'companion' | 'system';
  text: string;
  timestamp: number;
  feedback?: -1 | 1;
}

interface AppState {
  user: { id: string; name: string; email: string } | null;
  authToken: string | null;
  refreshToken: string | null;
  companions: Companion[];
  myCompanions: Companion[];
  messages: Message[];
  login: (name: string, email: string) => void;
  authLogin: (email: string, password: string) => Promise<{ success: boolean; message: string }>;
  authRegister: (name: string, email: string, password: string) => Promise<{ success: boolean; message: string; userId?: string }>;
  authVerifyOtp: (email: string, otp: string) => Promise<{ success: boolean; message: string }>;
  authResendOtp: (email: string) => Promise<{ success: boolean; message: string }>;
  logout: () => void;
  selectCompanion: (id: string, newName?: string) => void;
  updateCompanionAvatar: (companionId: string, newAvatarUrl: string) => void;
  sendMessage: (companionId: string, text: string) => Promise<void>;
  rateMessage: (messageId: string, rating: -1 | 1) => void;
  addSystemMessage: (companionId: string, text: string) => void;
  addXp: (companionId: string, amount: number) => void;
  unlockNextLevel: (companionId: string) => void;
  startScenario: (companionId: string, scenarioId: string, title: string) => void;
  maybeAbandonScenario: (companionId: string) => void;
  deleteCompanion: (companionId: string) => void;
}

const API_BASE_URL = ((import.meta as any).env?.VITE_API_BASE_URL ?? 'http://localhost:8000') + '/api';

function toBackendCompanionId(personality: string | undefined): string {
  const p = (personality ?? '').toLowerCase();
  if (p === 'study buddy') return 'party_friend';
  if (p === 'life-of-the-party') return 'party_friend';
  if (p === 'night-owl philosopher') return 'philosopher';
  if (p === 'competitive rival') return 'rival';
  if (p === 'clueless freshman') return 'freshman';
  return 'party_friend';
}

function normalizeUserText(text: string): string {
  return text.trim().toLowerCase().replace(/\s+/g, ' ');
}

function getRelationshipStage(points: number): string {
  if (points >= 500) return 'Confidant';
  if (points >= 300) return 'Close Friend';
  if (points >= 150) return 'Friend';
  if (points >= 50) return 'Curious';
  return 'Stranger';
}

function evaluateXpDelta(params: {
  text: string;
  recentUserMessages: string[];
  hasActiveScenario: boolean;
}): { delta: number; reasons: string[] } {
  const normalized = normalizeUserText(params.text);
  const reasons: string[] = [];

  const lowEffortSet = new Set(['ok', 'k', 'kk', 'hmm', 'hm', 'ya', 'yes', 'no', 'lol', 'idk', 'sure']);
  const isLowEffort = normalized.length <= 2 || (lowEffortSet.has(normalized) && normalized.split(' ').length <= 2);
  if (isLowEffort) {
    reasons.push('low effort');
  }

  const toxicWords = [
    'stupid', 'idiot', 'dumb', 'shut up', 'hate you',
    'kill yourself', 'moron', 'trash', 'worthless', 'bitch', 'asshole', 'fuck you',
  ];
  const isToxic = toxicWords.some(w => normalized.includes(w));
  if (isToxic) {
    reasons.push('toxic');
  }

  const breaksImmersionPhrases = [
    "you're just an ai", 'you are just an ai', "you're an ai", 'you are an ai',
    'this is fake', 'this story is fake', 'not real', 'roleplay is fake',
  ];
  const breaksImmersion = breaksImmersionPhrases.some(p => normalized.includes(p));
  if (breaksImmersion) {
    reasons.push('breaks immersion');
  }

  const recent = params.recentUserMessages.map(normalizeUserText).filter(Boolean);
  const isSpamRepeat = recent.length >= 3 && recent.slice(0, 3).every(m => m === normalized);
  if (isSpamRepeat) {
    reasons.push('spam repeat');
  }

  let delta = 0;
  if (isToxic) delta -= 5;
  if (breaksImmersion) delta -= 2;
  if (isSpamRepeat) delta -= 1;
  if (isLowEffort && !isToxic) delta -= 1;

  if (delta === 0) {
    const len = normalized.length;
    if (params.hasActiveScenario && len >= 8) {
      delta += 15;
      reasons.push('story interaction');
    } else if (len >= 25) {
      delta += 12;
      reasons.push('thoughtful');
    } else if (len >= 8) {
      delta += 10;
    }
  }

  delta = Math.max(-5, Math.min(delta, 15));
  return { delta, reasons };
}

/** Build auth headers from the current token in store. */
function authHeaders(): Record<string, string> {
  const token = useStore.getState().authToken;
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}

/** Attempt to refresh the access token using the refresh token. */
async function refreshAccessToken(): Promise<boolean> {
  const state = useStore.getState();
  const refreshToken = state.refreshToken;

  if (!refreshToken) {
    console.warn('No refresh token available');
    return false;
  }

  try {
    const resp = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${refreshToken}`,
      },
    });

    if (!resp.ok) {
      console.error('Token refresh failed');
      return false;
    }

    const data = await resp.json();
    const newAccessToken = data?.data?.access_token;

    if (newAccessToken) {
      useStore.setState({ authToken: newAccessToken });
      console.log('Token refreshed successfully');
      return true;
    }

    return false;
  } catch (error) {
    console.error('Token refresh error:', error);
    return false;
  }
}

export const INITIAL_COMPANIONS: Companion[] = [
  {
    id: 'c1', name: 'Oliver', age: 21, relationship: 'Study Partner',
    story: 'A perfectionist driven by academic excellence. He relies on you to stay grounded when the pressure gets to be too much.',
    personality: 'Study Buddy', color: 'blue', traits: ['Logical', 'analytical', 'calm'],
    theme: 'Clean, academic, structured',
    description: 'Your reliable partner for late-night cram sessions and logical debates.',
    avatarUrl: 'https://images.unsplash.com/photo-1614492898637-435e0f87cef8?w=1080&q=80',
    level: 1, xp: 0, nextLevelXp: 100, tier: 'demo',
    episodes: [
      { id: 'e1_1', title: 'The First Library Session', description: 'You meet up to organize your semester syllabus.', unlockLevel: 1, unlocked: true },
      { id: 'e1_2', title: 'Coffee Spills & Color-coding', description: 'Oliver teaches you his exact highlighter method.', unlockLevel: 2, unlocked: false },
      { id: 'e1_3', title: 'Midterm Crisis', description: 'Panic sets in, but logic prevails.', unlockLevel: 3, unlocked: false },
      { id: 'e1_4', title: 'The Lost Flashdrive', description: 'A frantic search across campus for his missing thesis draft.', unlockLevel: 5, unlocked: false },
      { id: 'e1_5', title: 'Debate Team Prep', description: 'You help him practice for the regional debate championship.', unlockLevel: 8, unlocked: false },
      { id: 'e1_6', title: 'Breaking the Routine', description: 'You force Oliver to take a day off and visit the botanical gardens.', unlockLevel: 11, unlocked: false },
      { id: 'e1_7', title: 'The Recommendation Letter', description: 'He struggles with imposter syndrome while applying for a prestigious internship.', unlockLevel: 13, unlocked: false },
      { id: 'e1_8', title: 'Group Project Disaster', description: 'Stepping in to save a failing group project together.', unlockLevel: 15, unlocked: false },
      { id: 'e1_9', title: 'Midnight Lab Access', description: 'Sneaking into the science lab to finish a crucial experiment.', unlockLevel: 17, unlocked: false },
      { id: 'e1_10', title: 'Valedictorian\'s Secret', description: 'He confesses his ultimate fear of failure before graduation.', unlockLevel: 20, unlocked: false },
    ]
  },
  {
    id: 'c2', name: 'Chloe', age: 20, relationship: 'Party Co-conspirator',
    story: 'A vibrant social butterfly with big dreams. Behind the partying, she secretly wants to build an event management empire.',
    personality: 'Life-of-the-Party', color: 'pink', traits: ['Energetic', 'funny', 'extroverted'],
    theme: 'Vibrant, playful',
    description: 'Always knows where the best events are. Brings energy to every conversation.',
    avatarUrl: 'https://images.unsplash.com/photo-1758275557720-37123c8eea5c?w=1080&q=80',
    level: 1, xp: 0, nextLevelXp: 100, tier: 'demo',
    episodes: [
      { id: 'e2_1', title: 'Welcome Week Mixer', description: 'Meeting at the craziest party of the year.', unlockLevel: 1, unlocked: true },
      { id: 'e2_2', title: 'Dorm Room Decor', description: 'Helping her hang up way too many fairy lights.', unlockLevel: 2, unlocked: false },
      { id: 'e2_3', title: 'The Afterparty', description: 'Finding the secret gathering after the main event.', unlockLevel: 3, unlocked: false },
      { id: 'e2_4', title: 'Campus DJ Debut', description: 'Chloe gets her first gig at the student union.', unlockLevel: 5, unlocked: false },
      { id: 'e2_5', title: 'Spring Break Planning', description: 'Chaos ensues as you both try to book flights on a budget.', unlockLevel: 8, unlocked: false },
      { id: 'e2_6', title: 'The Charity Gala', description: 'Organizing a formal event and stressing over the dress code.', unlockLevel: 11, unlocked: false },
      { id: 'e2_7', title: 'Social Media Detox', description: 'Chloe tries to go a week without her phone, with hilarious results.', unlockLevel: 13, unlocked: false },
      { id: 'e2_8', title: 'Sorority Rush Drama', description: 'Navigating the intense politics of Greek life.', unlockLevel: 15, unlocked: false },
      { id: 'e2_9', title: 'The Uninvited Guests', description: 'Bouncing crashers from her epic Halloween bash.', unlockLevel: 17, unlocked: false },
      { id: 'e2_10', title: 'Beyond the Party', description: 'Chloe reveals her serious ambitions for an event management company.', unlockLevel: 20, unlocked: false },
    ]
  },
  {
    id: 'c3', name: 'Julian', age: 22, relationship: 'Midnight Confidant',
    story: 'A brooding, philosophical writer struggling with intense family expectations and the search for artistic meaning.',
    personality: 'Night-Owl Philosopher', color: 'purple', traits: ['Deep thinker', 'empathetic'],
    theme: 'Calm, reflective, soft glow',
    description: 'For those 3 AM conversations about the universe and everything in between.',
    avatarUrl: 'https://images.unsplash.com/photo-1727790632675-204d26c2326c?w=1080&q=80',
    level: 1, xp: 0, nextLevelXp: 100, tier: 'trainable',
    episodes: [
      { id: 'e3_1', title: 'Midnight Coffee', description: 'Discussing existential dread over lukewarm coffee.', unlockLevel: 1, unlocked: true },
      { id: 'e3_2', title: 'Rainy Day Poetry', description: 'Reading obscure poems in the back of the campus bookstore.', unlockLevel: 2, unlocked: false },
      { id: 'e3_3', title: 'Rooftop Revelations', description: 'Stargazing and talking about the future.', unlockLevel: 3, unlocked: false },
      { id: 'e3_4', title: 'The Indie Film Fest', description: 'Enduring a 4-hour silent movie and debating its meaning.', unlockLevel: 5, unlocked: false },
      { id: 'e3_5', title: 'Vinyl Record Hunting', description: 'Scouring the city\'s oldest record shop for a rare album.', unlockLevel: 8, unlocked: false },
      { id: 'e3_6', title: 'Writer\'s Block', description: 'Helping him overcome a massive creative slump for his novel.', unlockLevel: 11, unlocked: false },
      { id: 'e3_7', title: 'The Abandoned Theater', description: 'Exploring an off-limits building on the edge of campus.', unlockLevel: 13, unlocked: false },
      { id: 'e3_8', title: 'Open Mic Night', description: 'Julian finally reads his work in front of an audience.', unlockLevel: 15, unlocked: false },
      { id: 'e3_9', title: 'A Letter from Home', description: 'Dealing with complicated family expectations.', unlockLevel: 17, unlocked: false },
      { id: 'e3_10', title: 'The Final Chapter', description: 'He dedicates his finished manuscript to you.', unlockLevel: 20, unlocked: false },
    ]
  },
  {
    id: 'c4', name: 'Victoria', age: 21, relationship: 'Academic Rival',
    story: 'Fiercely competitive and unapologetically ambitious. She pushes you to your limits and respects you as her only true equal.',
    personality: 'Competitive Rival', color: 'red', traits: ['Sharp', 'witty', 'challenging'],
    theme: 'Bold, intense',
    description: 'Pushes you to be your best by constantly trying to outdo you.',
    avatarUrl: 'https://images.unsplash.com/photo-1756973229525-53fbc1303a61?w=1080&q=80',
    level: 1, xp: 0, nextLevelXp: 100, tier: 'trainable',
    episodes: [
      { id: 'e4_1', title: 'The First Debate', description: 'A fierce argument over a class assignment.', unlockLevel: 1, unlocked: true },
      { id: 'e4_2', title: 'Library Staredown', description: 'An unspoken contest of who can study the longest.', unlockLevel: 2, unlocked: false },
      { id: 'e4_3', title: 'Hackathon Showdown', description: 'Going head-to-head in a 48-hour coding competition.', unlockLevel: 3, unlocked: false },
      { id: 'e4_4', title: 'Election Rivals', description: 'Running against each other for student council.', unlockLevel: 5, unlocked: false },
      { id: 'e4_5', title: 'The Truce', description: 'A temporary alliance to defeat a notoriously harsh professor\'s exam.', unlockLevel: 8, unlocked: false },
      { id: 'e4_6', title: 'Intramural Sports', description: 'Taking your rivalry to the volleyball court.', unlockLevel: 11, unlocked: false },
      { id: 'e4_7', title: 'The Internship Interview', description: 'Realizing you\'re competing for the exact same position.', unlockLevel: 13, unlocked: false },
      { id: 'e4_8', title: 'Vulnerable Moment', description: 'Victoria admits she respects you more than anyone else.', unlockLevel: 15, unlocked: false },
      { id: 'e4_9', title: 'The Sabotage Accusation', description: 'Clearing her name when someone tries to frame her for cheating.', unlockLevel: 17, unlocked: false },
      { id: 'e4_10', title: 'Partners in Crime', description: 'Deciding to join forces and start a company together post-graduation.', unlockLevel: 20, unlocked: false },
    ]
  },
  {
    id: 'c5', name: 'Toby', age: 18, relationship: 'Freshman Mentee',
    story: 'Completely lost in the chaotic world of college life. He looks up to you for guidance on everything from laundry to love.',
    personality: 'Clueless Freshman', color: 'cyan', traits: ['Curious', 'shy', 'polite'],
    theme: 'Light, soft, innocent',
    description: 'Needs a bit of guidance navigating the chaotic campus life.',
    avatarUrl: 'https://images.unsplash.com/photo-1722628219110-39ab18bfd4cb?w=1080&q=80',
    level: 1, xp: 0, nextLevelXp: 100, tier: 'demo',
    episodes: [
      { id: 'e5_1', title: 'Lost on Campus', description: 'Helping them find the lecture hall on day one.', unlockLevel: 1, unlocked: true },
      { id: 'e5_2', title: 'Laundry Room Disaster', description: 'Explaining why red socks and white shirts don\'t mix.', unlockLevel: 2, unlocked: false },
      { id: 'e5_3', title: 'First All-Nighter', description: 'Teaching them the art of survival during finals.', unlockLevel: 3, unlocked: false },
      { id: 'e5_4', title: 'Dining Hall Hacks', description: 'Showing Toby how to make gourmet meals from the buffet.', unlockLevel: 5, unlocked: false },
      { id: 'e5_5', title: 'The First Crush', description: 'Giving terrible advice on how to ask someone out.', unlockLevel: 8, unlocked: false },
      { id: 'e5_6', title: 'Choosing a Major', description: 'The existential panic of declaring a degree.', unlockLevel: 11, unlocked: false },
      { id: 'e5_7', title: 'Roommate Troubles', description: 'Helping him deal with a terribly messy roommate.', unlockLevel: 13, unlocked: false },
      { id: 'e5_8', title: 'Spring Concert Security', description: 'Toby accidentally volunteers as concert security and needs saving.', unlockLevel: 15, unlocked: false },
      { id: 'e5_9', title: 'The Secret Talent', description: 'Discovering Toby is secretly an absolute prodigy at the piano.', unlockLevel: 17, unlocked: false },
      { id: 'e5_10', title: 'The Mentor\'s Pride', description: 'Watching him confidently guide next year\'s incoming freshmen.', unlockLevel: 20, unlocked: false },
    ]
  }
];

export const useStore = create<AppState>()(
  persist(
    (set) => ({
      user: null,
      authToken: null,
      refreshToken: null,
      companions: INITIAL_COMPANIONS,
      myCompanions: [],
      messages: [],

      login: (name, email) => set({ user: { name, email } }),

      authLogin: async (email, password) => {
        console.log('=== LOGIN STARTED ===');
        console.log('Email:', email);
        try {
          const resp = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
          });

          console.log('Login response status:', resp.status);

          if (!resp.ok) {
            const data = await resp.json().catch(() => ({}));
            let msg: string;

            // Extract message from various error response structures
            // Priority 1: AppException structure - {success: false, message: "...", error_code: "...", details: {...}}
            if (data?.message) {
              msg = data.message;
              console.warn(`Login error: ${msg}`);
            }
            // Priority 2: HTTPException structure - {detail: {message: "...", error_code: "...", reset_at: ...}}
            else if (data?.detail) {
              const detail = data.detail;
              if (typeof detail === 'object' && detail !== null) {
                // Extract message from detail object if present
                if (typeof detail.message === 'string') {
                  msg = detail.message;
                } else if (Array.isArray(detail) && detail.length > 0) {
                  // Detail might be array of error objects
                  msg = detail.map((e: any) => e.msg || e.message || String(e)).join('; ');
                } else {
                  // Fallback: stringify detail object to ensure it's a string
                  msg = JSON.stringify(detail);
                }
              } else if (typeof detail === 'string') {
                // Detail is a plain string
                msg = detail;
              } else {
                msg = `Login failed (${resp.status})`;
              }
            }
            // Priority 3: Fallback for any other structure
            else {
              msg = `Login failed (${resp.status})`;
            }

            console.error('Login error:', msg);
            console.error('Error response:', data);
            return { success: false, message: msg };
          }

          const data = await resp.json();
          const tokens = data?.data;

          if (!tokens?.access_token) {
            console.error('No access token received');
            return { success: false, message: 'No token received from server' };
          }

          console.log('Login successful, saving tokens to store');
          console.log('Tokens:', {
            access_token: tokens.access_token ? 'present' : 'missing',
            refresh_token: tokens.refresh_token ? 'present' : 'missing',
            user: tokens.user
          });

          set({
            authToken: tokens.access_token,
            refreshToken: tokens.refresh_token ?? null,
            user: tokens.user
              ? {
                  id: tokens.user.id || tokens.user._id,
                  name: tokens.user.full_name ?? tokens.user.email,
                  email: tokens.user.email
                }
              : { id: '', name: email.split('@')[0], email },
          });
          localStorage.setItem('authToken', tokens.access_token);
          localStorage.setItem('refreshToken', tokens.refresh_token ?? '');

          console.log('Tokens saved to store, user:', tokens.user);
          console.log('=== LOGIN COMPLETED ===');
          return { success: true, message: 'Login successful' };
        } catch (e) {
          console.error('Login error:', e);
          return { success: false, message: e instanceof Error ? e.message : 'Network error' };
        }
      },

      authRegister: async (name, email, password) => {
        try {
          const resp = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ full_name: name, email, password }),
          });
          const data = await resp.json().catch(() => ({}));
          if (!resp.ok) {
            // Extract message from error response
            let msg: string;
            if (data?.message) {
              msg = data.message;
            } else if (data?.detail) {
              const detail = data.detail;
              if (typeof detail === 'object' && detail !== null) {
                if (typeof detail.message === 'string') {
                  msg = detail.message;
                } else if (Array.isArray(detail) && detail.length > 0) {
                  msg = detail.map((e: any) => e.msg || e.message || String(e)).join('; ');
                } else {
                  msg = JSON.stringify(detail);
                }
              } else if (typeof detail === 'string') {
                msg = detail;
              } else {
                msg = `Registration failed (${resp.status})`;
              }
            } else {
              msg = `Registration failed (${resp.status})`;
            }
            return { success: false, message: msg };
          }
          return { success: true, message: data?.message ?? 'Registration successful. Check your email for the OTP code.', userId: data?.data?.user_id };
        } catch (e) {
          return { success: false, message: e instanceof Error ? e.message : 'Network error' };
        }
      },

      authVerifyOtp: async (email, otp) => {
        try {
          const resp = await fetch(`${API_BASE_URL}/auth/verify-otp`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, otp, purpose: 'registration' }),
          });
          const data = await resp.json().catch(() => ({}));
          if (!resp.ok) {
            // Extract message from error response
            let msg: string;
            if (data?.message) {
              msg = data.message;
            } else if (data?.detail) {
              const detail = data.detail;
              if (typeof detail === 'object' && detail !== null) {
                if (typeof detail.message === 'string') {
                  msg = detail.message;
                } else if (Array.isArray(detail) && detail.length > 0) {
                  msg = detail.map((e: any) => e.msg || e.message || String(e)).join('; ');
                } else {
                  msg = JSON.stringify(detail);
                }
              } else if (typeof detail === 'string') {
                msg = detail;
              } else {
                msg = `Verification failed (${resp.status})`;
              }
            } else {
              msg = `Verification failed (${resp.status})`;
            }
            return { success: false, message: msg };
          }
          return { success: true, message: data?.message ?? 'Email verified successfully.' };
        } catch (e) {
          return { success: false, message: e instanceof Error ? e.message : 'Network error' };
        }
      },

      authResendOtp: async (email) => {
        try {
          const resp = await fetch(`${API_BASE_URL}/auth/resend-otp`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, purpose: 'registration' }),
          });
          const data = await resp.json().catch(() => ({}));
          if (!resp.ok) {
            // Extract message from error response
            let msg: string;
            if (data?.message) {
              msg = data.message;
            } else if (data?.detail) {
              const detail = data.detail;
              if (typeof detail === 'object' && detail !== null) {
                if (typeof detail.message === 'string') {
                  msg = detail.message;
                } else if (Array.isArray(detail) && detail.length > 0) {
                  msg = detail.map((e: any) => e.msg || e.message || String(e)).join('; ');
                } else {
                  msg = JSON.stringify(detail);
                }
              } else if (typeof detail === 'string') {
                msg = detail;
              } else {
                msg = `Resend failed (${resp.status})`;
              }
            } else {
              msg = `Resend failed (${resp.status})`;
            }
            return { success: false, message: msg };
          }
          return { success: true, message: data?.message ?? 'OTP resent to your email.' };
        } catch (e) {
          return { success: false, message: e instanceof Error ? e.message : 'Network error' };
        }
      },

            logout: () => {
        localStorage.removeItem('authToken');
        localStorage.removeItem('refreshToken');
        set({ user: null, authToken: null, refreshToken: null, myCompanions: [], messages: [] });
      },

      selectCompanion: (id, newName) => set((state) => {
        const comp = state.companions.find(c => c.id === id);
        if (!comp) return state;
        if (state.myCompanions.some(c => c.id === id)) return state;

        const newComp = {
          ...comp,
          pendingLevelUp: false,
          relationshipPoints: 0,
          relationshipStage: 'Stranger',
          activeScenarioId: undefined as string | undefined,
          activeScenarioTitle: undefined as string | undefined,
          activeScenarioUserMessages: 0
        };
        if (newName && newName !== comp.name) {
          newComp.name = newName;
          newComp.episodes = comp.episodes.map(ep => ({
            ...ep,
            description: ep.description.split(comp.name).join(newName)
          }));
        } else {
          newComp.episodes = comp.episodes.map(ep => ({ ...ep }));
        }

        const profileMsg: Message = {
          id: Math.random().toString(36).substring(7),
          companionId: id,
          sender: 'system',
          text: `COMPANION PROFILE: ${newComp.name}\n\nAGE:\n${newComp.age}\n\nRELATIONSHIP:\n${newComp.relationship}\n\nSTORY:\n${newComp.story}\n\nCHARACTERISTICS:\n${newComp.traits.join(', ')}\n\nTIER: ${newComp.tier ?? 'demo'}`,
          timestamp: Date.now() - 2000
        };

        const level1Episode = newComp.episodes.find(e => e.unlockLevel === 1);
        const details = level1Episode ? getPersonalizedEpisodeDetails(level1Episode.id, comp.name, newComp.name) : null;

        const initialMessages: Message[] = [profileMsg];

        if (level1Episode && details) {
          initialMessages.push({
            id: Math.random().toString(36).substring(7),
            companionId: id,
            sender: 'system',
            text: `NEW SCENARIO UNLOCKED: ${level1Episode.title}\n\nSCENARIO:\n${details.scenario}\n\nBACKSTORY:\n${details.backstory}\n\nNARRATION:\n${details.narration}`,
            timestamp: Date.now() - 1000
          });
          newComp.activeScenarioId = level1Episode.id as any;
          newComp.activeScenarioTitle = level1Episode.title;
          newComp.activeScenarioUserMessages = 0;

          // Store scenario on backend (with auth headers)
          const headers: Record<string, string> = {
            'Content-Type': 'application/json',
            ...authHeaders(),
          };

          // Only store on backend if user is authenticated
          const userId = state.user?.email;
          if (userId && headers.Authorization) {
            void fetch(`${API_BASE_URL}/memory/scenario/unlock`, {
              method: 'POST',
              headers,
              body: JSON.stringify({
                user_id: userId,
                companion_id: id,
                title: level1Episode.title,
                scenario: details.scenario,
                backstory: details.backstory,
                narration: details.narration
              })
            }).catch(() => {});
          }
        }

        return {
          myCompanions: [...state.myCompanions, newComp],
          messages: [...state.messages, ...initialMessages]
        };
      }),

      updateCompanionAvatar: (companionId, newAvatarUrl) => set((state) => ({
        myCompanions: state.myCompanions.map(c =>
          c.id === companionId ? { ...c, avatarUrl: newAvatarUrl } : c
        )
      })),

      deleteCompanion: async (companionId) => {
        console.log('[deleteCompanion] called with companionId:', companionId);

        // First update the UI optimistically, then handle the backend call
        set((state) => {
          // Remove companion from myCompanions
          const newMyCompanions = state.myCompanions.filter(c => c.id !== companionId);
          // Remove all messages for this companion
          const newMessages = state.messages.filter(m => m.companionId !== companionId);
          console.log('[deleteCompanion] Updating state:', {
            oldMyCompanionsCount: state.myCompanions.length,
            newMyCompanionsCount: newMyCompanions.length,
            oldMessagesCount: state.messages.length,
            newMessagesCount: newMessages.length
          });
          return { myCompanions: newMyCompanions, messages: newMessages };
        });

        try {
          const headers: Record<string, string> = {
            'Content-Type': 'application/json',
            ...authHeaders(),
          };

          const resp = await fetch(`${API_BASE_URL}/companion/${companionId}`, {
            method: 'DELETE',
            headers
          });
          console.log('[deleteCompanion] backend response status:', resp.status);
          const respText = await resp.text();
          console.log('[deleteCompanion] backend response text:', respText);
        } catch (e) {
          console.error('Error deleting companion on backend:', e);
        }
      },

      sendMessage: async (companionId, text) => {
        const cleaned = text.trim();
        if (!cleaned) return;

        const userMessage: Message = {
          id: Math.random().toString(36).substring(7),
          companionId,
          sender: 'user',
          text: cleaned,
          timestamp: Date.now()
        };

        // Save previous companion state for rollback if needed
        const prevState = useStore.getState();
        const prevCompanion = prevState.myCompanions.find(c => c.id === companionId);
        const prevMessages = prevState.messages.filter(m => m.companionId === companionId);

        // First, optimistically add just the user message
        set((state) => ({
          messages: [...state.messages, userMessage]
        }));

        const state = useStore.getState();
        const comp = state.myCompanions.find(c => c.id === companionId) ?? state.companions.find(c => c.id === companionId);
        const backendCompanionId = toBackendCompanionId(comp?.personality);

        // Calculate delta now (for demo) but don't apply until API succeeds
        const recentUserMessages = prevMessages
          .filter(m => m.sender === 'user')
          .slice(-3)
          .reverse()
          .map(m => m.text);
        const hasActiveScenario = !!prevCompanion?.activeScenarioId;
        const isTrainable = prevCompanion?.tier === 'trainable';
        const { delta, reasons } = isTrainable
          ? { delta: 0, reasons: [] }  // server will handle XP
          : evaluateXpDelta({ text: cleaned, recentUserMessages, hasActiveScenario });

        try {
          const headers: Record<string, string> = {
            'Content-Type': 'application/json',
            ...authHeaders(),
          };

          // Build scenario text from active episode
          let scenarioText: string | undefined;
          if (comp?.activeScenarioId && comp?.activeScenarioTitle) {
            const episode = comp.episodes?.find(ep => ep.id === comp.activeScenarioId);
            if (episode) {
              const details = getPersonalizedEpisodeDetails(episode.id, comp.personality, comp.name);
              if (details) {
                scenarioText = `Title: ${comp.activeScenarioTitle}\nScenario: ${details.scenario}\nBackstory: ${details.backstory}\nNarration: ${details.narration}`;
              }
            }
          }

          let resp = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers,
            body: JSON.stringify({
              companion_key: companionId,
              personality_id: backendCompanionId,
              message: cleaned,
              episode_id: comp?.activeScenarioId,
              scenario_text: scenarioText,
              companion_profile: comp ? {
                name: comp.name,
                age: comp.age,
                relationship: comp.relationship,
                story: comp.story,
                traits: comp.traits,
                personality: comp.personality,
                relationshipStage: comp.relationshipStage,
                level: comp.level,
                xp: comp.xp
              } : null
            })
          });

          // If token expired, try to refresh and retry
          if (resp.status === 401) {
            const refreshed = await refreshAccessToken();
            if (refreshed) {
              // Retry with new token
              const newHeaders: Record<string, string> = {
                'Content-Type': 'application/json',
                ...authHeaders(),
              };
              resp = await fetch(`${API_BASE_URL}/chat`, {
                method: 'POST',
                headers: newHeaders,
                body: JSON.stringify({
                  companion_key: companionId,
                  personality_id: backendCompanionId,
                  message: cleaned,
                  episode_id: comp?.activeScenarioId,
                  scenario_text: scenarioText,
                  companion_profile: comp ? {
                    name: comp.name,
                    age: comp.age,
                    relationship: comp.relationship,
                    story: comp.story,
                    traits: comp.traits,
                    personality: comp.personality,
                    relationshipStage: comp.relationshipStage,
                    level: comp.level,
                    xp: comp.xp
                  } : null
                })
              });
            }
          }

          if (!resp.ok) {
            const errorText = await resp.text();
            const error = errorText || `Request failed (${resp.status})`;

            // Check if it's still an auth error after refresh attempt
            if (resp.status === 401 || resp.status === 403) {
              throw new Error('AUTH_EXPIRED');
            }
            throw new Error(error);
          }

          const data = await resp.json();
          const replyText = typeof data?.reply === 'string' && data.reply.trim()
            ? data.reply.trim()
            : "I'm here—what would you like to talk about?";

          const compResponse: Message = {
            id: Math.random().toString(36).substring(7),
            companionId,
            sender: 'companion',
            text: replyText,
            timestamp: Date.now()
          };

          // For trainable companions, apply server-side XP/progression
          if (data?.tier === 'trainable' && data?.xp_delta != null) {
            set((s) => {
              const xpDelta = data.xp_delta as number;
              const totalXp = data.total_xp as number | undefined;
              const serverLevel = data.level as number | undefined;
              const serverStage = data.relationship_stage as string | undefined;
              const rlAction = data.rl_action as string | undefined;
              const pendingLevelUp = data.pending_level_up as boolean | undefined;

              const msgs = [...s.messages, compResponse];

              // Show XP system message
              if (xpDelta !== 0) {
                const reason = xpDelta > 0 ? (rlAction ? `+${rlAction}` : '') : 'penalty';
                msgs.push({
                  id: Math.random().toString(36).substring(7),
                  companionId,
                  sender: 'system',
                  text: `XP ${xpDelta > 0 ? '+' : ''}${xpDelta}${reason ? ` • ${reason}` : ''}${serverStage ? ` • ${serverStage}` : ''}`,
                  timestamp: Date.now(),
                });
              }

              const nextCompanions = s.myCompanions.map(c => {
                if (c.id !== companionId) return c;
                const updated = { ...c };
                // Update XP from server response
                if (totalXp != null) updated.xp = totalXp;
                if (serverLevel != null) updated.level = serverLevel;
                if (serverStage != null) updated.relationshipStage = serverStage;
                if (pendingLevelUp != null) updated.pendingLevelUp = pendingLevelUp;
                // relationship points from stage
                const stagePoints: Record<string, number> = {
                  Stranger: 0, Curious: 50, Friend: 150, 'Close Friend': 300, Confidant: 500,
                };
                if (serverStage && stagePoints[serverStage] != null) {
                  updated.relationshipPoints = stagePoints[serverStage];
                }
                // Update scenario message count
                const nextScenarioCount = updated.activeScenarioId
                  ? (updated.activeScenarioUserMessages ?? 0) + 1
                  : (updated.activeScenarioUserMessages ?? 0);
                if (updated.activeScenarioId && nextScenarioCount >= 6) {
                  return { ...updated, activeScenarioId: undefined, activeScenarioTitle: undefined, activeScenarioUserMessages: 0 };
                }
                return { ...updated, activeScenarioUserMessages: nextScenarioCount };
              });

              return { messages: msgs, myCompanions: nextCompanions };
            });
          } else {
            // For demo companions, apply XP now
            if (!isTrainable) {
              set((state) => {
                const nextMessages = [...state.messages, compResponse];
                if (delta < 0) {
                  nextMessages.push({
                    id: Math.random().toString(36).substring(7),
                    companionId,
                    sender: 'system',
                    text: `XP ${delta} • ${reasons.join(', ') || 'penalty'}`,
                    timestamp: Date.now()
                  });
                }

                const nextCompanions = state.myCompanions.map(c => {
                  if (c.id !== companionId) return c;

                  const relationshipPoints = Math.max(0, (c.relationshipPoints ?? 0) + delta);
                  let xp = c.xp + delta;
                  xp = Math.max(0, Math.min(xp, c.nextLevelXp));

                  let pendingLevelUp = !!c.pendingLevelUp;
                  if (xp >= c.nextLevelXp) pendingLevelUp = true;
                  if (pendingLevelUp && xp < c.nextLevelXp) pendingLevelUp = false;

                  const nextScenarioCount = c.activeScenarioId
                    ? (c.activeScenarioUserMessages ?? 0) + 1
                    : (c.activeScenarioUserMessages ?? 0);

                  if (c.activeScenarioId && nextScenarioCount >= 6) {
                    return { ...c, xp, pendingLevelUp, relationshipPoints, activeScenarioId: undefined, activeScenarioTitle: undefined, activeScenarioUserMessages: 0 };
                  }

                  return { ...c, xp, pendingLevelUp, relationshipPoints, activeScenarioUserMessages: nextScenarioCount };
                });

                return { messages: nextMessages, myCompanions: nextCompanions };
              });
            } else {
              // Just add companion reply and update scenario count for trainable (non-XP)
              set((state) => {
                const nextCompanions = state.myCompanions.map(c => {
                  if (c.id !== companionId) return c;
                  const nextScenarioCount = c.activeScenarioId
                    ? (c.activeScenarioUserMessages ?? 0) + 1
                    : (c.activeScenarioUserMessages ?? 0);
                  if (c.activeScenarioId && nextScenarioCount >= 6) {
                    return { ...c, activeScenarioId: undefined, activeScenarioTitle: undefined, activeScenarioUserMessages: 0 };
                  }
                  return { ...c, activeScenarioUserMessages: nextScenarioCount };
                });
                return { messages: [...state.messages, compResponse], myCompanions: nextCompanions };
              });
            }
          }
        } catch (err) {
          let message = "I couldn't reach the AI server right now. Please try again in a moment.";
          if (err instanceof Error && err.message) {
            // Handle expired authentication
            if (err.message === 'AUTH_EXPIRED') {
              message = 'Your session has expired. Please log in again to continue chatting.';
              // Clear auth state to redirect to login
              setTimeout(() => {
                useStore.setState({
                  authToken: null,
                  refreshToken: null,
                  user: null,
                  myCompanions: [],
                  messages: []
                });
                window.location.href = '/login';
              }, 2000);
            } else {
              try {
                const parsed = JSON.parse(err.message);
                if (typeof parsed?.detail === 'string' && parsed.detail.trim()) {
                  message = parsed.detail.trim();
                } else if (typeof parsed?.detail?.message === 'string') {
                  message = parsed.detail.message;
                }
              } catch {
                if (err.message.includes('OpenRouter error') || err.message.includes('OPENROUTER_API_KEY')) {
                  message = err.message;
                } else if (err.message.includes('401') || err.message.includes('403')) {
                  message = 'Please log in to continue chatting.';
                }
              }
            }
          }
          const fallback: Message = {
            id: Math.random().toString(36).substring(7),
            companionId,
            sender: 'companion',
            text: message,
            timestamp: Date.now()
          };
          set((s) => ({ messages: [...s.messages, fallback] }));
        }
      },

      rateMessage: (messageId, rating) => set((state) => ({
        messages: state.messages.map(m => (m.id === messageId ? { ...m, feedback: rating } : m))
      })),

      addSystemMessage: (companionId, text) => set((state) => {
        const newSystemMessage: Message = {
          id: Math.random().toString(36).substring(7),
          companionId,
          sender: 'system',
          text,
          timestamp: Date.now()
        };
        return { messages: [...state.messages, newSystemMessage] };
      }),

      addXp: (companionId, amount) => set((state) => {
        return {
          myCompanions: state.myCompanions.map(c => {
            if (c.id !== companionId) return c;
            const relationshipPoints = Math.max(0, (c.relationshipPoints ?? 0) + amount);
            let xp = c.xp + amount;
            xp = Math.max(0, Math.min(xp, c.nextLevelXp));

            let pendingLevelUp = !!c.pendingLevelUp;
            if (xp >= c.nextLevelXp) pendingLevelUp = true;
            if (pendingLevelUp && xp < c.nextLevelXp) pendingLevelUp = false;

            return { ...c, xp, pendingLevelUp, relationshipPoints };
          })
        };
      }),

      unlockNextLevel: async (companionId) => {
        console.log('[unlockNextLevel] called with companionId:', companionId);
        try {
          const headers: Record<string, string> = {
            'Content-Type': 'application/json',
            ...authHeaders(),
          };

          const resp = await fetch(`${API_BASE_URL}/companion/${companionId}/unlock-level`, {
            method: 'POST',
            headers
          });

          console.log('[unlockNextLevel] response status:', resp.status);

          if (!resp.ok) {
            const errorText = await resp.text();
            console.error('Unlock level failed:', errorText);
            throw new Error(errorText || 'Failed to unlock level');
          }

          // Now update local state
          set((state) => ({
            myCompanions: state.myCompanions.map(c => {
              if (c.id !== companionId) return c;
              if (!c.pendingLevelUp) return c;

              const newLevel = c.level + 1;
              const newNextXp = Math.floor(c.nextLevelXp * 1.5);
              const newEpisodes = c.episodes.map(ep => ({
                ...ep,
                unlocked: newLevel >= ep.unlockLevel ? true : ep.unlocked
              }));

              return {
                ...c,
                level: newLevel,
                xp: 0, // Reset XP for new level (matching backend)
                nextLevelXp: newNextXp,
                episodes: newEpisodes,
                pendingLevelUp: false,
                relationshipPoints: (c.relationshipPoints ?? 0) + 10
              };
            })
          }));
        } catch (err) {
          console.error('Error unlocking level:', err);
        }
      },

      startScenario: (companionId, scenarioId, title) => set((state) => ({
        myCompanions: state.myCompanions.map(c => (
          c.id === companionId
            ? { ...c, activeScenarioId: scenarioId, activeScenarioTitle: title, activeScenarioUserMessages: 0 }
            : c
        ))
      })),

      maybeAbandonScenario: (companionId) => set((state) => {
        // First check if the companion even exists in myCompanions (it might have been deleted!)
        const comp = state.myCompanions.find(c => c.id === companionId);
        if (!comp) return state;
        if (!comp?.activeScenarioId) return state;
        if ((comp.activeScenarioUserMessages ?? 0) > 0) {
          return {
            myCompanions: state.myCompanions.map(c => (
              c.id === companionId
                ? { ...c, activeScenarioId: undefined, activeScenarioTitle: undefined, activeScenarioUserMessages: 0 }
                : c
            ))
          };
        }

        const nextMessages = [
          ...state.messages,
          {
            id: Math.random().toString(36).substring(7),
            companionId,
            sender: 'system' as const,
            text: `XP ${SCENARIO_PENALTY} • left scenario`,
            timestamp: Date.now()
          }
        ];

        const nextCompanions = state.myCompanions.map(c => {
          if (c.id !== companionId) return c;
          const relationshipPoints = Math.max(0, (c.relationshipPoints ?? 0) + SCENARIO_PENALTY);
          let xp = c.xp + SCENARIO_PENALTY;
          xp = Math.max(0, Math.min(xp, c.nextLevelXp));
          let pendingLevelUp = !!c.pendingLevelUp;
          if (pendingLevelUp && xp < c.nextLevelXp) pendingLevelUp = false;
          return { ...c, xp, pendingLevelUp, relationshipPoints, activeScenarioId: undefined, activeScenarioTitle: undefined, activeScenarioUserMessages: 0 };
        });

        return {
          messages: nextMessages,
          myCompanions: nextCompanions
        };
      })
    }),
    {
      name: 'ai-campus-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => (({
        user: state.user,
        authToken: state.authToken,
        refreshToken: state.refreshToken,
        myCompanions: state.myCompanions,
        messages: state.messages,
      })),
    }
  )
);
