import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

nltk.download('vader_lexicon')

def analyze_sentiment(feedback):
    """Analyzes sentiment of feedback comments and assigns a score."""
    sia = SentimentIntensityAnalyzer()
    score = sia.polarity_scores(feedback.comments)["compound"]

    # Assign a sentiment category
    if score >= 0.05:
        feedback.sentiment = "Positive 😀"
    elif score <= -0.05:
        feedback.sentiment = "Negative 😞"
    else:
        feedback.sentiment = "Neutral 😐"

    feedback.sentiment_score = score  # Store numeric sentiment score
