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


def get_first_intent(intents):
    if intents is None:
        return None
    return intents[0]['value'], intents[0]['confidence']


def context_nlp(sender, text):
    client = app.get_wit_client()
    resp = client.message(text)

    print resp

    if 'entities' in resp:
        entities = resp.get('entities')
        intents = entities.get('intent', None)

        if intents is None:
            return False

        intention, prob = get_first_intent(intents)
        if intention == 'greeting' and prob > 0.5:
            data = {'recipient': {'id': sender}, 'message': {'text': 'How could I help you?'}}
            app.fb_send_message(data)
            return True

        if intention != 'update_currency' and prob > 0.2:
            if 'bot_currency' in entities:
                currency_value = entities['bot_currency'][0]['value']
                profile.save_currency_preference(sender, currency_value)
                data = {'recipient': {'id': sender}, 'message': {'text': 'Got it.'}}
                app.fb_send_message(data)
                return True
    return False

