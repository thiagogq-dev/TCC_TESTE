import matplotlib.pyplot as plt
import numpy as np
import csv

def plot_confusion_matrix(tp, fp, tn, fn, output_file, quadrant_colors):
    matrix = np.array([[tp, fp], [fn, tn]])

    plt.figure(figsize=(8, 8))
    plt.imshow(matrix, interpolation='nearest', cmap=plt.cm.Blues)

    for i in range(2):
        for j in range(2):
            plt.text(j, i, str(matrix[i, j]), horizontalalignment='center', verticalalignment='center', color='black')

    plt.gca().add_patch(plt.Rectangle((-0.5, 0.5), 1, 1, fill=True, edgecolor='black', facecolor=quadrant_colors[0]))
    plt.gca().add_patch(plt.Rectangle((0.5, 0.5), 1, 1, fill=True, edgecolor='black', facecolor=quadrant_colors[1]))
    plt.gca().add_patch(plt.Rectangle((-0.5, -0.5), 1, 1, fill=True, edgecolor='black', facecolor=quadrant_colors[2]))
    plt.gca().add_patch(plt.Rectangle((0.5, -0.5), 1, 1, fill=True, edgecolor='black', facecolor=quadrant_colors[3]))

    classes = ['Com', 'Sem']
    tick_marks = np.arange(len(classes))

    plt.xticks(tick_marks, classes, rotation=45)
    plt.yticks(tick_marks, classes)

    plt.ylabel('BIC')
    plt.xlabel('FIX')

    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['left'].set_visible(False)
    plt.gca().spines['bottom'].set_visible(False)

    plt.gca().invert_yaxis()

    plt.savefig(output_file)
    plt.close()

with open('./csv/commit_analizer.csv', mode='r') as file:
    reader = csv.reader(file)
    next(reader)

    bic_fix = 0
    bic = 0
    fix = 0
    none = 0

    for row in reader:
        if row[2] == "Yes" and row[4] == "Yes":
            bic_fix += 1
        elif(row[2] == "Yes" and row[4] == "No"):
            fix += 1
        elif(row[2] == "No" and row[4] == "Yes"):
            bic += 1
        else:
            none += 1

tp = bic_fix
fp = bic
tn = none
fn = fix

output_file = "./confusion_matrix.png"
plot_confusion_matrix(tp, fp, tn, fn, output_file, quadrant_colors=('yellow', 'red', 'green', 'orange'))
