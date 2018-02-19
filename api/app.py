import pickle
import pandas as pd
from flask import Flask
from flask import request
from flask import send_from_directory
from flask import jsonify
from flask import render_template
from flask import jsonify
import helpers.GenerateVectors as GV
import ast

# import helpers.sentence2vec as s2v
from nltk.corpus import stopwords
import numpy as np
import h5py

app = Flask(__name__)

# indexes to word embeddings
# embedding_matrix = np.load("models/embedding_matrix.npy")

# word to indexes
# word_to_idx = np.load("models/word_to_idx.npy").item()

# indexed documents to search against

idx_to_filename = pickle.load(open("data/models/idx_to_filename.pkl", 'rb'))
idx_to_metadata = pickle.load(open("data/models/idx_to_metadata.pkl", 'rb'))
allvocab_to_idx = pickle.load(open("data/models/allvocab_to_idx.pkl", 'rb'))
allvocab = allvocab_to_idx.keys()
wvvocab_to_idx = pickle.load(open("data/models/wvvocab_to_idx.pkl", 'rb'))
wvvocab = wvvocab_to_idx.keys()
counts = pickle.load(open("data/models/word_counts.pkl", 'rb'))
embedding_matrix = pickle.load(open("data/models/embedding_matrix.pkl", 'rb'))
sentence_vectors = pickle.load(open("data/models/sentence_vectors.pkl", 'rb'))
sentence_words = pickle.load(open("data/models/sentence_words.pkl", 'rb'))
sentence_words_idx = pickle.load(open("data/models/sentence_words_idx.pkl", 'rb'))
english_words = pickle.load(open("data/models/english_words.pkl", 'rb')).keys()
french_words = pickle.load(open("data/models/french_words.pkl", 'rb')).keys()

EMBEDDING_DIM = 100
NUM_ANSWERS = 10
TEXT_DATA_DIR = 'data/txt-pdftotext-fed/'



# NICOLAS PART

def query_to_vector(text):
    global wvvocab_to_idx, wvvocab
    global counts, embedding_matrix

    sentence_idx = [wvvocab_to_idx[word] for word in GV.cleanpassage(text).split() if word in wvvocab]
    return(GV.sentence_to_vec_idx([sentence_idx],counts,embedding_matrix,from_persisted=True))


def distdot(x,y):
    a = np.empty((len(x),len(y)))
    for i,xi in enumerate(x):
        for j,yj in enumerate(y):
            if np.linalg.norm(xi) == 0 or np.linalg.norm(yj) == 0:
                a[i,j] = -1
            else:
                a[i,j] = np.dot(xi,yj)
    return(-a)


def ngram_positions(ngram,phrase):
    "Retourne la ou les positions des ngrams dans la phrase"
    positions = []
    index = 0
    while index < len(phrase):
        index = phrase.find(ngram, index)
        if index == -1:
            break
        positions.append([index,index+len(ngram)])
        index += 1
    return(positions)


def list_in_array(lis,vec):
    includedflag = False
    for i in np.where(vec == lis[0])[0]:
        if includedflag:
            break
        includedflag = True
        if i + len(lis) - 1 <= len(vec):
            for j,m in enumerate(lis[1:]):
                if vec[i+j+1] != m:
                    includedflag = False
                    break
    return(includedflag)


def fuse_positions(positions):
    fpos = sorted(positions,key=lambda k:k[0])
    i = 1
    while i < len(fpos):
        if fpos[i][0] <= fpos[i-1][1]:
            fpos[i-1][1] = max(fpos[i-1][1],fpos[i][1])
            del fpos[i]
        else:
            i += 1
    return(fpos)

