import { useEffect, useState } from "react";
import axios from "axios";
import { Loader2 } from "lucide-react";
import Recorder from "@/components/Recorder";
import JournalCard from "@/components/JournalCard";
import { useJournalStore } from "@/store/journals";
import type { JournalEntry } from "@/types/journal";
import { useNavigate } from "react-router-dom";

const Journals = () => {
  const navigate = useNavigate();
  const {
    entries,
    hydrate,
    hydrated,
    addEntry,
    getStreakCount
  } = useJournalStore((state) => ({
    entries: state.entries,
    hydrate: state.hydrate,
    hydrated: state.hydrated,
    addEntry: state.addEntry,
    getStreakCount: state.getStreakCount
  }));

  const [isTranscribing, setIsTranscribing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void hydrate();
  }, [hydrate]);

  const handleRecordingReady = async (blob: Blob, duration: number) => {
    const formData = new FormData();
    formData.append("file", blob, `journal-${Date.now()}.webm`);
    setIsTranscribing(true);
    setError(null);
    try {
      const { data } = await axios.post<{
        transcript: string;
        duration: number;
      }>("/api/transcribe", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });

      const audioUrl = URL.createObjectURL(blob);
      const entry: JournalEntry = {
        id: crypto.randomUUID(),
        createdAt: new Date().toISOString(),
        transcript: data?.transcript ?? "",
        duration: data?.duration ?? duration,
        audioBlob: blob,
        audioUrl,
        encrypted: false,
        title: data?.transcript
          ? data.transcript.split(" ").slice(0, 5).join(" ")
          : undefined
      };
      await addEntry(entry);
    } catch (err) {
      console.error("Transcription failed", err);
      setError("Transcription failed. Try again or check the backend logs.");
    } finally {
      setIsTranscribing(false);
    }
  };

  const handleSelectCard = (entry: JournalEntry) => {
    navigate(`/journals/${entry.id}`);
  };

  return (
    <div className="flex flex-col gap-10">
      <header className="flex flex-col gap-2">
        <h1 className="text-4xl font-semibold text-gray-900">Unposted</h1>
        <p className="text-sm text-gray-500">
          Go from fuzzy thought to clear text. Fast.
        </p>
      </header>

      <section>
        <Recorder onRecordingReady={handleRecordingReady} />
        {isTranscribing && (
          <div className="mt-4 inline-flex items-center gap-2 rounded-full bg-brand/10 px-4 py-2 text-sm text-brand">
            <Loader2 className="h-4 w-4 animate-spin" />
            Transcribing your entry…
          </div>
        )}
        {error && <p className="mt-3 text-sm text-red-500">{error}</p>}
      </section>

      <section className="flex flex-col gap-6">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">Your Journals</h2>
          <span className="rounded-full bg-orange-100 px-4 py-1 text-sm font-semibold text-brand">
            {getStreakCount()} day streak
          </span>
        </div>
        {!entries.length && hydrated && (
          <div className="rounded-2xl border border-dashed border-gray-300 bg-gray-50 px-6 py-10 text-center text-sm text-gray-500">
            No journals yet. Tap record to begin.
          </div>
        )}
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {entries.map((entry) => (
            <JournalCard
              key={entry.id}
              entry={entry}
              onSelect={handleSelectCard}
            />
          ))}
        </div>
      </section>
    </div>
  );
};

export default Journals;
