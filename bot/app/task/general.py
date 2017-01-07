import app
# import spacy
from app.core import profile

# nlp = spacy.load('en')

# def context_nlp(sender, text):
#     doc = nlp(text)
#
#     # apply the matching
#     for w in doc:
#         print w.pos_
#         print w.lemma_
#         if w.pos_ in (u'NN', u'NOUN') and w.lemma_ == 'currency':
#             edge = w.head.right_edge
#             if edge.text in ('SGD', 'USD', 'JPY', 'RMB'):
#                 profile.save_currency_preference(sender, edge.text)
#                 data = {'recipient': {'id': sender}, 'message': {'text': 'Got it.'}}
#                 app.fb_send_message(data)
#                 return True
#     return False


import app


def context_nlp(sender, text):
    client = app.get_wit_client()
    resp = client.message(text)
    if 'entities' in resp:
        entities = resp.get('entities')
        if 'bot_currency' in entities:
            currency_value = entities['bot_currency'][0]['value']
            intents = entities.get('intent', None)
            if intents is None:
                return False
            for intent in intents:
                if intent['value'] != 'update_currency' and intent['confidence'] < 0.2:
                    continue
                profile.save_currency_preference(sender, currency_value)
                data = {'recipient': {'id': sender}, 'message': {'text': 'Got it.'}}
                app.fb_send_message(data)
                return True
    return False

