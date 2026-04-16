from sklearn.tree import DecisionTreeClassifier
import numpy as np
import pickle

# Example dataset
# [weight, fragile, transfer_time]
X = np.array([
    [20, 0, 60],
    [30, 1, 30],
    [15, 0, 90],
    [40, 1, 20],
    [10, 0, 120]
])

# Risk labels (0 = low, 1 = high)
y = np.array([0, 1, 0, 1, 0])

model = DecisionTreeClassifier()
model.fit(X, y)

pickle.dump(model, open('model.pkl', 'wb'))

print("Model trained!")