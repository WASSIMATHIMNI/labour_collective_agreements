import pandas as pd
from flask import Flask
from flask import request
from flask import send_from_directory
from flask import jsonify
from flask import render_template
from flask import jsonify
import helpers.util as util
import helpers.sentence2vec as s2v

import numpy as np
import h5py

app = Flask(__name__)

EMBEDDING_DIM = 100
# indexes to word embeddings
# embedding_matrix = np.load("models/embedding_matrix.npy")

#word to indexes
# word_to_idx = np.load("models/word_to_idx.npy").item()

#indexed documents to search against
sentence_vectors = np.load("models/sentence_vectors.npy")
filename_to_idx = np.load("models/filename_to_idx.npy").item()
idx_to_filename = np.load("models/idx_to_filename.npy").item()
idx_to_metadata = np.load("models/idx_to_metadata.npy").item()

clean_passages = pd.read_csv("models/clean_passages.csv",header=None).values
clean_passages = clean_passages.reshape(len(clean_passages))

raw_passages = pd.read_csv("models/raw_passages.csv",header=None).values
raw_passages = raw_passages.reshape(len(raw_passages))


# h5f = h5py.File('models/clauses.h5','r')
# clauses = h5f['clauses'][:]


from scipy.spatial import distance

def retrieve_vectors_from_pdf(vectors,from_pdf):
     return [(index,vector) for index,vector in enumerate(vectors) if idx_to_filename[int(idx_to_metadata[index].split("-")[0])] == from_pdf]


def retrieve_closest_passages(vector,vectors=None,from_pdf=None,num_passages=3):
    answers = []

    if vectors is None: vectors = sentence_vectors

    if from_pdf is not None:
        vectors_idx_pairs = retrieve_vectors_from_pdf(vectors,from_pdf=from_pdf);
        vectors = [v[1] for v in vectors_idx_pairs]
        idx_to_repoidx = {idx:v[0] for idx,v in enumerate(vectors_idx_pairs)}

        if len(vectors) > 0:
            distances = distance.cdist(vectors,vector)
            closest_indexes = sorted(range(len(distances)),key= lambda k: distances[k]);
            if len(closest_indexes) > num_passages:
                for index in range(num_passages):

                    repo_idx = idx_to_repoidx[closest_indexes[index]]

                    filename_index = int(idx_to_metadata[repo_idx].split("-")[0])
                    filename = idx_to_filename[filename_index]

                    url = "http://negotech.labour.gc.ca/{}/{}/{}/{}.pdf"
                    if filename[-1] == 'a':
                        url = url.format("eng","agreements",filename[:2],filename)
                    else:
                        url = url.format("fra","conventions",filename[:2],filename)

                    answers.append({
                        "raw_passage":raw_passages[repo_idx],
                        "clean_passage":clean_passages[repo_idx],
                        "metadata":idx_to_metadata[repo_idx],
                        "pdf_url": url
                    })
    else:
        distances = distance.cdist(vectors,vector)
        closest_indexes = sorted(range(len(distances)),key= lambda k: distances[k]);
        for index in range(num_passages):

            filename_index = int(idx_to_metadata[closest_indexes[index]].split("-")[0])
            filename = idx_to_filename[filename_index]

            url = "http://negotech.labour.gc.ca/{}/{}/{}/{}.pdf"
            if filename[-1] == 'a':
                url = url.format("eng","agreements",filename[:2],filename)
            else:
                url = url.format("fra","conventions",filename[:2],filename)

            answers.append({
                "raw_passage":raw_passages[closest_indexes[index]],
                "clean_passage":clean_passages[closest_indexes[index]],
                "metadata":idx_to_metadata[closest_indexes[index]],
                "pdf_url": url
            })

    return answers



@app.route("/")
def index():
    return render_template('index.html')

@app.route("/public/<path:path>")
def send_public(path):
    return send_from_directory('public',path);

@app.route("/search_results",methods=['POST', 'GET'])
def search():

    query = str(request.args.get('query'))
    if str(request.args.get('pdf')):
        pdf = str(request.args.get('pdf'))
    else:
        pdf = None
    

    sentence = util.query_to_sentence(query)
    vector = s2v.sentence_to_vec([sentence],EMBEDDING_DIM,from_persisted=True)


    answers = retrieve_closest_passages(vector,vectors=sentence_vectors,from_pdf=pdf,num_passages=20)

    # distances = distance.cdist(sentence_vectors,vector,'euclidean');
    # closest_indexes = sorted(range(len(distances)),key= lambda k: distances[k])


    # data = [clauses[i].decode("utf-8") for i in closest_indexes[:10]]

    # get_text_from_sentence(sentence)
    # call model and retrieve responses...

    # return render_template('results.html', results = {"query":query,"data":answers});
    results = {"query":query,"data":answers}
    return jsonify(results)


if __name__ == "__main__":
    app.debug = True
    app.run()
