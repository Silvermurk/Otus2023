# -*- coding: utf-8 -*-
#pylint_disable=wildcard-import
"""
Gradient check module for learning app
"""
import numpy as np
from random import randrange

from joblib.numpy_pickle_utils import xrange


def eval_numerical_gradient(f, x):
    """
  a naive implementation of numerical gradient of f at x 
  - f should be a function that takes a single argument
  - x is the point (numpy array) to evaluate the gradient at
  """

    fx_elevate = f(x)  # evaluate function value at original point
    grad = np.zeros(x.shape)
    height = 0.00001

    # iterate over all indexes in x
    it_index = np.nditer(x, flags=['multi_index'], op_flags=['readwrite'])
    while not it_index.finished:
        # evaluate function at x+h
        ix_elevated = it_index.multi_index
        x[ix_elevated] += height  # increment by h
        fxh_evaluated = f(x)  # evalute f(x + h)
        x[ix_elevated] -= height  # restore to previous value (very important!)

        # compute the partial derivative
        grad[ix_elevated] = (fxh_evaluated - fx_elevate) / height  # the slope
        print(ix_elevated, grad[ix_elevated])
        it_index.iternext()  # step to next dimension
    return grad


def grad_check_sparse(function, x_bias, analytic_grad, num_checks):
    """
    sample a few random elements and only return numerical
    in this dimensions.
    """
    height = 1e-5

    for _ in xrange(num_checks):
        ix_result = tuple([randrange(m) for m in x_bias.shape])

        x_bias[ix_result] += height  # increment by h
        fxph = function(x_bias)  # evaluate f(x + h)
        x_bias[ix_result] -= 2 * height  # increment by h
        fxmh = function(x_bias)  # evaluate f(x - h)
        x_bias[ix_result] += height  # reset

        grad_numerical = (fxph - fxmh) / (2 * height)
        grad_analytic = analytic_grad[ix_result]
        rel_error = abs(grad_numerical - grad_analytic) / (
                abs(grad_numerical) + abs(grad_analytic))
        print('numerical: %f analytic: %f, relative error: %e' % (
            grad_numerical, grad_analytic, rel_error))
