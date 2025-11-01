import { create } from "zustand";
import type { JournalEntry } from "@/types/journal";
import {
  clearJournals,
  deleteJournal,
  getAllJournals,
  revokeAudioUrl,
  saveJournal
} from "./db";

export interface JournalState {
  entries: JournalEntry[];
  hydrated: boolean;
  addEntry: (entry: JournalEntry) => Promise<void>;
  updateEntry: (id: string, patch: Partial<JournalEntry>) => Promise<void>;
  removeEntry: (id: string) => Promise<void>;
  clearAll: () => Promise<void>;
  hydrate: () => Promise<void>;
  getStreakCount: () => number;
  getEntry: (id: string) => JournalEntry | undefined;
}

export const useJournalStore = create<JournalState>((set, get) => ({
  entries: [],
  hydrated: false,
  addEntry: async (entry) => {
    const derivedAudioUrl =
      entry.audioUrl ??
      (entry.audioBlob ? URL.createObjectURL(entry.audioBlob) : undefined);
    const nextEntry = {
      ...entry,
      audioUrl: derivedAudioUrl
    };
    await saveJournal(nextEntry);
    set((state) => ({ entries: [nextEntry, ...state.entries] }));
  },
  updateEntry: async (id, patch) => {
    const existing = get().entries.find((entry) => entry.id === id);
    if (!existing) return;
    let updated = { ...existing, ...patch };
    if (patch.audioBlob) {
      const audioUrl = URL.createObjectURL(patch.audioBlob);
      revokeAudioUrl(existing);
      updated = { ...updated, audioUrl };
    }
    await saveJournal(updated);
    set((state) => ({
      entries: state.entries.map((entry) => (entry.id === id ? updated : entry))
    }));
  },
  removeEntry: async (id) => {
    await deleteJournal(id);
    set((state) => {
      const entry = state.entries.find((item) => item.id === id);
      if (entry) {
        revokeAudioUrl(entry);
      }
      return {
        entries: state.entries.filter((item) => item.id !== id)
      };
    });
  },
  clearAll: async () => {
    await clearJournals();
    set((state) => {
      state.entries.forEach(revokeAudioUrl);
      return { entries: [] };
    });
  },
  hydrate: async () => {
    if (get().hydrated) return;
    const entries = await getAllJournals();
    set({ entries, hydrated: true });
  },
  getStreakCount: () => {
    const entries = [...get().entries].sort(
      (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    );
    if (!entries.length) return 0;
    let streak = 1;
    let current = new Date(entries[0].createdAt);
    for (let i = 1; i < entries.length; i += 1) {
      const nextDate = new Date(entries[i].createdAt);
      const diff = Math.ceil(
        (current.getTime() - nextDate.getTime()) / (1000 * 60 * 60 * 24)
      );
      if (diff === 0) {
        continue;
      }
      if (diff === 1) {
        streak += 1;
        current = nextDate;
        continue;
      }
      break;
    }
    return streak;
  },
  getEntry: (id) => get().entries.find((entry) => entry.id === id)
}));