def retrieve_closest_passages_indexes(query, from_pdfs=None, idx_true=None):
    "retourne la liste des num_passages les plus proches de la query parmis les sentence_vectors."
    # from_pdf: liste de pdf. Seulement parmis les vectors du code pdf fourni (format idx_to_filename).
    # idx_true: Passage recherché (format int idx de la liste pages_list), si fourni, retourne aussi la position dans les queries de la vraie réponse dans la variable position_true.
    global sentence_vectors, sentence_words, sentence_words_idx
    global idx_to_filename, idx_to_metadata, allvocab_to_idx, allvocab, wvvocab_to_idx, wvvocab
    global counts, embedding_matrix
    global position_true

    global indexes, filtered_vectors, closest_indexes, CAorder, CAdord

    query_idx = []
    for i,s in enumerate(query.split('"')):
        if i%2 == 0:
            query_idx += [[allvocab_to_idx[word]] for word in GV.cleanpassage(s).split() if word in allvocab]
        else:
            query_idx.append([allvocab_to_idx[word] for word in GV.cleanpassage(s).split() if word in allvocab])

    indexes = []
    filtered_vectors = []

    if from_pdfs is not None: pdf_list = set([x.replace('-','') for x in from_pdfs])
    else: pdf_list = set(idx_to_filename.values())

    for i, v in enumerate(sentence_vectors):
        if idx_to_filename[int(idx_to_metadata[i].split("-")[0])] in pdf_list:
            grepsome = 0
            for words_idx in query_idx:
                if list_in_array(words_idx,sentence_words[sentence_words_idx[i]:sentence_words_idx[i+1]]):
                    grepsome += 1
            filtered_vectors.append(v)
            indexes.append([i, len(indexes), grepsome, int(idx_to_metadata[i].split('-')[0])])

    if len(filtered_vectors) == 0:
        print('ERREUR: pdf(s) introuvable:', ' '.join(from_pdfs))
        return([])

    vector = query_to_vector(query)
    distances = distdot([vector], filtered_vectors)[0]


    closest_indexes = sorted(indexes, key=lambda k: (-k[2], distances[k[1]]))
    if idx_true is not None:
        position_true = list(map(list, zip(*closest_indexes)))[0].index(idx_true) + 1

    CAorder = list(OrderedDict.fromkeys(list(map(list, zip(*closest_indexes)))[3]))
    CAdord = {}
    for i,d in enumerate(CAorder):
        CAdord[d] = i
    for i in range(len(indexes)):
        indexes[i][3] = CAdord[indexes[i][3]]

    closest_indexes = sorted(indexes, key=lambda k: (k[3],-k[2], distances[k[1]]))

    answers = []
    ans = [[closest_indexes[0][0]],[],[]]
    for i in range(1,len(closest_indexes)+1):
        if i == len(closest_indexes):
            answers.append(ans)
        elif i != 0 and (closest_indexes[i-1][3] != closest_indexes[i][3]):
            answers.append(ans)
            ans = [[closest_indexes[i][0]],[],[]]
        elif closest_indexes[i][2] != 0:
            ans[1].append(closest_indexes[i][0])
        else:
            ans[2].append(closest_indexes[i][0])

    #answers = list(map(list, zip(*closest_indexes)))[0]

    return answers

# returns the text from a list on indexes
def get_closest_passages(query, answers, num_answers=NUM_ANSWERS):
    global idx_to_metadata, idx_to_filename
    global TEXT_DATA_DIR
    global english_words
    global french_words

    if num_answers == None: num_answers = len(answers)

    metalist = [(int(idx_to_metadata[idx].split('-')[0]),int(idx_to_metadata[idx].split('-')[1])) for idx in answers][:num_answers]
    pdflist = list(set(list(map(list, zip(*metalist)))[0]))

    textCA = []
    for pdf in pdflist:
        textCA.append(GV.filterCA(TEXT_DATA_DIR+idx_to_filename[pdf]+'.pkl',english_words,french_words))

    results = []
    for meta in metalist:
        text = '\n'.join(textCA[pdflist.index(meta[0])][meta[1]])
        cleantext = unidecode(text).lower()
        highlight_pos = []
        for word in GV.cleanpassage(query).split():
            highlight_pos += ngram_positions(word,cleantext)
            highlight_pos = fuse_positions(highlight_pos)
        results.append([idx_to_filename[meta[0]]+'-%i'%meta[1],text,highlight_pos])

    urls = []
    for result in results:
        filename = result[0]
        url = "http://negotech.labour.gc.ca/{}/{}/{}/{}.pdf"
        if filename.split("-")[0][-1] == 'a':
            url = url.format("eng", "agreements",filename[:2], filename)
        else:
            url = url.format("fra", "conventions",filename[:2], filename)

        urls.append(url)

    response = [{"metadata":result[0], "raw_passage":result[1],"pdf_url":urls[index],"highlights":result[2]} for index,result in enumerate(results)]
    return response


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/public/<path:path>")
def send_public(path):
    return send_from_directory('public', path)


