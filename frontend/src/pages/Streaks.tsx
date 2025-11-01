import { useEffect } from "react";
import { useJournalStore } from "@/store/journals";

const Streaks = () => {
  const entries = useJournalStore((state) => state.entries);
  const streak = useJournalStore((state) => state.getStreakCount());
  const hydrate = useJournalStore((state) => state.hydrate);

  useEffect(() => {
    void hydrate();
  }, [hydrate]);

  return (
    <div className="max-w-2xl space-y-6">
      <header>
        <h1 className="text-3xl font-semibold text-gray-900">Streaks</h1>
        <p className="text-sm text-gray-500">
          Keep your reflection streak alive by journaling every day.
        </p>
      </header>

      <section className="space-y-3 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="text-5xl font-semibold text-brand">{streak}</div>
        <p className="text-sm text-gray-600">day streak</p>
        <p className="text-sm text-gray-500">
          Entries counted once per calendar day. Multiple recordings on the same
          day still count toward your streak.
        </p>
      </section>

      <section className="space-y-2 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-gray-900">
          Recent check-ins
        </h2>
        {!entries.length && (
          <p className="text-sm text-gray-500">No entries yet.</p>
        )}
        <ul className="space-y-1 text-sm text-gray-600">
          {entries.slice(0, 10).map((entry) => {
            const created = new Date(entry.createdAt);
            return (
              <li key={entry.id}>
                {created.toLocaleDateString(undefined, {
                  month: "short",
                  day: "numeric",
                  year: "numeric"
                })}{" "}
                — {entry.transcript.split(" ").slice(0, 6).join(" ")}…
              </li>
            );
          })}
        </ul>
      </section>
    </div>
  );
};

export default Streaks;
