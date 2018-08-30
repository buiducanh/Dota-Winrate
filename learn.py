from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, GridSearchCV
from fastFM import als
import numpy as np
from scipy import sparse
from sklearn.ensemble import RandomForestClassifier
import json
import os
import pprint

def random_forest(X, Y):
    x_train, x_test, y_train, y_test = train_test_split(X, Y, test_size=0.1, random_state=RANDOM_SEED)

    hyper_params = {
            "n_estimators": [10, 60, 100]
            }

    est = RandomForestClassifier(random_state=RANDOM_SEED)

    cv = GridSearchCV(est, hyper_params)

    cv.fit(x_train, y_train)

    return {"score": cv.score(x_test, y_test), "results": cv.cv_results_}

def factorization_machine(X, Y):
    x_train, x_test, y_train, y_test = train_test_split(X, Y, test_size=0.1, random_state=RANDOM_SEED)

    hyper_params = {
            "rank": [2, 6, 8, 10]
            }

    est = als.FMClassification(n_iter=1000)

    cv = GridSearchCV(est, hyper_params)

    cv.fit(x_train, y_train)

    return {"score": cv.score(x_test, y_test), "results": cv.cv_results_}


def logistic_reg(X, Y):
    x_train, x_test, y_train, y_test = train_test_split(X, Y, test_size=0.1, random_state=RANDOM_SEED)

    hyper_params = {
            "C": [10, 1.0, 0.1, 0.01, 0.001],
            }

    est = LogisticRegression(penalty="l2", random_state=RANDOM_SEED)

    cv = GridSearchCV(est, hyper_params)

    cv.fit(x_train, y_train)

    return {"score": cv.score(x_test, y_test), "results": cv.cv_results_}

RANDOM_SEED = 100

dataset = np.load("data/dota.npy")

X_heroes_only = dataset[:, :228]
X_heroes_and_roles = dataset[:, :-1]

Y = dataset[:, -1]

label = ["heroes only", "heroes & roles"]
datasets = [X_heroes_only, X_heroes_and_roles]

results_filename = "results.json"
results_file = open(results_filename, "w")
scores = {}
for i, X in enumerate(datasets):
    scores[label[i] + " - lr"] = logistic_reg(X, Y)

    scores[label[i] + " - rf"] = random_forest(X, Y)

    Y[Y == 0] = -1
    X_sp = sparse.csc_matrix(X)

    scores[label[i] + " - fm"] = factorization_machine(X_sp, Y)

json.dump(scores, results_file, default=lambda x: x.tolist())

pprint.pprint(scores)
