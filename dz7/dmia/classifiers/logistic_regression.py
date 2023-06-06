# -*- coding: utf-8 -*-
#pylint_disable=too-many-arguments
#pylint_disable=too-many-locals
"""
Logistic regression logic
"""
import numpy as np
from joblib.numpy_pickle_utils import xrange
from scipy import sparse
from scipy.sparse import spmatrix


class LogisticRegression:
    """
    Class for training our network on given data
    """
    def __init__(self):
        self.weight = None
        self.loss_history = None

    def train(self, bias_x, bias_y, learning_rate=1e-3, reg=1e-5, num_iters=100,
              batch_size=200, verbose=False):
        """
        Train this classifier using stochastic gradient descent.

        Inputs:
        - bias_x: N x D array of training data. Each training point is a
        D-dimensional column.
        - bias_y: 1-dimensional array of length N with labels 0-1, for 2 classes.
        - learning_rate: (float) learning rate for optimization.
        - reg: (float) regularization strength.
        - num_iters: (integer) number of steps to take when optimizing
        - batch_size: (integer) number of training examples
        to use at each step.
        - verbose: (boolean) If true, print progress during optimization.

        Outputs:
        A list containing the value of the loss function at
        each training iteration.
        """
        # Add a column of ones to X for the bias sake.
        bias_x = LogisticRegression.append_biases(bias_x)
        num_train, dim = bias_x.shape
        if self.weight is None:
            # lazily initialize weights
            self.weight = np.random.randn(dim) * 0.01

        # Run stochastic gradient descent to optimize W
        self.loss_history = []
        for _iter in xrange(num_iters):
            #########################################################################
            # Sample batch_size elements from the training data and their           #
            # corresponding labels to use in this round of gradient descent.        #
            # Store the data in X_batch and their corresponding labels in           #
            # y_batch; after sampling X_batch should have shape (batch_size, dim)   #
            # and y_batch should have shape (batch_size,)                           #
            #                                                                       #
            # Hint: Use np.random.choice to generate indices. Sampling with         #
            # replacement is faster than sampling without replacement.              #
            #########################################################################
            indexes = np.random.choice(num_train, batch_size)
            x_batch = bias_x[indexes, :]
            y_batch = bias_y[indexes]
            #########################################################################
            #                       END OF YOUR CODE                                #
            #########################################################################

            # evaluate loss and gradient
            loss, gradient_w = self.loss(x_batch, y_batch, reg)
            self.loss_history.append(loss)
            # perform parameter update
            #########################################################################
            # Update the weights using the gradient and the learning rate.          #
            #########################################################################

            self.weight -= learning_rate * gradient_w

            #########################################################################
            #                       END OF YOUR CODE                                #
            #########################################################################

            if verbose and _iter % 100 == 0:
                print ('iteration %s / %s: loss %s', _iter, num_iters, loss)

        return self

    def predict_proba(self, x_bias, append_bias=False):
        """
        Use the trained weights of this linear classifier to predict probabilities for
        data points.

        Inputs:
        - X: N x D array of data. Each row is a D-dimensional point.
        - append_bias: bool. Whether to append bias before predicting or not.

        Returns:
        - y_proba: Probabilities of classes for the data in X. y_pred is a 2-dimensional
          array with a shape (N, 2), and each row is a distribution of
          classes [prob_class_0, prob_class_1].
        """
        if append_bias:
            x_bias = LogisticRegression.append_biases(x_bias)
        ###########################################################################
        # Implement this method. Store the probabilities of classes in y_proba.   #
        # Hint: It might be helpful to use np.vstack and np.sum                   #
        ###########################################################################

        proba = self.sigmoid(x_bias.dot(self.weight.T))
        y_proba = np.vstack((1 - proba, proba)).T

        ###########################################################################
        #                           END OF YOUR CODE                              #
        ###########################################################################
        return y_proba

    def predict(self, x_bias):
        """
        Use the ```predict_proba``` method to predict labels for data points.

        Inputs:
        - x_bias: N x D array of training data. Each column is a D-dimensional point.

        Returns:
        - y_pred: Predicted labels for the data in X. y_pred is a 1-dimensional
          array of length N, and each element is an integer giving the predicted
          class.
        """

        ###########################################################################
        # Implement this method. Store the predicted labels in y_pred.            #
        ###########################################################################
        y_proba = self.predict_proba(x_bias, append_bias=True)
        y_pred = np.argmax(y_proba, axis=1)

        ###########################################################################
        #                           END OF YOUR CODE                              #
        ###########################################################################
        return y_pred

    def loss(self, x_batch, y_batch, reg):
        """Logistic Regression loss function
        Inputs:
        - X: N x D array of data. Data are D-dimensional rows
        - y: 1-dimensional array of length N with labels 0-1, for 2 classes
        Returns:
        a tuple of:
        - loss as single float
        - gradient with respect to weights w; an array of same shape as w
        Loss = -(1 / m) * sum(yi * log(pi) + (1 - yi) * log(1 - pi))
        Grad = (1/m) (pi - yi) * xi"""
        modus = x_batch.shape[0]
        pi_number = self.sigmoid(x_batch.dot(self.weight))

        loss = -np.dot(y_batch, np.log(pi_number)) - np.dot((1 - y_batch),
                                                     np.log(1.0-pi_number))
        loss = loss / modus

        dual_weight = (1 / modus) * (pi_number - y_batch) * x_batch

        # Right now the loss is a sum over all training examples, but we want it
        # to be an average instead so we divide by num_train.
        # Note that the same thing must be done with gradient.


        # Add regularization to the loss and gradient.
        # Note that you have to exclude bias term in regularization.

        loss += (reg / (2.0 * modus)) * np.dot(self.weight[:-1], self.weight[:-1])
        dual_weight[:-1] = dual_weight[:-1] + (reg * self.weight[:-1]) / modus

        return loss, dual_weight

    @staticmethod
    def append_biases(x_bias):
        """
        Append bias to plot
        """
        return sparse.hstack((x_bias, np.ones(x_bias.shape[0])[:, np.newaxis])).tocsr()

    def sigmoid(self, x_bias):
        """
        Calculate 1 / exp of bias
        """
        return 1.0 / (1.0 + np.exp(-x_bias))

    @staticmethod
    def safe_sparse_dot(a_dot, b_dot, dense_output=False):
        """
        Set matrix to array on a and b dots
        """
        if isinstance(a_dot, spmatrix) or isinstance(b_dot, spmatrix):
            ret = a_dot * b_dot
            if dense_output and hasattr(ret, "toarray"):
                ret = ret.toarray()
            return ret
        return np.dot(a_dot, b_dot)
