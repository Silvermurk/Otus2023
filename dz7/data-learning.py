import pandas as pd
import tqdm
from matplotlib import pyplot as plt
from sklearn import linear_model
from sklearn.feature_extraction.text import TfidfVectorizer

from dmia.gradient_check import *
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

from dz7.dmia.classifiers.logistic_regression import LogisticRegression


def data_learning():
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
    X = tfidfed
    y = train_df.Prediction.values
    X_train, X_test, y_train, y_test = train_test_split(X, y, train_size=0.7, random_state=42)
    X_train_sample = X_train[:10000]
    y_train_sample = y_train[:10000]
    clf = LogisticRegression()
    clf.w = np.random.randn(X_train_sample.shape[1] + 1) * 2
    loss, grad = clf.loss(LogisticRegression.append_biases(X_train_sample), y_train_sample, 0.0)

    f = lambda w: clf.loss(LogisticRegression.append_biases(X_train_sample), y_train_sample, 0.0)[0]
    grad_numerical = grad_check_sparse(f, clf.w, grad, 10)
    print("grad_numerical: %s", grad_numerical)
    clf = LogisticRegression()
    clf.train(X_train, y_train)
    print("Train f1-score = %s.3f", accuracy_score(y_train, clf.predict(X_train)))
    print("Test f1-score = %s.3f", accuracy_score(y_test, clf.predict(X_test)))

    clf = LogisticRegression()
    train_scores = []
    test_scores = []
    num_iters = 3000

    for _ in tqdm.trange(num_iters):
        clf.train(X_train, y_train, learning_rate=1.0, num_iters=1, batch_size=256, reg=1e-3)
        train_scores.append(accuracy_score(y_train, clf.predict(X_train)))
        test_scores.append(accuracy_score(y_test, clf.predict(X_test)))
        plt.figure(figsize=(10, 8))
        plt.plot(train_scores, 'r', test_scores, 'b')
    clf = linear_model.SGDClassifier(max_iter=1000, random_state=42, loss="log", penalty="l2", alpha=1e-3, eta0=1.0,
                                     learning_rate="constant")
    clf.fit(X_train, y_train)
    print("Train accuracy = %s.3f", accuracy_score(y_train, clf.predict(X_train)))
    print("Test accuracy = %s.3f", accuracy_score(y_test, clf.predict(X_test)))


if __name__ == '__main__':
    data_learning()
