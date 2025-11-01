import { useEffect, useState } from "react";
import { useJournalStore } from "@/store/journals";

const Settings = () => {
  const clearAll = useJournalStore((state) => state.clearAll);
  const hydrate = useJournalStore((state) => state.hydrate);
  const [storageMode, setStorageMode] = useState<"local" | "encrypted">("local");
  const [isClearing, setIsClearing] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    void hydrate();
  }, [hydrate]);

  const handleClear = async () => {
    setIsClearing(true);
    setMessage(null);
    try {
      await clearAll();
      setMessage("All journals cleared.");
    } finally {
      setIsClearing(false);
    }
  };

  return (
    <div className="max-w-2xl space-y-8">
      <header>
        <h1 className="text-3xl font-semibold text-gray-900">Settings</h1>
        <p className="text-sm text-gray-500">
          Tune privacy options and clear local entries.
        </p>
      </header>

      <section className="space-y-4 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-gray-900">Storage Mode</h2>
        <p className="text-sm text-gray-500">
          Encryption is a future enhancement; selecting it will enable UI
          placeholders.
        </p>
        <div className="flex gap-4">
          {(["local", "encrypted"] as const).map((mode) => (
            <button
              key={mode}
              type="button"
              onClick={() => setStorageMode(mode)}
              className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                storageMode === mode
                  ? "bg-brand text-white"
                  : "border border-gray-200 text-gray-600"
              }`}
            >
              {mode === "local" ? "Local only" : "Encrypted (preview)"}
            </button>
          ))}
        </div>
      </section>

      <section className="space-y-4 rounded-2xl border border-red-100 bg-red-50 p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-red-600">
          Danger Zone — Clear Journals
        </h2>
        <p className="text-sm text-red-500">
          Clears all entries from IndexedDB. This cannot be undone.
        </p>
        <button
          type="button"
          onClick={handleClear}
          disabled={isClearing}
          className="rounded-full bg-red-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-red-600 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isClearing ? "Clearing…" : "Clear all journals"}
        </button>
        {message && <p className="text-sm text-red-600">{message}</p>}
      </section>

      <footer className="text-sm text-gray-400">
        Unposted v0.0.1 — Private by default. Stored locally in your browser.
      </footer>
    </div>
  );
};

export default Settings;
