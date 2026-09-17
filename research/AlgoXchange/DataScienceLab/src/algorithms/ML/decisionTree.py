"""
    Use a Decision Tree to identify emails from the Enron corpus by author:
    Sara has label 0
    Chris has label 1
"""

import sys
from time import time
sys.path.append("../tools/")
from email_preprocess import preprocess
from time import time


### features_train and features_test are the features for the training
### and testing datasets, respectively
### labels_train and labels_test are the corresponding item labels
features_train, features_test, labels_train, labels_test = preprocess()




#########################################################
### your code goes here ###
from sklearn import tree
from sklearn.metrics import accuracy_score

print features_train
print features_train[0]
print len(features_train[0])



clf = tree.DecisionTreeClassifier(min_samples_split=40)


t0 = time()
clf.fit(features_train, labels_train)
t1= time()
print "Fitting Time:", t1-t0
t2 = time()
pred = clf.predict(features_test)
t3 = time()
print "Prediction:", t3-t2

acc = accuracy_score(pred, labels_test)
print "Accuracy:", acc

#########################################################