# this is called when the user searches for a question
# @app.route("/search_results", methods=['POST', 'GET'])
# def search():
#
#     query = str(request.args.get('query'))
#
#     pdf = None
#     if request.args.get('pdf') is not None:
#         pdf = str(request.args.get('pdf'))
#
#     num_results = 25  # str(request.args.get("num_results"))
#     is_grepped = True  # str(request.args.get("with_grep"))
#
#     sentence = util.query_to_sentence(query)
#     vector = s2v.sentence_to_vec(
#         [sentence], EMBEDDING_DIM, from_persisted=True)
#
#     answers = None
#
#     if is_grepped:
#
#         # remove stop words from query
#         query_words = query.split(" ")
#         filtered_words = [
#             word for word in query_words if word not in stopwords.words('english')]
#         answers = retrieve_closest_passages_indexes(
#             vector, vectors=sentence_vectors, from_pdf=pdf, num_passages=len(sentence_vectors) - 1)
#
#         grepped_answers = []
#         ungrepped_answers = []
#
#         for answer in answers:
#             if any(word in answer["clean_passage"] for word in filtered_words):
#                 grepped_answers.append(answer)
#
#             else:
#                 ungrepped_answers.append(answer)
#
#         # if number of grepped_answers is smaller than expected number of results
#         if len(grepped_answers) < num_results:
#             answers = grepped_answers + ungrepped_answers
#             answers = answers[:num_results]
#
#         else:
#             answers = grepped_answers[:num_results]
#
#     else:
#         answers = retrieve_closest_passages_indexes(
#             vector, vectors=sentence_vectors, from_pdf=pdf, num_passages=num_results)
#
#     # distances = distance.cdist(sentence_vectors,vector,'euclidean');
#     # closest_indexes = sorted(range(len(distances)),key= lambda k: distances[k])
#
#     # data = [clauses[i].decode("utf-8") for i in closest_indexes[:10]]
#
#     # get_text_from_sentence(sentence)
#     # call model and retrieve responses...
#
#     # return render_template('results.html', results = {"query":query,"data":answers});
#     results = {"query": query, "data": answers}
#     return jsonify(results)
#


@app.route("/search_results", methods=['POST', 'GET'])
def search():

    query = str(request.args.get('query'))

    page = str(request.args.get('query'))
    if page is None: page = 1

    if request.args.get('pdfs') is not None:
        pdfs = ast.literal_eval(request.args.get('pdfs'));

    answer_indexes = retrieve_closest_passages_indexes(query,from_pdfs=pdfs)[(page-1)*NUM_ANSWERS:page*NUM_ANSWERS]
    displayed_indexes = [answer[0][0] for answer in answer_indexes]

    answers = get_closest_passages(query,displayed_indexes)

    results = {"query": query, "data": answers,"indexes":answer_indexes}

    return jsonify(results)


@app.route("passage_indexes",methods = ["POST","GET"])
def passage_indexes():

    query = str(request.args.get('query'))

    if request.args.get('indexes') is not None:
        indexes = ast.literal_eval(request.args.get('indexes'));
        answers = get_closest_passages(query,indexes)
        results = {"query": query, "data": answers}
        return jsonify(results)

    else:
        return jsonify({"error":"indexes input missing"})
    #return the information on passage indexes


# this is to be used for the next,previous page buttons...
@app.route("/answers", methods=['POST', 'GET'])
def get_answers_for_indexes():

    answer_ids = ast.literal_eval(request.args.get('ids'));
    answers = get_closest_passages(answer_ids)

    results = {"data": answers}
    return jsonify(results)




@app.route("/", methods=['POST', 'GET'])
def get_meta_data():
    pdf = str(request.args.get('pdf'))

    results = {"pdf": pdf}
    return jsonify(results)


if __name__ == "__main__":
    app.debug = True
    app.run()
