from flask import render_template
from models import EmailBrain as eb

def onEmailBrainRequest():
    return render_template('index.html')


def onRetrieveSimilarEmailRequest(email):
    brain  = eb.EmailBrain()
    similar = brain.getSimilarEmails(email)
    return render_template('similaremails.html', results = similar);

def onRetrieveEmailsFromCategoryRequest(category):
    brain  = eb.EmailBrain()
    emails = brain.getEmailsFromCategory(category)
    return render_template('emails.html',results = emails)
