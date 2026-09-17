
""" The sklearn Naive Bayes classifier to classify the terrain data.

    The objective of this exercise is to recreate the decision
    boundary found in the lesson video, and make a plot that
    visually shows the decision boundary """

from prepData import *
from Chit.config.Visualizations.classificationVis import prettyPicture, output_image

import numpy as np
import pylab as pl

def classify(features_train, labels_train):
    """
    :param features_train:
    :param labels_train:
    :return:

    ### import the sklearn module for GaussianNB
    ### create classifier
    ### fit the classifier on the training features and labels
    ### return the fit classifier
    """

    from sklearn.naive_bayes import GaussianNB
    clf = GaussianNB()

    #from sklearn.svm import SVC
    #clf = SVC(C = 10000000000,kernel='rbf')
    clf.fit(features_train, labels_train)
    return clf


features_train, labels_train, features_test, labels_test = makeTerrainData()

### the training data (features_train, labels_train) have both "fast" and "slow" points mixed
### in together--separate them so we can give them different colors in the scatterplot,
### and visually identify them
grade_fast = [features_train[ii][0] for ii in range(0, len(features_train)) if labels_train[ii]==0]
bumpy_fast = [features_train[ii][1] for ii in range(0, len(features_train)) if labels_train[ii]==0]
grade_slow = [features_train[ii][0] for ii in range(0, len(features_train)) if labels_train[ii]==1]
bumpy_slow = [features_train[ii][1] for ii in range(0, len(features_train)) if labels_train[ii]==1]


# You will need to complete this function imported from the ClassifyNB script.
# Be sure to change to that code tab to complete this quiz.
clf = classify(features_train, labels_train)



### draw the decision boundary with the text points overlaid
prettyPicture(clf, features_test, labels_test)
output_image("test.png", "png", open("test.png", "rb").read())
