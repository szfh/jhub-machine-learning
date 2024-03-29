# -*- coding: utf-8 -*-
"""
date: 2020-03-29
"""
# =============================================================================
# Part 1- Import Data
# =============================================================================

"""Import libraries"""
import pandas as pd

"""Import dataset, if it is not already imported"""
try:
    dataset
except NameError:
    # from google.colab import files
    # uploaded = files.upload()
    dataset = pd.read_excel('breast-cancer.xls')

# =============================================================================
# Part 2 - Data preprocessing
# =============================================================================

"""Import libraries"""
import numpy as np
import datetime as datetime
import itertools

"""Create independent and dependent variables"""
X = dataset.iloc[:, :-1].values
y = dataset.iloc[:, -1].values

"""
Some data in the dataset is incorrectly coded as dates.
eg. '3-5' -> 3 May 19.
This loop changes datetimes to the correct range.
"""
def datetime_to_string(s):
    """Replace datetimes with strings"""
    switch={
        datetime.datetime(2019, 5, 3):'3-5',
        datetime.datetime(2019, 9, 5):'5-9',
        datetime.datetime(2019, 8, 6):'6-8',
        datetime.datetime(2019, 11, 9):'9-11',
        datetime.datetime(2014, 10, 1):'10-14',
        datetime.datetime(2014, 12, 1):'12-14',
        }
    return switch.get(s,s)

for i, j in itertools.product(range(X.shape[0]), [2,3]):
    X[i, j] = datetime_to_string(X[i, j])

"""
Data is given as a range in string format.
This loop replaces with the midpoint of the two values (rounded up).
eg. '40-49' -> 45
"""
def get_mid_point(n):
    """Get the mid point of a range of values"""
    n = n.split('-')
    n = [int(i) for i in n]
    n = np.mean(n)
    n = np.ceil(n)
    n = int(n)
    return(n)

for i, j in itertools.product(range(X.shape[0]), [0,2,3]):
    X[i, j] = get_mid_point(X[i, j])

"""
There are missing values encoded as '?'
All are categorical variables, so the mean cannot be found.
Strategy: replace with the most frequent category.
"""
from sklearn.impute import SimpleImputer
missingvalues = SimpleImputer(missing_values='?',strategy='most_frequent')
missingvalues = missingvalues.fit(X)
X = missingvalues.transform(X)

"""Encode categorical data"""
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import LabelEncoder
for j in [4,6,8]:
    X[:, j] = np.array(LabelEncoder().fit_transform(X[:, j]))
from sklearn.preprocessing import OneHotEncoder
one_hot_encoder1 = ColumnTransformer([('encoder', OneHotEncoder(), [1])], remainder='passthrough')
X = np.array(one_hot_encoder1.fit_transform(X))
one_hot_encoder2 = ColumnTransformer([('encoder', OneHotEncoder(), [9])], remainder='passthrough')
X = np.array(one_hot_encoder2.fit_transform(X))
y = LabelEncoder().fit_transform(y)

"""
Avoid the dummy variable trap.
Categories created by OneHotEncoder are multicollinear.
Strategy: one column is dropped from each.
"""
X = np.delete(X, [0,5],axis=1)

"""Change type"""
X = np.array(X, dtype=np.int32)

"""Feature scaling. Variables have mean = 0 and variance = 1."""
from sklearn.preprocessing import StandardScaler
sc_X = StandardScaler()
X = StandardScaler().fit_transform(X)

# =============================================================================
# Part 3 - Build Artificial Neural Network
# =============================================================================

def build_model(nodes=[1], input_dim=13):
    """Build an Artifical Neural Network"""

    """Import libraries"""
    from tensorflow.python.keras.models import Sequential
    from tensorflow.python.keras.layers import Dense

    """Initialise the ANN"""
    classifier = Sequential()

    """
    Add the layers to the model.
    kernel_initializer = 'uniform', randomly initialise the weights close to 0.
    activation = 'relu' for hidden layers, non-zero output to positive input.
    activation = 'sigmoid' for output layer to get probability.
    """
    classifier.add(Dense(units=nodes[0], kernel_initializer='uniform', activation='relu', input_dim=input_dim))
    for node in nodes[1:-1]:
        classifier.add(Dense(units=node, kernel_initializer='uniform', activation='relu'))
    classifier.add(Dense(units=nodes[-1], kernel_initializer='uniform', activation='sigmoid'))

    """
    Compile the ANN.
    optimizer = 'adam', commonly used gradient descent algorithm.
    loss = 'binary-crossentropy' for binary classification.
    """
    classifier.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    return(classifier)

