
import spacy
import re

# Load spaCy's English model (download first with: python -m spacy download en_core_web_sm)
nlp = spacy.load("en_core_web_md")

nlp.max_length = 5000000  # or higher if needed

# Read the text file
with open("the story of mankind.txt", 'r', encoding='utf-8') as file:
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

print('model: medium')

if 'nephtys' in unique_lemmas:
    print("The word 'nephtys' is present in the text.")
else:
    print("The word 'nephtys' is not present in the text.")

if 'sanctify' in unique_lemmas:
    print("The word 'sanctify' is present in the text.")
else:
    print("The word 'sanctify' is not present in the text.")

if 'be' in unique_lemmas:
    print("The word 'be' is present in the text.")
else:
    print("The word 'be' is not present in the text.")
