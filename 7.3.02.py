
import spacy
import re

model = "en_core_web_lg"  # Use the large model for better accuracy
# Load spaCy's English model (download first with: python -m spacy download en_core_web_sm)
nlp = spacy.load(model)

nlp.max_length = 5000000  # or higher if needed

# Read the text file
with open("the story of mankind(the read version).txt", 'r', encoding='utf-8') as file:
    text = file.read().lower()

# Optional: Clean text with regex to remove unwanted characters (keeping letters, numbers, apostrophes)
text = re.sub(r'[^\w\'\s]', '', text)

# Process text with spaCy
# Disable unnecessary components for speed (e.g., named entity recognition)
doc = nlp(text, disable=["ner", "parser"])

# Extract lemmas (base forms) for words, ignoring whitespace tokens
lemmas = [token.lemma_ for token in doc if token.is_alpha]

# Count total words and unique words
total_words = len(lemmas)
unique_lemmas = set(lemmas)
unique_count = len(unique_lemmas)

print(f"Total words: {total_words}")
print(f"Unique words (after lemmatization): {unique_count}")
print()

print(f'model: {model}')
