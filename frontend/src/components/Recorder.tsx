import { useCallback, useEffect, useRef, useState } from "react";
import { Mic, Pause, Play, Square, Trash2 } from "lucide-react";

type RecorderStatus = "idle" | "recording" | "paused" | "preview" | "error";

export interface RecorderProps {
  onRecordingReady: (blob: Blob, duration: number) => void;
}

const formatTime = (seconds: number): string => {
  const minutes = Math.floor(seconds / 60)
    .toString()
    .padStart(2, "0");
  const remaining = Math.floor(seconds % 60)
    .toString()
    .padStart(2, "0");
  return `${minutes}:${remaining}`;
};

export const Recorder = ({ onRecordingReady }: RecorderProps) => {
  const [status, setStatus] = useState<RecorderStatus>("idle");
  const [elapsed, setElapsed] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewDuration, setPreviewDuration] = useState(0);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);
  const elapsedRef = useRef(0);

  const stopTracks = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    mediaRecorderRef.current = null;
  }, []);

  const resetState = useCallback(() => {
    stopTracks();
    setElapsed(0);
    setPreviewUrl((current) => {
      if (current) URL.revokeObjectURL(current);
      return null;
    });
    setPreviewDuration(0);
    elapsedRef.current = 0;
    chunksRef.current = [];
    setStatus("idle");
  }, [stopTracks]);

  useEffect(() => {
    return () => {
      resetState();
    };
  }, [resetState]);

  const startTimer = () => {
    timerRef.current = window.setInterval(() => {
      setElapsed((current) => {
        const next = current + 1;
        elapsedRef.current = next;
        return next;
      });
    }, 1000);
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;
      chunksRef.current = [];
      elapsedRef.current = 0;

      recorder.ondataavailable = (event) => {
        if (event.data.size) {
          chunksRef.current.push(event.data);
        }
      };

      recorder.onstop = () => {
        stopTracks();
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        const url = URL.createObjectURL(blob);
        setPreviewUrl(url);
        setPreviewDuration(elapsedRef.current);
        setStatus("preview");
      };

      recorder.start();
      setStatus("recording");
      setElapsed(0);
      elapsedRef.current = 0;
      startTimer();
    } catch (err) {
      console.error(err);
      setError("Microphone permissions are required to record audio.");
      setStatus("error");
    }
  };

  const handlePause = () => {
    const recorder = mediaRecorderRef.current;
    if (!recorder) return;
    if (recorder.state === "recording") {
      recorder.pause();
      timerRef.current && clearInterval(timerRef.current);
      setStatus("paused");
    } else if (recorder.state === "paused") {
      recorder.resume();
      startTimer();
      setStatus("recording");
    }
  };

  const handleStop = () => {
    const recorder = mediaRecorderRef.current;
    if (!recorder) return;
    recorder.stop();
  };

  const handleDiscard = () => {
    resetState();
  };

  const handleSave = () => {
    if (!previewUrl) return;
    const blob = new Blob(chunksRef.current, { type: "audio/webm" });
    onRecordingReady(blob, previewDuration);
    resetState();
  };

  return (
    <div className="flex flex-col items-center gap-4 rounded-3xl border border-orange-200 bg-white p-6 shadow-md">
      {status === "idle" && (
        <>
          <Mic className="h-12 w-12 text-brand" />
          <p className="text-lg font-medium text-gray-700">
            Tell us how you feel today.
          </p>
          <button
            type="button"
            onClick={startRecording}
            className="flex items-center gap-2 rounded-full bg-brand px-6 py-3 font-semibold text-white shadow-lg transition hover:bg-brand-dark"
          >
            <Mic className="h-5 w-5" />
            Start Recording
          </button>
        </>
      )}

      {status === "recording" && (
        <div className="flex w-full flex-col items-center gap-4">
          <span className="rounded-full bg-orange-100 px-4 py-1 text-sm font-semibold text-brand">
            Recording…
          </span>
          <div className="text-4xl font-mono font-bold text-gray-900">
            {formatTime(elapsed)}
          </div>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={handlePause}
              className="flex items-center gap-2 rounded-full border border-gray-200 px-4 py-2 text-sm font-semibold text-gray-700 transition hover:border-gray-300"
            >
              <Pause className="h-4 w-4" />
              Pause
            </button>
            <button
              type="button"
              onClick={handleStop}
              className="flex items-center gap-2 rounded-full bg-brand px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-dark"
            >
              <Square className="h-4 w-4" />
              Stop
            </button>
          </div>
        </div>
      )}

      {status === "paused" && (
        <div className="flex flex-col items-center gap-4">
          <span className="text-sm font-semibold text-gray-500">
            Recording paused
          </span>
          <div className="text-4xl font-mono font-bold text-gray-900">
            {formatTime(elapsed)}
          </div>
          <button
            type="button"
            onClick={handlePause}
            className="flex items-center gap-2 rounded-full bg-brand px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-dark"
          >
            <Play className="h-4 w-4" />
            Resume
          </button>
        </div>
      )}

      {status === "preview" && previewUrl && (
        <div className="flex w-full flex-col gap-4">
          <audio controls src={previewUrl} className="w-full" />
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-500">
              Duration: {formatTime(previewDuration)}
            </span>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handleDiscard}
                className="flex items-center gap-2 rounded-full border border-gray-200 px-4 py-2 text-sm font-semibold text-gray-600 transition hover:border-gray-300"
              >
                <Trash2 className="h-4 w-4" />
                Discard
              </button>
              <button
                type="button"
                onClick={handleSave}
                className="rounded-full bg-brand px-5 py-2 text-sm font-semibold text-white transition hover:bg-brand-dark"
              >
                Save &amp; Transcribe
              </button>
            </div>
          </div>
        </div>
      )}

      {status === "error" && error && (
        <p className="text-sm text-red-500">{error}</p>
      )}
    </div>
  );
};

export default Recorder;
