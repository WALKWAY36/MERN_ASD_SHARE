GRID_SEARCH = {
    'RANDOM_FOREST': { 
        'n_estimators': [50, 100, 200],
        'max_depth': [5, 10, 15, None],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4],
        'max_features': ['sqrt', 'log2', None],       
    },
    'GRADIENT_BOOSTING':  {
        'n_estimators': [50, 100, 200],
        'learning_rate': [0.01, 0.05, 0.1, 0.2],
        'max_depth': [3, 4, 5, 6],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4],
        'subsample': [0.8, 0.9, 1.0]
    },
    'MLP': {
        'hidden_layer_sizes': [(32,), (64,), (64, 32), (128, 64), (64, 32, 16)],
        'activation': ['relu', 'tanh', 'logistic'],
        'alpha': [0.0001, 0.001, 0.01],
        'learning_rate_init': [0.001, 0.01, 0.1],
        'solver': ['adam', 'sgd'],
    }
}

RANDOM_SEARCH = {
    'RANDOM_FOREST': {
                'n_estimators': [50, 100, 150, 200, 300],
                'max_depth': [3, 5, 7, 10, 15, 20, None],
                'min_samples_split': [2, 3, 5, 7, 10],
                'min_samples_leaf': [1, 2, 3, 4, 5],
                'max_features': ['sqrt', 'log2', None],
                'bootstrap': [True, False]
            },
    'GRADIENT_BOOSTING':  {
                'n_estimators': [50, 100, 150, 200, 300],
                'learning_rate': [0.001, 0.01, 0.05, 0.1, 0.2],
                'max_depth': [2, 3, 4, 5, 6, 7],
                'min_samples_split': [2, 3, 5, 7, 10],
                'min_samples_leaf': [1, 2, 3, 4, 5],
                'subsample': [0.7, 0.8, 0.9, 1.0],
                'max_features': ['sqrt', 'log2', None]
            },
    'MLP': {
                'hidden_layer_sizes': [(16,), (32,), (64,), (32, 16), (64, 32), 
                                    (128, 64), (64, 32, 16), (128, 64, 32)],
                'activation': ['relu', 'tanh', 'logistic'],
                'alpha': [0.00001, 0.0001, 0.001, 0.01, 0.1],
                'learning_rate_init': [0.0001, 0.001, 0.01, 0.1],
                'solver': ['adam', 'sgd', 'lbfgs'],
                'batch_size': [16, 32, 64, 'auto']
            }
}

