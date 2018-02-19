#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 24 10:49:07 2017

@author: berube

This code downloads all collective agreements from Negotech and runs pdftotext on them. The code needs to have an internet connection to work.
It also downloads the metadata linked to the collective agreements in file metadata.txt
Variables to be modified:

Type of subset to be selected in level (line 48): #0:Federal+active, 1:All active, 2:All
All collective agreements will be sotcked in list form in pickle format in the folder in variable pklpath (line 42)
pdftotext and pdfinfo executables must be in directory in the variable execpath (line 43)
    both can be downloaded through the Windows xpf tools at http://www.xpdfreader.com/download.html  --  http://www.xpdfreader.com/dl/xpdf-tools-win-4.00.zip
"""
import os
import subprocess
import pickle
from datetime import datetime
import urllib.request

def nopagepdf(filepath):
    "Retourne le nombre de pages dans un pdf"
    global execpath

    pageline = 'Pages: 0'
    try:
        meta = subprocess.check_output([execpath+'pdfinfo',filepath],shell=True).decode("utf-8")
    except UnicodeDecodeError:
        try:
            meta = subprocess.check_output([execpath+'pdfinfo',filepath],shell=True).decode("latin-1")
        except UnicodeDecodeError:
            meta = ''
            print('ERREUR: encodage introuvable dans le metadata')
    for i in meta.split('\r\n'):
        if i[:5].lower() == 'pages':
            pageline = i
    return(int(pageline.split()[-1]))

#Path ou sauvegarder les fichier .pkl des textrip des fichiers pdf, ou chaque element de la liste correspond a une page
pklpath = 'C:\\Users\\wassim.athimni\\DOCUMENTS\\projects\\QA_collective_agreements\\prep\\data\\txt-pdftotext-fed\\'
execpath = 'C:\\Users\\wassim.athimni\\xpdf-tools-win-4.00\\bin64\\'

#Importation de la liste des URLS a télécharger et traiter
#0:Federal+active, 1:All active, 2:All
level = 0
CA_to_langact = {}
for dat in urllib.request.urlopen('http://negotech.labour.gc.ca/data/negotech_mapfile.tab'):
    ds = dat.decode('UTF-8').replace('\n','').replace('\r','').replace('\ufeff','').split('\t')
    if ds[0].isdecimal():
        CA_to_langact[ds[0]] = [ds[1] == 'Y',ds[2] == 'Y',ds[7] == 'Y']

CAkeys = CA_to_langact.keys()
urls = []
metadata = []
headerflag = True
caidx_present = set([d.split('.')[0][:-1] for d in os.listdir(pklpath)])

for dat in urllib.request.urlopen('http://negotech.labour.gc.ca/data/iris_to_negotech_extract.tab'):
    addflag = False
    ds = dat.decode('UTF-8').replace('\n','').replace('\r','').replace('\ufeff','').split('\t')
    caidx = ds[0].replace('-','')
    if headerflag:
        metadata.append('\t'.join(ds))
        headerflag = False
    if caidx.isdecimal():
        if (level == 0 and ds[29].lower() in ('active','current') and ds[5] != '30') or (level >= 1 and ds[29].lower() in ('active','current')) or level == 2:
            if caidx in CAkeys:
                cainfos = CA_to_langact[caidx]
                if cainfos[2]:
                    metadata.append('\t'.join(ds))
                    addflag = True
                    if cainfos[0]:
                        urls.append('http://negotech.labour.gc.ca/eng/agreements/'+caidx[:2]+'/'+caidx+'a.pdf')
                    if cainfos[1]:
                        urls.append('http://negotech.labour.gc.ca/fra/ententes/'+caidx[:2]+'/'+caidx+'c.pdf')
        if not addflag and caidx in caidx_present:
            metadata.append('\t'.join(ds))

with open(pklpath+'metadata.txt','w') as fo:
    fo.write('\n'.join(metadata))

#Affiche la progression à l'écran
#0: aucun affichage
#1: pourcentage + erreurs
#2: numero de la convention traitée
#3: all information
verbose = 3

if verbose >= 1:
    print(str(datetime.now()),'\tCODE START')

notfound = []
ncount = 0
dirlist = os.listdir(pklpath)
for icount,url in enumerate(urls):
    #Download du pdf
    #Progess bar
    if verbose == 1 and icount >= len(urls)*ncount/100:
        print('%i%%'%(ncount))
        ncount += 1
    if verbose >= 2:
        print('%i/%i'%(icount+1,len(urls)))
    #Test si le DL a déjà été fait
    coll = url.split('/')[-1]
    if coll.split('.')[0]+".pkl" in dirlist:
        if verbose >= 3:
            print('\tPDF déja traité:',coll)
    else:
        if verbose >= 3:
            print('\tTéléchargement du pdf:',coll)
        try:
            urllib.request.urlretrieve(url,pklpath+coll)
        except urllib.error.HTTPError as err:
            if verbose >= 1:
                print('ERREUR: PDF introuvable en ligne:',coll)
            notfound.append(coll)
            continue

        #Pdftotext sur le pdf (par page)
        colldata = []
        nopage = nopagepdf(pklpath+coll)
        if nopage == 0:
            if verbose >= 1:
                print('ERREUR: PDF vide:',coll)
            notfound.append(coll)
            p = subprocess.Popen('del '+pklpath+coll,shell=True)
            p.wait()
            continue
        if verbose >= 3:
            print('\tTraitement pdf2text de',nopage,'pages')
        #pdftotext
        for i in range(1,nopage):
            p = subprocess.Popen(execpath+'pdftotext -f %i -l %i -layout '%(i,i)+pklpath+coll+' '+pklpath+coll[:-4]+'%.4i.txt'%i)
            p.wait()
        #Lecture des données
        for i in range(1,nopage):
            with open(pklpath+coll[:-4]+'%.4i.txt'%i,'r') as f:
                colldata.append(f.read())
        #Suppression des fichiers temporaires
        for i in range(1,nopage):
            p = subprocess.Popen('del '+pklpath+coll[:-4]+'%.4i.txt'%i,shell=True)
            p.wait()
        #Ecriture du fichier pkl
        pickle.dump(colldata,open(pklpath+coll[:-4]+'.pkl','wb'))
        #Suppression du pdf
        p = subprocess.Popen('del '+pklpath+coll,shell=True)
        p.wait()

if verbose >= 1:
    print(str(datetime.now()),'\tCODE DONE')
    print(len(notfound),'pdf not found, in list "notfound"')