"""
Build model.

Approach:
We need to build a model to achieve good accuracy while minimising overfitting.
There is no "standard" design approach, the model must have enough nodes to capture the dataset complexity.
A trial and error approach from a simple starting point is usually effective.

Tests:
Initial test of 2 hidden layers each with 7 nodes (mean of input and output = ((13+1)/2))
Additional layers added to capture weights for more data relationships.
Very large numbers (>100) or too many hidden layers (>6) can cause overfitting.
Too small (<5 in the first/second layer) means relevant variables/weights are not always captured.

Strategy:
Use 4 hidden layers, first with 25 nodes to capture the data complexity (13 inputs).
Then scaling down to the single output node.
This gives regular good predictions for this dataset.
"""
nodes = [25,15,8,3,1]
classifier = build_model(nodes, input_dim=X.shape[1])

# =============================================================================
# Part 4 - Evaluate Artificial Neural Network with k-Fold Cross Evaluation
# =============================================================================

def train_model(classifier, X, y, epochs, batch_size, verbose=1):
    """Train the ANN using training data"""
    classifier.fit(X, y, epochs=epochs, batch_size=batch_size, verbose=verbose)
    return(classifier)

def predict(X_test, classifier):
    """Predict the test set results"""
    y_pred = classifier.predict(X_test)
    y_pred = (y_pred > 0.5)
    return(y_pred)

def getconfusionmatrix(y_test, y_pred):
    """Make the confusion matrix"""
    from sklearn.metrics import confusion_matrix
    cm = confusion_matrix(y_test, y_pred)
    return(cm)

def getaccuracy(cm):
    """Calculate the accuracy"""
    accuracy = (cm[0,0]+cm[1,1])/(cm.sum())
    return(accuracy)

def plotconfusionmatrix(cm, accuracy):
    """Plot the confusion matrix"""
    import matplotlib.pyplot as plt
    plt.imshow(cm, interpolation='nearest', cmap='Blues')
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, cm[i, j], color='white' if cm[i, j] >= cm.max()/2 else 'black')
    plt.title('Confusion matrix\nAccuracy = %0.2f%%' %(100*accuracy))
    plt.xticks([0,1],['No recurrence','Recurrence'])
    plt.yticks([0,1],['No recurrence','Recurrence'],rotation=90,verticalalignment='center')
    plt.xlabel('Prediction')
    plt.ylabel('Actual')
    plt.show()

def kfold(classifier, epochs, batch_size=10, n_splits=10, verbose=1):
    """Perform k-fold cross evaluation of the model"""
    from sklearn.model_selection import StratifiedKFold
    kfold = StratifiedKFold(n_splits=n_splits, shuffle=True)

    cms = []
    accuracies = []
    for train, test in kfold.split(X, y):
        classifier = train_model(classifier, X[train], y[train], epochs=epochs, batch_size=batch_size, verbose=verbose)
        y_pred = predict(X[test],classifier)
        cm = getconfusionmatrix(y[test], y_pred)
        cms.append(cm)
        accuracies.append(getaccuracy(cm))

    return(cms, accuracies)

"""
Fit the ANN to the training set, and evaluate with k-fold cross evaluation.
The training parameters are passed to the function and run multiple times.
This gives multiple confusion matrices as an output with calculated accuracies.

Tests:
If there are too few epochs or batches, the model is more likely to predict 0 for all test variables
(because there is ~62% chance of no recurrence in the whole dataset)
Accuracy stabilises usually around 60-120 epochs. Adding more epochs to ensure convergance is helpful.

Strategy:
Epochs = 200, accuracy has stabilised by this many runs.
Batch size = 10, enough runs for sufficient weight training iterations.
n_splits = 10, enough evaluations to get reliable mean accuracy.
"""
epochs=200
batch_size=10
n_splits=10
verbose = 0 # set verbose=1/0 for more/less text in console.
cms, accuracies = kfold(classifier, epochs=epochs, batch_size=batch_size, n_splits=n_splits, verbose=verbose)

print('k-fold cross evaluation splits: %d' %(n_splits))
print('Mean accuracy = %.2f%%' %(np.mean(accuracies)*100))
print('Best accuracy = %.2f%%' %(np.max(accuracies)*100))
print('Worst accuracy = %.2f%%' %(np.min(accuracies)*100))
print('Standard deviation = %.4f' %(np.std(accuracies)))
print('k-Fold cross evaluation best accuracy confusion matrix:')
plotconfusionmatrix(cms[np.argmax(accuracies)], np.max(accuracies))

# =============================================================================
# Part 5 - Predict unseen data
# =============================================================================

"""
Create training and test set.

Strategy:
80% training, 20% test to balance training data with verification.
For more test data this can be increased to ~0.5 exchanging a minor loss of accuracy (~10%).
"""
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)

"""
Train model.
The same classifier and parameters are used as for the k-fold cross evaluation.
"""
classifier = train_model(classifier, X_train, y_train, epochs=epochs, batch_size=batch_size, verbose=verbose)

"""Predict recurrence"""
y_pred = predict(X_test,classifier)

"""Make the confusion matrix"""
cm = getconfusionmatrix(y_test, y_pred)

"""Caluclate the accuracy"""
accuracy = getaccuracy(cm)

"""Plot the confusion matrix"""
print('Unseen data confusion matrix:')
plotconfusionmatrix(cm, accuracy)
