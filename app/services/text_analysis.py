# Placeholder text analysis utilities. Install textblob for basic sentiment.
from textblob import TextBlob

def sentiment(text: str) -> dict:
    t = TextBlob(str(text))
    return {'polarity': t.sentiment.polarity, 'subjectivity': t.sentiment.subjectivity}

def summarize(text: str, max_sentences: int = 2) -> str:
    s = str(text).split('.')
    return '.'.join(s[:max_sentences]).strip() + '.'
