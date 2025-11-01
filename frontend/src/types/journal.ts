export interface JournalEntry {
  id: string;
  createdAt: string;
  transcript: string;
  duration: number;
  audioBlob?: Blob;
  audioUrl?: string;
  encrypted: boolean;
  title?: string;
  emotion?: string;
}
