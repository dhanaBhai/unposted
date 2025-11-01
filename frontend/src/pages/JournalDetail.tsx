import { useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import JournalDetail from "@/components/JournalDetail";
import { useJournalStore } from "@/store/journals";

const JournalDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const entry = useJournalStore((state) =>
    id ? state.getEntry(id) : undefined
  );
  const removeEntry = useJournalStore((state) => state.removeEntry);
  const hydrate = useJournalStore((state) => state.hydrate);

  useEffect(() => {
    void hydrate();
  }, [hydrate]);

  const handleDelete = async (entryId: string) => {
    await removeEntry(entryId);
    navigate("/journals");
  };

  if (!id) {
    return <p className="text-sm text-gray-500">No journal selected.</p>;
  }

  if (!entry) {
    return (
      <div className="space-y-4">
        <p className="text-lg font-semibold text-gray-900">
          Entry not found or still loading.
        </p>
        <button
          type="button"
          onClick={() => navigate("/journals")}
          className="rounded-full bg-brand px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-dark"
        >
          Back to Journals
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-3xl">
      <JournalDetail entry={entry} onDelete={handleDelete} />
    </div>
  );
};

export default JournalDetailPage;
