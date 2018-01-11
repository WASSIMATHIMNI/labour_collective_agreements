import os
import pickle

DATA_DIR = "data/texts-pkls"
pdfs = {}
for name in sorted(os.listdir(DATA_DIR)):
    filename, file_extension = os.path.splitext(name)
    if file_extension == ".pkl":
        path ="{}/{}".format(DATA_DIR,name)
        pdfs[path] = pickle.load(open(path,'rb'))


def get_pdf(pdf):
    return pdfs[pdf]
