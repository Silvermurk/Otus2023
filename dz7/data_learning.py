# -*- coding: utf-8 -*-
# pylint:disable=too-many-locals
# pylint:disable=unnecessary-lambda-assignment
"""
Module to visualize, compare and learn regression app
"""
import numpy as np
import pandas as pd
import tqdm
from matplotlib import pyplot as plt
from sklearn import linear_model
from sklearn.feature_extraction.text import TfidfVectorizer

from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

from dz7.dmia.classifiers.logistic_regression import LogisticRegression
from dz7.dmia.gradient_check import grad_check_sparse


def test_data_learning():
    """
    Method for learning how learning actually works and visualize data
    """
    train_df = pd.read_csv('./data/train.csv')

    print('train_df.shape: %s', train_df.shape)
    print('train_df.Prediction.value_counts(normalize=True), %s',
          train_df.Prediction.value_counts(normalize=True))
    print('train_df.head(): %s', train_df.head())
    print('train_df.tail(): %s', train_df.tail())
    review_summaries = list(train_df['Reviews_Summary'].values)
    review_summaries = [l.lower() for l in review_summaries]
    print('review_summaries end: %s', review_summaries[:5])
    vectorizer = TfidfVectorizer()
    tfidfed = vectorizer.fit_transform(review_summaries)
    vector_x = tfidfed
    vector_y = train_df.Prediction.values
    x_train, x_test, y_train, y_test = train_test_split(
        vector_x, vector_y, train_size=0.7, random_state=42)
    x_train_sample = x_train[:10000]
    y_train_sample = y_train[:10000]
    clf = LogisticRegression()
    clf.w = np.random.randn(x_train_sample.shape[1] + 1) * 2
    loss, grad = clf.loss(
        LogisticRegression.append_biases(x_train_sample),
        y_train_sample, 0.0)
    print('loss=%s\n'
          'grad=%s', loss, grad)

    log_loss = lambda w: clf.loss(
        LogisticRegression.append_biases(x_train_sample),
        y_train_sample,
        0.0)[0]
    grad_check_sparse(log_loss, clf.w, grad, 10)
    clf = LogisticRegression()
    clf.train(x_train, y_train)
    print("Train f1-score = %s",
          accuracy_score(y_train, clf.predict(x_train)))
    print("Test f1-score = %s",
          accuracy_score(y_test, clf.predict(x_test)))

    clf = LogisticRegression()
    train_scores = []
    test_scores = []
    num_iters = 3000

    for _ in tqdm.trange(num_iters):
        clf.train(x_train,
                  y_train,
                  learning_rate=1.0,
                  num_iters=1,
                  batch_size=256,
                  reg=1e-3)
        train_scores.append(accuracy_score(y_train, clf.predict(x_train)))
        test_scores.append(accuracy_score(y_test, clf.predict(x_test)))
    # 3000 will take too much pipeline time and fail 60 sec GitHub watchdog
    clf = linear_model.SGDClassifier(
        max_iter=1000,
        random_state=42,
        loss="log",
        penalty="l2",
        alpha=1e-3,
        eta0=1.0,
        learning_rate="constant")
    clf.fit(x_train, y_train)
    print("Train accuracy = %s",
          accuracy_score(y_train, clf.predict(x_train)))
    print("Test accuracy = %s",
          accuracy_score(y_test, clf.predict(x_test)))
    assert accuracy_score(y_train, clf.predict(x_train)) > 0.8
    assert accuracy_score(y_test, clf.predict(x_test)) > 0.8
