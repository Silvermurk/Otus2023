# -*- coding: utf-8 -*-
import numpy as np
import pylab as plt
from matplotlib.colors import ListedColormap

cmap_light = ListedColormap(['#FFAAAA', '#AAFFAA', '#AAAAFF'])
cmap_bold = ListedColormap(['#FF0000', '#00FF00', '#0000FF'])


def plot_surface(X, y, clf):
    """
    Mathlab surface plotting
    """
    height = 0.2
    x_min, x_max = X[:, 0].min() - 1, X[:, 0].max() + 1
    y_min, y_max = X[:, 1].min() - 1, X[:, 1].max() + 1
    xx_coords, yy_coords = np.meshgrid(np.arange(x_min, x_max, height),
                                       np.arange(y_min, y_max, height))
    Z_predict = clf.predict(np.c_[xx_coords.ravel(), yy_coords.ravel()])

    Z = Z_predict.reshape(xx_coords.shape)
    plt.figure(figsize=(8, 8))
    plt.pcolormesh(xx_coords, yy_coords, Z, cmap=cmap_light)

    # Plot also the training points
    plt.scatter(X[:, 0], X[:, 1], c=y, cmap=cmap_bold)
    plt.xlim(xx_coords.min(), xx_coords.max())
    plt.ylim(yy_coords.min(), yy_coords.max())
