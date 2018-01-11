# -*- coding: utf-8 -*-
"""
Created on Fri Oct 27 09:28:45 2017

@author: nicolas.berube

This code generates all necessary files que the query code and stocks them in the folder models/

This code needs the following files in the same directory of the code:
    words_dictionary.json
    liste.de.mots.francais.sansaccents.txt
    txt-pdftotext-fed/ - THIS CAN BE CHANGED WITH THE VARIABLE TEXT_DATA_DIR on line 224
        containing all .pkl files of pdftotext rips of collective agreements - created with masspdftotext.py
    models/
        an empty folder to contain calculation files
"""

from unidecode import unidecode
import pickle
import re
import json
import os
#import sys
from datetime import datetime
from gensim.models import Word2Vec
import multiprocessing
import numpy as np
from collections import Counter
#from scipy.spatial import distance
#import random
#import nltk
from sklearn.decomposition import PCA
from typing import List

# from helpers.pdfs import get_pdf

# A SIMPLE BUT TOUGH TO BEAT BASELINE FOR SENTENCE EMBEDDINGS
# Sanjeev Arora, Yingyu Liang, Tengyu Ma
# Princeton University
# convert a list of sentence with word2vec items into a set of sentence vectors
def sentence_to_vec_idx(s2v_sentences: List[List[int]], counts, embedding_matrix, a: float=1e-3,from_persisted=False,persist=False,ver=''):
    total_count = sum(counts.values())
    embedding_size = len(embedding_matrix[0])

    sentence_set = []
    for sentence in s2v_sentences:
        vs = np.zeros(embedding_size)  # add all word2vec values into one vector for the sentence
        sentence_length = len(sentence)
        for word_idx in sentence:

            # a_value could be also the tf-idf score of the word...
            # word_frequency in document set goes higher, a_value is less...
            a_value = a / (a + counts[word_idx]/total_count)  # smooth inverse frequency, (sif)
            vs = np.add(vs, np.multiply(a_value, embedding_matrix[word_idx]))  # vs += sif * word_vector

        if sentence_length != 0:
            vs = np.divide(vs, sentence_length)  # weighted average
        sentence_set.append(vs)  # add to our existing re-calculated set of sentences

    # sentence set is now ready.
    # every sentence is composed of a weighted average on the words that compose it...


    # calculate PCA of this sentence set
    if from_persisted:
        u = np.load("data/models/pca_component"+ver+".npy")
    else:
        pca = PCA(n_components=embedding_size)
        pca.fit(np.array(sentence_set))
        u = pca.components_[0]  # the PCA vector


    uT = np.transpose(u).reshape(len(u),1)
    P = np.multiply(u,uT)  # u x uT (Projection matrix onto u...)

    if persist:
        np.save("data/models/pca_component"+ver, u)

    # pad the vector?  (occurs if we have less sentences than embeddings_size)
    if len(P) < embedding_size:
        for i in range(embedding_size - len(P)):
            P = np.append(P, 0)  # add needed extension for multiplication below

    # resulting sentence vectors, vs = vs - u x uT x vs (Which is basically the substraction of v by its projection onto u)
    sentence_vecs = []
    for vs in sentence_set:
        sub = P.dot(vs)
        # sub = np.multiply(u,vs)
        vsn = np.subtract(vs, sub)
        if np.linalg.norm(vsn) != 0:
            vsn = np.divide(vsn,np.linalg.norm(vsn))
        sentence_vecs.append(vsn)

    return sentence_vecs

def filterCA(filename,english_words,french_words):
    "Importe sous format de liste [page][phrase] l'information d'une convention collective sous format tesseract .pkl (fait avec masstesseract.py) ou pdftotext .txt (fait avec masspdftotext.py)"

    if filename.split('.')[-2][-1] == 'a':
        dict_words = english_words
    elif filename.split('.')[-2][-1] == 'c':
        dict_words = french_words
    else:
        raise NameError('langue introuvable')

    #THIS NEEDS TO BE FIXED
    filename = filename.replace("texts-pdftotext-fed","texts-pkls")

    if filename.split('.')[-1] == 'pkl':
        # data = get_pdf(filename)
        data = pickle.load(open(filename,'rb'))
        data.append('.Ending final flag.')
    elif filename.split('.')[-1] == 'txt':
        with open(filename) as f:
            data = [f.read(),'.Ending final flag.']
    else:
        raise NameError('filetype introuvable')

    fdata = []
    newpage = []
    newdat = ''
    newpageflag = False
    replacelist = [['Mr.','Mr'],['Ms.','Ms'],['Mrs.','Mrs'],['Dr.','Dr']]
    for pagex in data:
        page = pagex
        for r in replacelist:
            page = page.replace(r[0],r[1])
        if newpageflag:
            fdata.append([])
        newpageflag = True
        for datx in page.replace('. ','.\n').split('\n'):
            dat = ' '.join(datx.split())
            iflag = False
            for w in re.sub('[^a-zA-Z]+',' ',unidecode(dat)).lower().split():
                if w in dict_words:
                    iflag = True
                    break
            #if line not devoid of true words
            if iflag:
                #if line should merge with previous line
                if len(newdat) > 0 and (((newdat[-1].islower() or newdat[-1] in '-):;,"\'') and (dat[0].isalpha() or dat[0].isnumeric() or dat[0] in '($"\''))  or  ((newdat[-1].isnumeric() or newdat[-1].isalpha()) and dat[0].islower())) or (dat[0].islower() and len(dat.split()[0]) > 1 and dat.split()[0] in dict_words):
                    newdat += ' '+dat
                #if line should be a new line, and previous line has to be added
                else:
                    iflag = False
                    for w in re.sub('[^a-zA-Z]+',' ',unidecode(newdat)).lower().split():
                        if w in dict_words and len(w) > 1:
                            iflag = True
                            break
                    #adding previous line only if line to be added is not single letters (devoid of information)
                    if iflag:
                        newpage.append(newdat)
                    #if newpage, adding page to data
                    if newpageflag:
                        fdata.append(newpage)
                        newpage = []
                        newpageflag = False
                    #creating new line
                    newdat = dat
    return(fdata[1:])

