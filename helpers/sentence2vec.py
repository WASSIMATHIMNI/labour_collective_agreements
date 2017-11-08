# !/usr/bin/python3

#
#  Copyright 2016 Peter de Vocht
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import numpy as np
from sklearn.decomposition import PCA
from typing import List
import pickle

word_counts = np.load("models/word_counts.npy").item()
total_count = sum(word_counts.values())


# an embedding word with associated vector
class Word:
    def __init__(self, text, vector):
        self.text = text
        self.vector = vector


# a sentence, a list of words
class Sentence:
    def __init__(self, word_list):
        self.word_list = word_list

    # return the length of a sentence
    def len(self) -> int:
        return len(self.word_list)


# todo: get the frequency for a word in a document set
def get_word_frequency(word_text):
    # probability of word in document set (the higher -> 1) ~ The word frequency in the set
    return word_counts[word_text]/total_count


# A SIMPLE BUT TOUGH TO BEAT BASELINE FOR SENTENCE EMBEDDINGS
# Sanjeev Arora, Yingyu Liang, Tengyu Ma
# Princeton University
# convert a list of sentence with word2vec items into a set of sentence vectors
def sentence_to_vec(sentence_list: List[Sentence], embedding_size: int, a: float=1e-3,from_persisted=False,persist=False):
    sentence_set = []
    for sentence in sentence_list:
        vs = np.zeros(embedding_size)  # add all word2vec values into one vector for the sentence
        sentence_length = sentence.len()
        for word in sentence.word_list:

            # a_value could be also the tf-idf score of the word...
            # word_frequency in document set goes higher, a_value is less...
            a_value = a / (a + get_word_frequency(word.text))  # smooth inverse frequency, (sif)


            vs = np.add(vs, np.multiply(a_value, word.vector))  # vs += sif * word_vector

        vs = np.divide(vs, sentence_length)  # weighted average
        sentence_set.append(vs)  # add to our existing re-calculated set of sentences

    # sentence set is now ready.
    # every sentence is composed of a weighted average on the words that compose it...


    # calculate PCA of this sentence set
    if from_persisted:
        u = np.load("models/pca_component.npy")
    else:
        pca = PCA(n_components=embedding_size)
        pca.fit(np.array(sentence_set))
        u = pca.components_[0]  # the PCA vector


    uT = np.transpose(u).reshape(len(u),1)
    P = np.multiply(u,uT)  # u x uT (Projection matrix onto u...)

    if persist:
        np.save("models/pca_component", u)

    # pad the vector?  (occurs if we have less sentences than embeddings_size)
    if len(P) < embedding_size:
        for i in range(embedding_size - len(P)):
            P = np.append(P, 0)  # add needed extension for multiplication below

    # resulting sentence vectors, vs = vs - u x uT x vs (Which is basically the substraction of v by its projection onto u)
    sentence_vecs = []
    for vs in sentence_set:
        sub = P.dot(vs)
        # sub = np.multiply(u,vs)
        sentence_vecs.append(np.subtract(vs, sub))

    return sentence_vecs
