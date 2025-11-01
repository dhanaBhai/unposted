
#!/usr/bin/env python3
"""
Audio Prosody Analysis with Sentence-Level Valence Correlation

Requirements:
whisperx>=3.1.0
librosa>=0.10.0
parselmouth>=0.4.0
numpy>=1.21.0
pandas>=1.3.0
matplotlib>=3.5.0
soundfile>=0.12.0
aeneas (optional fallback)
"""

import argparse
import json
import csv
import logging
import warnings
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Audio processing
try:
    import librosa
    import soundfile as sf
except ImportError as e:
    print(f"Error: Missing required audio library: {e}")
    print("Install with: pip install librosa soundfile")
    sys.exit(1)

# Praat features (optional)
try:
    import parselmouth
    PARSELMOUTH_AVAILABLE = True
except ImportError:
    PARSELMOUTH_AVAILABLE = False
    warnings.warn("parselmouth not available. Will use librosa for F0 estimation.")

# Forced alignment libraries
WHISPERX_AVAILABLE = False
AENEAS_AVAILABLE = False

try:
    import whisperx
    WHISPERX_AVAILABLE = True
except ImportError:
    pass

try:
    from aeneas.executetask import ExecuteTask
    from aeneas.task import Task
    AENEAS_AVAILABLE = True
except ImportError:
    pass

if not WHISPERX_AVAILABLE and not AENEAS_AVAILABLE:
    print("Error: Neither WhisperX nor Aeneas is available for forced alignment.")
    print("Install WhisperX with: pip install whisperx")
    print("Or install Aeneas with: pip install aeneas")
    sys.exit(1)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_transcript(transcript_path: str) -> List[str]:
    """Load transcript file with one sentence per line."""
    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            sentences = [line.strip() for line in f.readlines() if line.strip()]
        logger.info(f"Loaded {len(sentences)} sentences from transcript")
        return sentences
    except Exception as e:
        logger.error(f"Failed to load transcript: {e}")
        raise


def load_valence_scores(valence_path: str) -> Dict[int, float]:
    """Load valence scores from JSON or CSV file."""
    valence_path = Path(valence_path)
    
    try:
        if valence_path.suffix.lower() == '.json':
            with open(valence_path, 'r') as f:
                data = json.load(f)
            # Handle both dict with string keys and list formats
            if isinstance(data, dict):
                valence_scores = {int(k): float(v) for k, v in data.items()}
            elif isinstance(data, list):
                valence_scores = {i: float(v) for i, v in enumerate(data)}
            else:
                raise ValueError("JSON must be dict or list format")
                
        elif valence_path.suffix.lower() == '.csv':
            df = pd.read_csv(valence_path)
            if 'index' in df.columns and 'valence' in df.columns:
                valence_scores = dict(zip(df['index'], df['valence']))
            elif len(df.columns) >= 2:
                # Assume first column is index, second is valence
                valence_scores = dict(zip(df.iloc[:, 0], df.iloc[:, 1]))
            else:
                raise ValueError("CSV must have index and valence columns")
        else:
            raise ValueError("Valence file must be .json or .csv")
            
        logger.info(f"Loaded valence scores for {len(valence_scores)} sentences")
        return valence_scores
        
    except Exception as e:
        logger.error(f"Failed to load valence scores: {e}")
        raise


def perform_forced_alignment(audio_path: str, sentences: List[str]) -> List[Dict]:
    """Perform forced alignment using WhisperX or Aeneas fallback."""
    
    if WHISPERX_AVAILABLE:
        return _align_with_whisperx(audio_path, sentences)
    elif AENEAS_AVAILABLE:
        return _align_with_aeneas(audio_path, sentences)
    else:
        raise RuntimeError("No alignment library available")


def _align_with_whisperx(audio_path: str, sentences: List[str]) -> List[Dict]:
    """Perform alignment using WhisperX."""
    logger.info("Using WhisperX for forced alignment")
    
    try:
        # Load audio
        audio = whisperx.load_audio(audio_path)
        
        # Load model
        model = whisperx.load_model("base")
        
        # Transcribe
        result = model.transcribe(audio, batch_size=16)
        
        # Load alignment model
        model_a, metadata = whisperx.load_align_model(language_code=result["language"], device="cpu")
        
        # Align
        result = whisperx.align(result["segments"], model_a, metadata, audio, "cpu", return_char_alignments=False)
        
        # Convert to sentence-level alignment
        return _aggregate_words_to_sentences(result["segments"], sentences)
        
    except Exception as e:
        logger.error(f"WhisperX alignment failed: {e}")
        if AENEAS_AVAILABLE:
            logger.info("Falling back to Aeneas")
            return _align_with_aeneas(audio_path, sentences)
        else:
            raise