def cleanpassage(passage):
    "Clean une phrase (lowercase alphanum unicode) pour la rendre analysable par word2vec et sentence2vec"
    oldpassage = unidecode(passage)
    newpassage = ''
    for i,c in enumerate(oldpassage):
        if c.isalnum():
            newpassage += c
        elif c in '.,:' and i > 0 and i < len(oldpassage)-1 and oldpassage[i-1].isnumeric() and oldpassage[i+1].isnumeric():
            newpassage += c
        elif c in '-' and i > 0 and i < len(oldpassage)-1 and oldpassage[i-1].isalpha() and oldpassage[i+1].isalpha():
            newpassage += c
        elif c == '(':
            try:
                k = oldpassage[i:].index(')')+i
                addflag = True
                if k == i+1:
                    addflag = False
                for j,d in enumerate(oldpassage[i+1:k]):
                    if (not d.isalnum()) and not (d in '.' and j > 0 and j < k-i-2 and oldpassage[i+j].isnumeric() and oldpassage[i+j+2].isnumeric()) and not (d in '-' and j > 0 and j < k-i-2 and oldpassage[i+j].isalpha() and oldpassage[i+j+2].isalpha()) :
                        addflag = False
            except ValueError:
                addflag = False
            if addflag:
                newpassage += c
            else:
                newpassage += ' '
        elif c == ')':
            if '(' in newpassage:
                if ')' in newpassage:
                    if newpassage.count('(') > newpassage.count(')'):
                        newpassage += c
                    else:
                        newpassage += ' '
                else:
                    newpassage += c
            else:
                newpassage += ' '
        else:
            newpassage += ' '
    return(' '.join(newpassage.split()).lower())

