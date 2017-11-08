import re
import numpy as np
import helpers.sentence2vec as s2v

EMBEDDING_DIM = 100

# indexes to word embeddings
embedding_matrix = np.load("models/embedding_matrix.npy")

#word to indexes
word_to_idx = np.load("models/word_to_idx.npy").item()

def get_text_from_sentence(sentence):
    return [word.text for word in sentence.word_list]

def query_to_sentence(text):
    text = text.lower()
    sentence = re.sub("[^\w]", " ",  text).split()
    embeddings = [s2v.Word("", np.zeros(EMBEDDING_DIM))] * len(sentence)
    for i,word in enumerate(sentence):
        if word in word_to_idx:
            embeddings[i] = s2v.Word(word,embedding_matrix[word_to_idx[word]])

    return s2v.Sentence(embeddings)
