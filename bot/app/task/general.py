import app
import spacy
from app.core import profile

nlp = spacy.load('en')


def context_nlp(sender, text):
    doc = nlp(text)

    # apply the matching
    for w in doc:
        print w.pos_
        print w.lemma_
        if w.pos_ in (u'NN', u'NOUN') and w.lemma_ == 'currency':
            edge = w.head.right_edge
            if edge.text in ('SGD', 'USD', 'JPY', 'RMB'):
                profile.save_currency_preference(sender, edge.text)
                data = {'recipient': {'id': sender}, 'message': {'text': 'Got it.'}}
                app.fb_send_message(data)
                return True
    return False