if __name__ == "__main__":

    print(str(datetime.now())+'\t'+'Importation des dictionnaires')
    cwd = os.getcwd()+'/'
    #ver = str(datetime.now()).replace('.','-').replace(' ','-').replace(':','-')

    #English
    try:
        filename = cwd+"data/words_dictionary.json"
        with open(filename,"r") as english_dictionary:
            valid_words = json.load(english_dictionary)
            pickle.dump(valid_words,open('data/models/english_words.pkl','wb'))
            english_words = valid_words.keys()
    except Exception as e:
        print(str(e))

    #French
    try:
        filename = cwd+"data/liste.de.mots.francais.sansaccents.txt"
        with open(filename,"r") as french_dictionnary:
            data = french_dictionnary.read()
        valid_words = dict((el,0) for el in data.split('\n'))
        pickle.dump(valid_words,open('data/models/french_words.pkl','wb'))
        french_words = valid_words.keys()
    except Exception as e:
        print(str(e))

    #pickle.dump(english_words,open('models/english_words.pkl','wb'))
    #pickle.dump(french_words,open('models/french_words.pkl','wb'))
    #stopwords = nltk.corpus.stopwords.words('english')

    TEXT_DATA_DIR = cwd+'data/texts-pkls/'
    passages = []  # list of text samples
    text_filenames = []
    icount = 0
    ncount = 0

    print(str(datetime.now())+'\t'+'Importation des conventions collectives')
    #passage: for [agreement][page] du texte des collective agreements. Les phrases sont separes dans des sauts a la ligne \n
    for name in sorted(os.listdir(TEXT_DATA_DIR)):
        icount += 1
        if icount  > ncount*len(os.listdir(TEXT_DATA_DIR))/10:
            print('%i%%'%(ncount*10))
            ncount += 1
        if name[-4:] == '.pkl':
            #print(icount, len(sorted(os.listdir(TEXT_DATA_DIR))),name)
            path = os.path.join(TEXT_DATA_DIR, name)
            filename, file_extension = os.path.splitext(path)
            filename = filename.split("/")[-1]
            passages.append(['\n'.join(page) for page in filterCA(path,english_words,french_words)])
            text_filenames.append(filename)

    print(str(datetime.now())+'\t'+'Indexation des conventions collectives')
    #Indexation et ordonnement des passages des conventions collectives
    filename_to_idx = {filename:index for index,filename in enumerate(text_filenames)}
    idx_to_filename = {v:k for k,v in filename_to_idx.items()}
    pickle.dump(idx_to_filename,open('data/models/idx_to_filename.pkl','wb'))
    #passages_by_words: liste des passages cleanés de toutes les conventions pour word2vec. Les passages sont des listes de mots
    passages_by_words = [cleanpassage(phrase).split() for text in passages for page in text for phrase in page.split('\n')]

    print(str(datetime.now())+'\t'+'Word2vec')
    EMBEDDING_DIM = 100
    num_workers = multiprocessing.cpu_count()
    num_features = EMBEDDING_DIM
    min_word_count = 30
    context_size = 7
    seed = 23

    model = Word2Vec(
    #     bigrams[clauses_by_words],
        passages_by_words,
        seed=seed,
        workers=num_workers,
        size=num_features,
        min_count=min_word_count,
        window=context_size
                    )

    #page_list: liste des contenus des pages des conventions pour sentence2vec. Les pages sont des strings.
    #idx_to_metadata: Retourne l'index [idx_convention][no_page] de la idx_eme page de page_list
    print(str(datetime.now())+'\t'+'Indexation de Word2vec')
    page_list = []
    metadata_to_idx = {}
    for t,text in enumerate(passages):
        for p,page in enumerate(text):
            metadata_to_idx["%.4i-%.4i"%(t,p)] = len(page_list)
            page_list.append(cleanpassage(page))
    idx_to_metadata = {v:k for k,v in metadata_to_idx.items()}
    pickle.dump(idx_to_metadata,open('data/models/idx_to_metadata.pkl','wb'))


    #allvocab: to test if word exist
    #allvocab_to_idx: transform word into it's idx number for stockage purposes
    allvocab = set([word for passage in passages_by_words for word in passage])
    listvocab = list(allvocab)
    allvocab_to_idx = {listvocab[index]:index for index in range(len(listvocab))}
    pickle.dump(allvocab_to_idx,open("data/models/allvocab_to_idx.pkl",'wb'))
    #idx_to_word = {v:k for k,v in word_to_idx.items()}
    #np.save("models/idx_to_word",idx_to_word)
    del listvocab

    #wvvocab: to test if word has a vector representation (count > 30)
    #wvvocab_to_idx: to transform word into its idx number in the vector matrix embedding_matrix and in the Counter counts
    #counts: to know the number of occurences of a word
    wvwords = [word for passage in passages_by_words for word in passage if word in model.wv.vocab]
    wvvocab = set(wvwords)
    listvocab = list(wvvocab)
    wvvocab_to_idx = {listvocab[index]:index for index in range(len(listvocab))}
    pickle.dump(wvvocab_to_idx,open("data/models/wvvocab_to_idx.pkl",'wb'))
    del listvocab
    wvwords = [wvvocab_to_idx[word] for word in wvwords]
    counts = Counter(wvwords)
    del wvwords
    pickle.dump(counts,open("data/models/word_counts.pkl",'wb'))

    embedding_matrix = np.zeros((len(wvvocab), EMBEDDING_DIM))
    for word,idx in wvvocab_to_idx.items():
        embedding_matrix[idx] = model[word]
    pickle.dump(embedding_matrix,open("data/models/embedding_matrix.pkl",'wb'))


    print(str(datetime.now())+'\t'+'Sentence2vec')

    #sentence_vectors: List des vecteurs Sentenc2vec correspondant a chacune des pages. Utiliser idx_to_metadata pour la correspondance entre sentence_vectors et passages
    s2v_sentences = [[wvvocab_to_idx[word] for word in page.split() if word in wvvocab] for page in page_list]
    sentence_vectors = sentence_to_vec_idx(s2v_sentences,counts,embedding_matrix,persist=True)
    pickle.dump(sentence_vectors,open("data/models/sentence_vectors.pkl",'wb'))

    #sentence_words: liste des word_idx de wvvocab_to_idx (unique) dans la page correspondant à sentence_vectors
    #sentence_words_idx: les donnees de la n_eme page sont contenu aux positions sentence_words_idx[n] à sentence_words_idx[n+1] de sentence_words
    sentence_words = []
    sentence_words_idx = [0]
    for sentence in [[allvocab_to_idx[word] for word in page.split() if word in allvocab] for page in page_list]:
        sentence_words += list(set(sentence))
        sentence_words_idx.append(len(sentence_words))

    sentence_words = np.array(sentence_words,dtype='u4')
    sentence_words_idx = np.array(sentence_words_idx,dtype='u4')
    pickle.dump(sentence_words,open("data/models/sentence_words.pkl",'wb'))
    pickle.dump(sentence_words_idx,open("data/models/sentence_words_idx.pkl",'wb'))

    #print(str(datetime.now())+'\t'+'export page_list')
    #pickle.dump(page_list,open("models/adel_page_list.pkl",'wb'))
