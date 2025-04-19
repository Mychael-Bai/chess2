import spacy
import re
from collections import Counter
import multiprocessing

# Load spaCy's large English model
nlp = spacy.load("en_core_web_lg")

nlp.max_length = 1000000  # Reduced per chunk to save memory

# Function to process a single chunk
def process_chunk(chunk):
    # Process chunk with spaCy first
    doc = nlp(chunk, disable=["ner", "parser", "tok2vec"])
    # Extract lemmas and debug info for 'sanctifies'
    lemmas = []
    debug_info = []
    for token in doc:
        # Clean and check token
        if token.is_alpha:
            clean_text = re.sub(r'[^\w\'\s]', '', token.text.lower())
            if clean_text:  # Only process if there's text after cleaning
                lemmas.append(token.lemma_)
                if token.text.lower() == "sanctifies":
                    debug_info.append({
                        "text": token.text,
                        "lemma": token.lemma_,
                        "pos": token.pos_,
                        "tag": token.tag_
                    })
    return lemmas, debug_info

def main():
    # Read the text file
    with open("the story of mankind.txt", 'r', encoding='utf-8') as file:
        text = file.read().lower()

    # Split text into chunks
    chunk_size = 1000000  # Adjust based on memory (1M characters ~200K words)
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

    # Process chunks in parallel
    lemmas = []
    all_debug_info = []
    with multiprocessing.Pool() as pool:
        results = pool.map(process_chunk, chunks)
        for chunk_lemmas, chunk_debug in results:
            lemmas.extend(chunk_lemmas)
            all_debug_info.extend(chunk_debug)

    # Count total and unique words
    total_words = len(lemmas)
    unique_lemmas = set(lemmas)
    unique_count = len(unique_lemmas)

    print(f"Total words: {total_words}")
    print(f"Unique words (after lemmatization): {unique_count}")
    print()

    # Check for 'sanctifies' and 'sanctify'
    if 'sanctifies' in unique_lemmas:
        print("The word 'sanctifies' is present in the text.")
    else:
        print("The word 'sanctifies' is not present in the text.")

    if 'sanctify' in unique_lemmas:
        print("The word 'sanctify' is present in the text.")
    else:
        print("The word 'sanctify' is not present in the text.")

    # Print debug information for 'sanctifies'
    print("\nDebug info for 'sanctifies':")
    if all_debug_info:
        for info in all_debug_info:
            print(f"Text: {info['text']}, Lemma: {info['lemma']}, POS: {info['pos']}, Tag: {info['tag']}")
    else:
        print("No tokens found for 'sanctifies'. This suggests a tokenization or text processing issue.")

if __name__ == '__main__':
    main()