def _align_with_aeneas(audio_path: str, sentences: List[str]) -> List[Dict]:
    """Perform alignment using Aeneas."""
    logger.info("Using Aeneas for forced alignment")
    
    try:
        # Create temporary text file
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for i, sentence in enumerate(sentences):
                f.write(f"sentence_{i+1:03d} {sentence}\n")
            text_file = f.name
        
        # Create task configuration
        config_string = f'''
        task_language=en|
        is_text_type=plain|
        os_task_file_format=json
        '''
        
        # Create and execute task
        task = Task(config_string=config_string)
        task.audio_file_path_absolute = audio_path
        task.text_file_path_absolute = text_file
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            task.sync_map_file_path_absolute = f.name
            sync_map_file = f.name
        
        ExecuteTask(task).execute()
        
        # Load results
        with open(sync_map_file, 'r') as f:
            alignment_data = json.load(f)
        
        # Clean up
        os.unlink(text_file)
        os.unlink(sync_map_file)
        
        # Convert to our format
        alignments = []
        for fragment in alignment_data['fragments']:
            alignments.append({
                'start': float(fragment['begin']),
                'end': float(fragment['end']),
                'text': fragment['lines'][0] if fragment['lines'] else ""
            })
        
        return alignments
        
    except Exception as e:
        logger.error(f"Aeneas alignment failed: {e}")
        raise


def _aggregate_words_to_sentences(segments: List[Dict], sentences: List[str]) -> List[Dict]:
    """Aggregate word-level timestamps to sentence-level."""
    logger.info("Aggregating word timestamps to sentences")
    
    alignments = []
    current_time = 0.0
    
    for i, sentence in enumerate(sentences):
        # Find best matching segment(s) for this sentence
        sentence_words = sentence.lower().split()
        best_start = current_time
        best_end = current_time + 2.0  # Default 2 second duration
        
        # Try to find matching words in segments
        for segment in segments:
            if 'words' in segment:
                segment_text = segment.get('text', '').lower()
                # Simple overlap check
                overlap = len(set(sentence_words) & set(segment_text.split()))
                if overlap > len(sentence_words) * 0.3:  # 30% overlap threshold
                    if segment['words']:
                        best_start = segment['words'][0].get('start', best_start)
                        best_end = segment['words'][-1].get('end', best_end)
                    else:
                        best_start = segment.get('start', best_start)
                        best_end = segment.get('end', best_end)
                    break
        
        alignments.append({
            'start': best_start,
            'end': best_end,
            'text': sentence
        })
        
        current_time = best_end
    
    return alignments


def extract_prosody_features(audio_path: str, start_time: float, end_time: float, 
                           sr: int = 22050) -> Dict[str, Union[float, List[float]]]:
    """Extract prosody features for a given time segment."""
    
    # Load audio segment
    y, sr = librosa.load(audio_path, sr=sr, offset=start_time, duration=end_time - start_time)
    
    if len(y) == 0:
        logger.warning(f"Empty audio segment at {start_time}-{end_time}")
        return _empty_prosody_features()
    
    features = {}
    
    # Duration
    features['duration'] = end_time - start_time
    
    # RMS Energy
    rms = librosa.feature.rms(y=y)[0]
    features['mean_rms'] = float(np.mean(rms))
    features['rms_std'] = float(np.std(rms))
    
    # Zero Crossing Rate
    zcr = librosa.feature.zero_crossing_rate(y)[0]
    features['zcr_mean'] = float(np.mean(zcr))
    
    # F0 features
    if PARSELMOUTH_AVAILABLE:
        features.update(_extract_praat_features(y, sr))
    else:
        features.update(_extract_librosa_f0(y, sr))
    
    # Tempo estimation
    try:
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        features['tempo_estimate'] = float(tempo)
    except:
        features['tempo_estimate'] = 0.0
    
    # Speaking rate (words per second estimate)
    # Rough estimate based on syllable detection via onset detection
    try:
        onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
        syllable_rate = len(onset_frames) / features['duration'] if features['duration'] > 0 else 0
        features['speaking_rate'] = float(syllable_rate)
    except:
        features['speaking_rate'] = 0.0
    
    return features


