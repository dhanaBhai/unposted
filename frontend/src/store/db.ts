import Dexie, { Table } from "dexie";
import type { JournalEntry } from "@/types/journal";

class JournalDatabase extends Dexie {
  journals!: Table<JournalEntry, string>;

  constructor() {
    super("unposted");
    this.version(1).stores({
      journals: "id, createdAt"
    });
  }
}

export const journalDb = new JournalDatabase();

export const getAllJournals = async (): Promise<JournalEntry[]> => {
  const records = await journalDb.journals.orderBy("createdAt").reverse().toArray();
  return records.map((entry) => {
    const audioUrl =
      entry.audioUrl ??
      (entry.audioBlob ? URL.createObjectURL(entry.audioBlob) : undefined);
    return {
      ...entry,
      audioUrl
    };
  });
};

export const saveJournal = async (entry: JournalEntry): Promise<void> => {
  const { audioUrl, ...persistable } = entry;
  await journalDb.journals.put({ ...persistable, audioUrl: undefined });
};

export const deleteJournal = async (id: string): Promise<void> => {
  await journalDb.journals.delete(id);
};

export const clearJournals = async (): Promise<void> => {
  await journalDb.journals.clear();
};

export const revokeAudioUrl = (entry: JournalEntry): void => {
  if (entry.audioUrl && entry.audioUrl.startsWith("blob:")) {
    URL.revokeObjectURL(entry.audioUrl);
  }
};
