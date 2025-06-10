import json
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

with open('intents.json') as f:
    data = json.load(f)

corpus = []
tags = []

for intent in data['intents']:
    for pattern in intent['patterns']:
        corpus.append(pattern.lower())
        tags.append(intent['tag'])

vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(corpus)

model = MultinomialNB()
model.fit(X, tags)

pickle.dump(model, open('model.pkl', 'wb'))
pickle.dump(vectorizer, open('vectorizer.pkl', 'wb'))
print("Model and vectorizer saved.")
