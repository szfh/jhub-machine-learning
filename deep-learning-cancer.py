# -*- coding: utf-8 -*-
"""
date: 2020-03-29
"""
# =============================================================================
# Part 1- Import Data
# =============================================================================

"""Import libraries"""
import pandas as pd

"""Import dataset"""
try:
    dataset
except NameError:
    # from google.colab import files
    # uploaded = files.upload()
    dataset = pd.read_excel('breast-cancer.xls')

# =============================================================================
# Part 2 - Data Preprocessing
# =============================================================================

"""Import libraries"""
import numpy as np
import datetime as datetime
import itertools

"""Create arrays of independent and dependent variables"""
X = dataset.iloc[:, :-1].values
y = dataset.iloc[:, -1].values

"""
Some data in the dataset is incorrectly coded as dates.
eg. '3-5' -> 3 May 19.
This loop changes datetimes to the correct range.
"""
def datetime_to_string(s):
    """Function to replace datetimes with strings"""
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
    """Function to get the mid point of a range of values"""
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
Strategy: replace with the most frequent category
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

"""Encode dependent variable"""
y = LabelEncoder().fit_transform(y)

"""Change type"""
X = np.array(X, dtype=np.int64)
y = np.array(y, dtype=np.int64)

"""
Avoid the dummy variable trap.
Categories created by OneHotEncoder are multicollinear.
Strategy: one column is dropped from each.
"""
X = np.delete(X, [0,5],axis=1)

"""
Create training and test set.
n = 286
Strategy:
80% training, 20% test to balance training data with verification.
For more test data this can be increased to ~0.5 exchanging a minor loss of accuracy (~10%).
"""
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)

"""
Feature scaling.
Variables have mean = 0 and variance = 1.
"""
from sklearn.preprocessing import StandardScaler
sc_X = StandardScaler()
X_train = sc_X.fit_transform(X_train)
X_test = sc_X.transform(X_test)

# =============================================================================
# Part 3 - Artificial Neural Network
# =============================================================================

"""
Approach:
We need to build a model to achieve good accuracy while minimising overfitting.
There is no "standard" build method, the model must have enough nodes to capture the dataset complexity.
A trial and error approach from a simple starting point is usually effective.

Tests:
Initial test of 2 hidden layers both with 7 nodes (mean of input and output = ((13+1)/2))
Very large numbers (>50) or too many hidden layers (>6) can cause overfitting.
Too small (<5 in the first/second layer) means relevant variables/weights are not always captured.

Strategy:
Use 3 hidden layers, first with 20 nodes (above) to capture the data complexity (13 inputs)
Then scaling down to 1 node in the output (20-8-3-1).
This gives regular good predictions for this dataset.
"""

"""Import libraries"""
from keras.models import Sequential
from keras.layers import Dense

"""As a function"""
def build_model(epochs=100, batch_size=10):
    """Initialise the ANN"""
    classifier = Sequential()

    """
    Add the layers to the model.
    kernel_initializer = 'uniform', randomly initialise the weights close to 0.
    activation = 'relu' for hidden layers, non-zero output to positive input.
    activation = 'sigmoid' for output layer to get probability.
    """
    classifier.add(Dense(units=20, kernel_initializer='uniform', activation='relu', input_dim=13))
    classifier.add(Dense(units=8, kernel_initializer='uniform', activation='relu'))
    classifier.add(Dense(units=3, kernel_initializer='uniform', activation='relu'))
    classifier.add(Dense(units=1, kernel_initializer='uniform', activation='sigmoid'))

    """
    Compile the ANN
    optimizer = 'adam', commonly used gradient descent algorithm
    loss = 'binary-crossentropy' for binary classification problem
    """
    classifier.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

    """
    Fit the ANN to the training set

    Tests:
    If there are too few epochs or batches, the model is more likely to predict 0 for all test variables
    (because there is ~62% chance of no recurrence in the whole dataset)
    Accuracy stabilises usually around 100-200 epochs. Adding more epochs to ensure convergance is helpful though.
    Batch size = 10 is sufficient for enough weight training.

    Strategy:
    Epochs = 500, weights have converged by this many runs.
    Batch size = 10, enough runs for reliable updates.

    Set verbose=1 to see training.
    """
    classifier.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, verbose=1)
    return(classifier)

# =============================================================================
# Part 4 - Make the predictions
# =============================================================================

def predict(X_test):
    """Predict the test set results"""
    y_pred = classifier.predict(X_test)
    y_pred = (y_pred > 0.5)
    return(y_pred)

def cm(y_test, y_pred):
    """Make the confusion matrix"""
    from sklearn.metrics import confusion_matrix
    cm = confusion_matrix(y_test, y_pred)
    accuracy = (cm[0,0]+cm[1,1])/(cm.sum())
    return(cm, accuracy)

""""Applying k-Fold Cross Validation"""
# from sklearn.model_selection import cross_val_score
# print(cross_val_score(estimator=classifier, X=X_train, y=y_train, cv=10))
# print(cross_val_score(estimator=classifier, X=X_train, y=y_train, cv=10, scoring='accuracy'))
# accuracies = cross_val_score(estimator=classifier, X=X_train, y=y_train, cv=10)
# accuracies.mean()
# accuracies.std()

from sklearn.model_selection import StratifiedKFold
kfold = StratifiedKFold(n_splits=10, shuffle=True, random_state=1)
cvscores = []
for train, test in kfold.split(X, y):
    print(y[:5])
# =============================================================================
# Part 5 - Evaluate the model
# =============================================================================

"""Plot"""
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

"""
Analysis:
The model usually reaches accuracy of 65%-72% on the test data.
It is realistic to assume this is close to the limit of the dataset due the inherent uncertainty of cancer recurrence.
"""
