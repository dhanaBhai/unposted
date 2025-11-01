import type { JournalEntry } from "@/types/journal";
import { CalendarClock, Mic } from "lucide-react";

interface JournalCardProps {
  entry: JournalEntry;
  onSelect: (entry: JournalEntry) => void;
}

export const JournalCard = ({ entry, onSelect }: JournalCardProps) => {
  const created = new Date(entry.createdAt);
  const title =
    entry.title ||
    entry.transcript?.split(" ").slice(0, 5).join(" ") ||
    created.toLocaleString();

  return (
    <button
      type="button"
      onClick={() => onSelect(entry)}
      className="flex w-full flex-col gap-3 rounded-2xl border border-gray-200 bg-white p-5 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-lg"
    >
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <Mic className="h-4 w-4 text-brand" />
      </div>
      <p className="line-clamp-4 text-sm text-gray-600">{entry.transcript}</p>
      <div className="flex items-center justify-between text-xs text-gray-400">
        <span className="inline-flex items-center gap-1">
          <CalendarClock className="h-4 w-4" />
          {created.toLocaleDateString(undefined, {
            month: "short",
            day: "numeric",
            year: "numeric"
          })}
        </span>
        <span>{Math.round(entry.duration)} sec</span>
      </div>
    </button>
  );
};

export default JournalCard;
