import matplotlib.pyplot as plt
import numpy as np
import os
import json

def train_test_err_plot(ax, res, x_param, title):
    mean_train_score = res['mean_train_score']
    mean_test_score = res['mean_test_score']
    params = res['params']

    #Create values and labels for line graphs
    values = np.vstack((mean_train_score, mean_test_score))
    inds   = list(map(lambda x: x[x_param], params))

    #Plot a line graph
    ax.plot(inds,values[0,:],'or-', linewidth=1, label="train_score") #Plot the first series in red with circle marker
    ax.plot(inds,values[1,:],'sb-', linewidth=1, label="test_score") #Plot the first series in blue with square marker

    #This plots the data
    ax.grid(True) #Turn the grid on
    ax.set_ylabel("Score") #Y-axis label
    ax.set_xlabel("Value") #X-axis label
    ax.set_title(title) #Plot title

    minx = np.min(inds)
    maxx = np.max(inds)
    ax.set_xlim(minx - 0.1,maxx + 0.1) #set x axis range

    ax.set_ylim(np.min(values) - 0.01, np.max(values) + 0.02) #Set yaxis range
    ax.legend(loc="best")


def bar_chart_vector_comparison(heroes_scores, roles_scores):
    ind = np.arange(3)  # the x locations for the groups
    width = 0.35       # the width of the bars

    fig, ax = plt.subplots()
    rects1 = ax.bar(ind, heroes_scores, width, color='r')

    rects2 = ax.bar(ind + width, roles_scores, width, color='y')

    # add some text for labels, title and axes ticks
    ax.set_ylabel('Scores')
    ax.set_title('Scores by model and feature vector')
    ax.set_xticks(ind + width / 2)
    ax.set_xticklabels(('LogReg', 'FactrMc', 'RandFrst'))

    ax.legend((rects1[0], rects2[0]), ('Heroes only', 'Heroes & roles'), loc="best")

    plt.savefig("Figures/scores.pdf")

inp = open("results.json")
res = json.load(inp)

f, (ax1, ax2) = plt.subplots(2)
lr_heroes = res["heroes only - lr"]["results"]
lr_roles = res["heroes & roles - lr"]["results"]

train_test_err_plot(ax1, lr_heroes, "C", "Heroes only with Logistic Regression")
train_test_err_plot(ax2, lr_roles, "C", "Heroes & roles with Logistic Regression")
f.tight_layout()
f.savefig("Figures/lr.pdf")

f, (ax1, ax2) = plt.subplots(2)
fm_heroes = res["heroes only - fm"]["results"]
fm_roles = res["heroes & roles - fm"]["results"]

train_test_err_plot(ax1, fm_heroes, "rank", "Heroes only with Factorization Machines")
train_test_err_plot(ax2, fm_roles, "rank", "Heroes & roles with Factorization Machines")
f.tight_layout()
f.savefig("Figures/fm.pdf")

f, (ax1, ax2) = plt.subplots(2)
rf_heroes = res["heroes only - rf"]["results"]
rf_roles = res["heroes & roles - rf"]["results"]

train_test_err_plot(ax1, rf_heroes, "n_estimators", "Heroes only with Random Forest")
train_test_err_plot(ax2, rf_roles, "n_estimators", "Heroes & roles with Random Forest")
f.tight_layout()
f.savefig("Figures/rf.pdf")

models_labels = ["lr", "fm", "rf"]
heroes_scores = []
roles_scores = []
for s in models_labels:
    heroes = res["heroes only - " + s]["score"]
    roles = res["heroes & roles - " + s]["score"]
    heroes_scores.append(heroes)
    roles_scores.append(roles)
bar_chart_vector_comparison(heroes_scores, roles_scores)
