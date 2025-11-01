#!/usr/bin/env python3
"""
Text Valence Computation for Audio Journaling App

Computes semantic positivity (valence) from text transcripts.
Maps emotional tone to numerical values for combination with audio arousal data.
"""

import re
import sys
import json
from typing import Dict, List, Optional
import nltk
import os
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Download required NLTK data if not present
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

class ValenceAnalyzer:
    """Analyzes text valence using VADER sentiment analysis."""
    
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        # Common filler words to remove for cleaner analysis
        self.filler_words = {
            'um', 'uh', 'er', 'ah', 'like', 'you know', 'i mean', 
            'sort of', 'kind of', 'basically', 'actually', 'literally'
        }
    
    def clean_text(self, text: str) -> str:
        """Clean text by removing filler words and normalizing."""
        # Convert to lowercase
        text = text.lower().strip()
        
        # Remove filler words
        for filler in self.filler_words:
            text = re.sub(r'\b' + re.escape(filler) + r'\b', '', text)
        
        # Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def split_sentences(self, text: str) -> List[str]:
        """Split text into sentences using NLTK."""
        try:
            sentences = nltk.sent_tokenize(text)
            return [s.strip() for s in sentences if s.strip()]
        except Exception:
            # Fallback to simple splitting if NLTK fails
            sentences = re.split(r'[.!?]+', text)
            return [s.strip() for s in sentences if s.strip()]
    
    def compute_sentence_valence(self, sentence: str) -> Dict[str, float]:
        """Compute valence for a single sentence using VADER."""
        scores = self.analyzer.polarity_scores(sentence)
        return {
            'compound': scores['compound'],  # This is our valence_raw (-1 to 1)
            'pos': scores['pos'],
            'neu': scores['neu'], 
            'neg': scores['neg'],
            'length': len(sentence.split())
        }
    
    def aggregate_valence(self, sentence_scores: List[Dict[str, float]]) -> Dict[str, float]:
        """Aggregate valence scores across sentences, weighted by length."""
        if not sentence_scores:
            return {'valence_raw': 0.0, 'confidence': 0.0}
        
        total_weight = sum(score['length'] for score in sentence_scores)
        if total_weight == 0:
            return {'valence_raw': 0.0, 'confidence': 0.0}
        
        # Weighted average of compound scores
        weighted_valence = sum(
            score['compound'] * score['length'] 
            for score in sentence_scores
        ) / total_weight
        
        # Confidence is the absolute value of valence (stronger sentiment = higher confidence)
        confidence = abs(weighted_valence)
        
        return {
            'valence_raw': weighted_valence,
            'confidence': confidence
        }

def compute_valence(text: str, model: str = "vader") -> Dict[str, float]:
    """
    Compute text valence from transcript.
    
    Args:
        text: Input text transcript
        model: Analysis model ("vader" only for now)
    
    Returns:
        Dictionary with:
        - valence_raw: Raw valence score (-1 to 1)
        - valence_norm: Normalized valence (0 to 1) 
        - confidence: Confidence in the measurement (0 to 1)
    """
    if model != "vader":
        raise ValueError("Only 'vader' model is currently supported")
    
    if not text or not text.strip():
        return {
            'valence_raw': 0.0,
            'valence_norm': 0.5,
            'confidence': 0.0
        }
    
    analyzer = ValenceAnalyzer()
    
    # Clean the input text
    cleaned_text = analyzer.clean_text(text)
    
    # Split into sentences
    sentences = analyzer.split_sentences(cleaned_text)
    
    # Compute valence for each sentence
    sentence_scores = []
    for sentence in sentences:
        if sentence:  # Skip empty sentences
            score = analyzer.compute_sentence_valence(sentence)
            sentence_scores.append(score)
    
    # Aggregate scores
    result = analyzer.aggregate_valence(sentence_scores)
    
    # Normalize valence from (-1, 1) to (0, 1)
    valence_norm = (result['valence_raw'] + 1.0) / 2.0
    
    return {
        'valence_raw': result['valence_raw'],
        'valence_norm': valence_norm,
        'confidence': result['confidence']
    }

def analyze_transcript_detailed(text: str) -> Dict:
    """
    Detailed analysis including per-sentence breakdown.
    Useful for debugging and understanding the analysis.
    """
    analyzer = ValenceAnalyzer()
    cleaned_text = analyzer.clean_text(text)
    sentences = analyzer.split_sentences(cleaned_text)
    
    sentence_details = []
    for sentence in sentences:
        if sentence:
            score = analyzer.compute_sentence_valence(sentence)
            sentence_details.append({
                'text': sentence,
                'valence': score['compound'],
                'length': score['length'],
                'pos': score['pos'],
                'neg': score['neg'],
                'neu': score['neu']
            })
    
    overall = compute_valence(text)
    
    return {
        'overall': overall,
        'sentences': sentence_details,
        'cleaned_text': cleaned_text,
        'sentence_count': len(sentence_details)
    }

def main():
    """CLI interface for testing valence computation."""
    if len(sys.argv) > 1:
        # Use command line argument
        text = ' '.join(sys.argv[1:])
    else:
        # Read from stdin
        eof_hint = "Ctrl+Z then Enter" if os.name == "nt" else "Ctrl+D"
        print(f"Enter text to analyze ({eof_hint} to finish):")
        text = sys.stdin.read().strip()
    
    if not text:
        print("No text provided.", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Compute valence
        result = compute_valence(text)
        
        # Pretty print results
        print(json.dumps(result, indent=2))
        
        # Also show detailed analysis
        print("\n--- Detailed Analysis ---")
        detailed = analyze_transcript_detailed(text)
        
        print(f"Cleaned text: {detailed['cleaned_text']}")
        print(f"Sentences analyzed: {detailed['sentence_count']}")
        
        for i, sentence in enumerate(detailed['sentences'], 1):
            print(f"  {i}. \"{sentence['text']}\" -> valence: {sentence['valence']:.3f}")
        
    except Exception as e:
        print(f"Error analyzing text: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