def _extract_praat_features(y: np.ndarray, sr: int) -> Dict[str, float]:
    """Extract F0, jitter, shimmer using Parselmouth/Praat."""
    try:
        # Convert to Praat Sound object
        sound = parselmouth.Sound(y, sampling_frequency=sr)
        
        # Extract pitch
        pitch = sound.to_pitch()
        f0_values = pitch.selected_array['frequency']
        f0_values = f0_values[f0_values != 0]  # Remove unvoiced frames
        
        features = {}
        if len(f0_values) > 0:
            features['mean_f0'] = float(np.mean(f0_values))
            features['median_f0'] = float(np.median(f0_values))
            features['f0_std'] = float(np.std(f0_values))
            features['f0_contour'] = f0_values[::max(1, len(f0_values)//20)].tolist()  # Downsample
        else:
            features['mean_f0'] = 0.0
            features['median_f0'] = 0.0
            features['f0_std'] = 0.0
            features['f0_contour'] = []
        
        # Jitter and shimmer
        try:
            pointprocess = parselmouth.praat.call(sound, "To PointProcess (periodic, cc)", 75, 600)
            jitter = parselmouth.praat.call(pointprocess, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3)
            features['jitter'] = float(jitter) if not np.isnan(jitter) else 0.0
        except:
            features['jitter'] = 0.0
        
        try:
            shimmer = parselmouth.praat.call([sound, pointprocess], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
            features['shimmer'] = float(shimmer) if not np.isnan(shimmer) else 0.0
        except:
            features['shimmer'] = 0.0
        
        return features
        
    except Exception as e:
        logger.warning(f"Praat feature extraction failed: {e}")
        return _extract_librosa_f0(y, sr)


def _extract_librosa_f0(y: np.ndarray, sr: int) -> Dict[str, float]:
    """Extract F0 using librosa as fallback."""
    try:
        # Use piptrack for F0 estimation
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr, threshold=0.1)
        
        # Extract F0 contour
        f0_contour = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:
                f0_contour.append(pitch)
        
        features = {}
        if f0_contour:
            features['mean_f0'] = float(np.mean(f0_contour))
            features['median_f0'] = float(np.median(f0_contour))
            features['f0_std'] = float(np.std(f0_contour))
            features['f0_contour'] = f0_contour[::max(1, len(f0_contour)//20)]  # Downsample
        else:
            features['mean_f0'] = 0.0
            features['median_f0'] = 0.0
            features['f0_std'] = 0.0
            features['f0_contour'] = []
        
        # No jitter/shimmer available in librosa
        features['jitter'] = 0.0
        features['shimmer'] = 0.0
        
        return features
        
    except Exception as e:
        logger.warning(f"Librosa F0 extraction failed: {e}")
        return {
            'mean_f0': 0.0, 'median_f0': 0.0, 'f0_std': 0.0, 'f0_contour': [],
            'jitter': 0.0, 'shimmer': 0.0
        }


def _empty_prosody_features() -> Dict[str, Union[float, List[float]]]:
    """Return empty prosody features for failed extractions."""
    return {
        'duration': 0.0, 'mean_rms': 0.0, 'rms_std': 0.0, 'zcr_mean': 0.0,
        'mean_f0': 0.0, 'median_f0': 0.0, 'f0_std': 0.0, 'f0_contour': [],
        'tempo_estimate': 0.0, 'speaking_rate': 0.0, 'jitter': 0.0, 'shimmer': 0.0,
        'pause_before': 0.0, 'pause_after': 0.0
    }


def calculate_pauses(alignments: List[Dict]) -> List[Dict]:
    """Calculate pause durations between sentences."""
    for i, alignment in enumerate(alignments):
        # Pause before
        if i > 0:
            pause_before = alignment['start'] - alignments[i-1]['end']
            alignment['pause_before'] = max(0.0, pause_before)
        else:
            alignment['pause_before'] = 0.0
        
        # Pause after
        if i < len(alignments) - 1:
            pause_after = alignments[i+1]['start'] - alignment['end']
            alignment['pause_after'] = max(0.0, pause_after)
        else:
            alignment['pause_after'] = 0.0
    
    return alignments


def create_visualization(results: List[Dict], output_path: str):
    """Create scatter plots of valence vs prosody features."""
    if not results:
        return
    
    # Extract data
    valences = [r['valence'] for r in results if 'valence' in r]
    f0_means = [r['mean_f0'] for r in results if r['mean_f0'] > 0]
    rms_means = [r['mean_rms'] for r in results]
    
    if len(valences) != len(f0_means) or len(valences) != len(rms_means):
        logger.warning("Mismatched data lengths for visualization")
        return
    
    # Create plots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Valence vs F0
    ax1.scatter(valences, f0_means, alpha=0.7)
    ax1.set_xlabel('Valence Score')
    ax1.set_ylabel('Mean F0 (Hz)')
    ax1.set_title('Valence vs Mean F0')
    ax1.grid(True, alpha=0.3)
    
    # Valence vs RMS
    ax2.scatter(valences, rms_means, alpha=0.7, color='orange')
    ax2.set_xlabel('Valence Score')
    ax2.set_ylabel('Mean RMS Energy')
    ax2.set_title('Valence vs Mean RMS Energy')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save plot
    plot_path = output_path.replace('.json', '_plot.png')
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    logger.info(f"Visualization saved to {plot_path}")
    plt.close()


def main():
    parser = argparse.ArgumentParser(description='Audio Prosody Analysis with Valence Correlation')
    parser.add_argument('--audio', required=True, help='Audio file path (wav/mp3)')
    parser.add_argument('--transcript', required=True, help='Transcript file (one sentence per line)')
    parser.add_argument('--valence', required=True, help='Valence scores (JSON/CSV)')
    parser.add_argument('--out', default='prosody_report.json', help='Output file path')
    
    args = parser.parse_args()
    
    # Validate inputs
    for path in [args.audio, args.transcript, args.valence]:
        if not Path(path).exists():
            logger.error(f"Input file not found: {path}")
            sys.exit(1)
    
    try:
        # Load inputs
        logger.info("Loading inputs...")
        sentences = load_transcript(args.transcript)
        valence_scores = load_valence_scores(args.valence)
        
        # Validate alignment between transcript and valence
        if len(sentences) != len(valence_scores):
            logger.warning(f"Mismatch: {len(sentences)} sentences vs {len(valence_scores)} valence scores")
        
        # Perform forced alignment
        logger.info("Performing forced alignment...")
        alignments = perform_forced_alignment(args.audio, sentences)
        
        # Calculate pauses
        alignments = calculate_pauses(alignments)
        
        # Extract prosody features
        logger.info("Extracting prosody features...")
        results = []
        
        for i, (sentence, alignment) in enumerate(zip(sentences, alignments)):
            logger.info(f"Processing sentence {i+1}/{len(sentences)}")
            
            # Extract prosody
            prosody = extract_prosody_features(
                args.audio, 
                alignment['start'], 
                alignment['end']
            )
            
            # Combine all data
            result = {
                'index': i,
                'text': sentence,
                'valence': valence_scores.get(i, 0.0),
                'start_time': alignment['start'],
                'end_time': alignment['end'],
                **prosody
            }
            
            results.append(result)
        
        # Save JSON output
        with open(args.out, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {args.out}")
        
        # Save CSV summary
        csv_path = args.out.replace('.json', '.csv')
        df = pd.DataFrame(results)
        df.to_csv(csv_path, index=False)
        logger.info(f"CSV summary saved to {csv_path}")
        
        # Create visualization
        create_visualization(results, args.out)
        
        # Print summary table
        print("\n" + "="*80)
        print("PROSODY ANALYSIS SUMMARY")
        print("="*80)
        print(f"{'Idx':<3} {'Valence':<8} {'F0(Hz)':<8} {'RMS':<8} {'Duration':<8} {'Text':<30}")
        print("-"*80)
        
        for r in results[:10]:  # Show first 10
            text_preview = r['text'][:27] + "..." if len(r['text']) > 30 else r['text']
            print(f"{r['index']:<3} {r['valence']:<8.2f} {r['mean_f0']:<8.1f} "
                  f"{r['mean_rms']:<8.3f} {r['duration']:<8.2f} {text_preview:<30}")
        
        if len(results) > 10:
            print(f"... and {len(results) - 10} more sentences")
        
        print(f"\nTotal sentences processed: {len(results)}")
        print(f"Average F0: {np.mean([r['mean_f0'] for r in results if r['mean_f0'] > 0]):.1f} Hz")
        print(f"Average valence: {np.mean([r['valence'] for r in results]):.2f}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Example usage demonstration
    if len(sys.argv) == 1:
        print("Audio Prosody Analysis Script")
        print("="*40)
        print("Usage:")
        print("  python prosody_analysis.py --audio audio.wav --transcript sentences.txt --valence valence.json")
        print("\nExample files:")
        print("  sentences.txt: One sentence per line")
        print("  valence.json: {\"0\": 0.2, \"1\": -0.5, \"2\": 0.8}")
        print("  valence.csv: index,valence\\n0,0.2\\n1,-0.5\\n2,0.8")
        print("\nRequired packages:")
        print("  pip install whisperx librosa parselmouth numpy pandas matplotlib soundfile")
        sys.exit(0)
    
    main()
