import { useEffect, useState } from "react";
import type { JournalEntry } from "@/types/journal";
import { DownloadCloud, FileText, ShieldCheck, Trash } from "lucide-react";

interface JournalDetailProps {
  entry: JournalEntry;
  onDelete?: (id: string) => void;
}

const downloadBlob = (blob: Blob, filename: string) => {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
};

export const JournalDetail = ({ entry, onDelete }: JournalDetailProps) => {
  const created = new Date(entry.createdAt);
  const [audioSrc, setAudioSrc] = useState<string | null>(null);

  useEffect(() => {
    if (entry.audioUrl) {
      setAudioSrc(entry.audioUrl);
      return;
    }
    if (!entry.audioBlob) {
      setAudioSrc(null);
      return;
    }
    const url = URL.createObjectURL(entry.audioBlob);
    setAudioSrc(url);
    return () => URL.revokeObjectURL(url);
  }, [entry.audioBlob, entry.audioUrl]);

  const handleDelete = () => {
    onDelete?.(entry.id);
  };

  const handleDownloadAudio = () => {
    if (entry.audioBlob) {
      downloadBlob(entry.audioBlob, `${entry.id}.webm`);
      return;
    }
    if (entry.audioUrl) {
      fetch(entry.audioUrl)
        .then((response) => response.blob())
        .then((blob) => downloadBlob(blob, `${entry.id}.webm`))
        .catch((err) => console.error("Failed to download audio", err));
    }
  };

  const handleExportTranscript = () => {
    const blob = new Blob([entry.transcript], { type: "text/plain" });
    downloadBlob(blob, `${entry.id}.txt`);
  };

  return (
    <section className="flex flex-col gap-6 rounded-3xl bg-surface-dark p-8 text-white shadow-xl">
      <header className="flex flex-col gap-2">
        <span className="text-sm uppercase tracking-wide text-brand">
          {created.toLocaleDateString(undefined, {
            month: "short",
            day: "numeric",
            year: "numeric"
          })}
        </span>
        <h1 className="text-2xl font-semibold">
          {entry.title || "Appreciation for Your Viewership"}
        </h1>
      </header>

      <p className="rounded-2xl bg-white/10 p-4 text-base leading-relaxed text-white/90">
        {entry.transcript || "Transcript will appear here."}
      </p>

      {audioSrc ? (
        <audio controls src={audioSrc} className="w-full">
          Your browser does not support the audio element.
        </audio>
      ) : (
        <div className="rounded-2xl border border-dashed border-white/20 p-6 text-sm text-white/70">
          Audio preview unavailable for this entry.
        </div>
      )}

      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={handleDownloadAudio}
          className="inline-flex items-center gap-2 rounded-full border border-white/20 px-4 py-2 text-sm font-semibold transition hover:bg-white/10"
        >
          <DownloadCloud className="h-4 w-4" />
          Download Audio
        </button>
        <button
          type="button"
          onClick={handleExportTranscript}
          className="inline-flex items-center gap-2 rounded-full border border-white/20 px-4 py-2 text-sm font-semibold transition hover:bg-white/10"
        >
          <FileText className="h-4 w-4" />
          Export Transcript
        </button>
        <button
          type="button"
          onClick={handleDelete}
          className="inline-flex items-center gap-2 rounded-full border border-red-400/60 px-4 py-2 text-sm font-semibold text-red-200 transition hover:bg-red-500/10"
        >
          <Trash className="h-4 w-4" />
          Delete
        </button>
      </div>

      <footer className="flex items-center gap-2 text-sm text-white/70">
        <ShieldCheck className="h-4 w-4 text-brand" />
        Private by default — stored locally in your browser.
      </footer>
    </section>
  );
};

export default JournalDetail;
