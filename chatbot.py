#Libraries for nltk
import nltk
nltk.download('punkt')
from nltk.stem.lancaster import LancasterStemmer
stemmer=LancasterStemmer()

#Libraries for tensorflow processing
import tensorflow as tf
import numpy as np
import tflearn
import json

from google.colab import files
files.upload()

with open ('intents.json') as json_data:
  intents=json.load(json_data)

words=[]
classes=[]
documents=[]
ignore=['?']
#loop through each sentence in intents pattern
for intent in intents['intents']:
  for pattern in intent['patterns']:
    #tokenize every word in the sentence and add to word list
    word=nltk.word_tokenize(pattern)
    words.extend(word)
    #add words to documents with corresponding tag
    documents.append((word,intent['tag']))
    #add tags to classes list
    if(intent['tag'] not in classes):
      classes.append(intent['tag'])

#perform stemming, lower each word and remove duplicates
words=[stemmer.stem(w.lower()) for w in words if w not in ignore]

words=sorted(list(set(words)))
#remove duplicate classes
classes=sorted(list(set(classes)))

import random
#create training data
training=[]
output=[]
#create an empty array for output
output_empty=[0]*len(classes)

#create training set, bag of words for each sentence
for doc in documents:
  bag=[]
  pattern_words=doc[0]
  #stemming each word
  pattern_words=[stemmer.stem(word.lower()) for word in pattern_words]
  #create bag of words array
  for w in words:
    bag.append(1) if w in pattern_words else bag.append(0)

    #output is 1 for current tag and 0 for rest of the tags
    output_row=list(output_empty)
    output_row[classes.index(doc[1])]=1
    training.append([bag,output_row])

#shuffling features and turning it into np.array
random.shuffle(training)
training=np.array(training)

#creating training lists
train_x=list(training[:,0])
train_y=list(training[:,1])

#resetting underlying graph data
tf.reset_default_graph()

#Building nueral network
net= tflearn.input_data(shape=[None,len(train_x[0])])
net= tflearn.fully_connected(net,10)
net= tflearn.fully_connected(net,10)
net= tflearn.fully_connected(net,len(train_y[0]),activation='softmax')
net= tflearn.regression(net)

#defining model and setting up tensorboard
model= tflearn.DNN(net, tensorboard_dir='tflearn_logs')

#start training
model.fit(train_x,train_y,n_epoch=1000,batch_size=8,show_metric=True)
model.save('model.tflearn')

import pickle

pickle.dump({'words':words,'classes':classes,'train_x':train_x,'train_y':train_y},open('training_data',"wb"))

#restoring all the data saved
data=pickle.load(open("training_data","rb"))
words=data['words']
classes=data['classes']
train_x=data['train_x']
train_y=data['train_y']

with open('intents.json') as json_data:
  intents=json.load(json_data)

#load the saved model
model.load('./model.tflearn')

#function for tokenizing and stemming sentences
def clean_up_sentence(sentence):
  #tokenizing the pattern
  sentence_words=nltk.word_tokenize(sentence)
  #stemming each word
  sentence_words=[stemmer.stem(word.lower()) for word in sentence_words]
  return sentence_words

#returning bag of words: 0 or 1 for each word in bag that exists in sentence
def bow(sentence,words,show_details=False):
  #tokenizing the pattern
  sentence_words=clean_up_sentence(sentence)
  #generating bag of words
  bag=[0]*len(words)
  for s in sentence_words:
    for i,w in enumerate(words):
      if w==s:
        bag[i]=1
        if show_details:
          print("found in bag :%s" %w)
  return (np.array(bag))

context={}
error_threshold=0.3
def classify(sentence):
  #generate probabilities from the model
  results=model.predict([bow(sentence,words)])[0]
  #filter out predictions below a threshold
  results=[[i,r] for i,r in enumerate(results) if r>error_threshold]
  #sort by strength of probability
  results.sort(key=lambda x:x[1],reverse=True)
  return_list=[]
  for r in results:
    return_list.append((classes[r[0]],r[1]))
  #return tuple of intent and probability
  return return_list

def response(sentence,userid='123',show_details=False):
  results=classify(sentence)
  if results:
    while results:
      for i in intents['intents']:
          #find a tag matching the first result
          if i['tag']==results[0][0]:
            #set content for this intent if necessary
            if 'context_set' in i:
              if show_details:
                print('context :', i['context_set'])
                context[userid]=i['context_set']
            #check if this intent is contextual and applies to this user's conversation
            if not 'context_filter' in i or \
                (userid in context and 'context_filter' in i and i['context_filter']==context[userid]):
                if show_details:
                  print('tag: ',i[tag])
                #a random response from the intent    
                return print(random.choice(i['responses']))
      results.pop(0)



