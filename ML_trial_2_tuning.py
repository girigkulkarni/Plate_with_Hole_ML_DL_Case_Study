#%%
# all required imports
import pandas as pd
import numpy as np
from string import Template
import os,glob
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
## metrics
from sklearn.metrics import r2_score
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
### models
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
import optuna
from sklearn.model_selection import cross_val_score
import plotly.graph_objects as go

#%%
# Get the data ready

data = pd.read_csv(r"D:\Agentic_AI\Plate_with_a_hole\Step1_Data\train_validation_Input_Output_V1.csv")


# Check for missing values
data.isna().sum()

#remove rows with missing data
data.dropna(inplace=True)

data.isna().sum()

#%%
X = data.drop('Max_Stress', axis=1)
y=data['Max_Stress']

# We do not these columns as they do not add value to data
X = X.drop(['counter','name','Location'],axis=1)

cat_features = ['Material', 'bc_loc']
one_hot = OneHotEncoder()
transformer = ColumnTransformer([('one_hot',
                                 one_hot,
                                 cat_features)],
                                 remainder='passthrough')

transformed_X = transformer.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(transformed_X,
                                                    y,
                                                    test_size=0.2,
                                                    random_state=42)

# %%
## cross validation and tuning
# Loss direction: minimize negative RMSE (equivalent to minimize RMSE)
def _rmse_cv(model, X, y, cv=5):
    scores = cross_val_score(
        model, X, y, cv=cv, scoring="neg_root_mean_squared_error"
    )
    return np.mean(scores)  # negative RMSE (Optuna will maximize this)
#%%
## Comprisng performances of optmized models

all_df_optimized = pd.DataFrame()
all_df_optimized['Y test'] = y_test

#%%
def rf_objective(trial):
    params = {
        "n_estimators": trial.suggest_int("n_estimators", 100, 500),
        "max_depth": trial.suggest_int("max_depth", 3, 20),
        "min_samples_split": trial.suggest_int("min_samples_split", 2, 20),
        "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 10),
        "max_features": trial.suggest_categorical(
            "max_features", ["sqrt", "log2", 0.1, 0.2, 0.3, 0.5]
        ),
        "bootstrap": trial.suggest_categorical("bootstrap", [True, False]),
        "random_state": 42,
        "n_jobs": -1,
    }
    model = RandomForestRegressor(**params)
    return _rmse_cv(model, X_train, y_train, cv=5)

#%%
# Example: 50 trials per model
N_TRIALS = 50

# RandomForest
study_rf = optuna.create_study(direction="maximize")
study_rf.optimize(rf_objective, n_trials=N_TRIALS)
print("RF best params:", study_rf.best_params)
print("RF best CV RMSE:", -study_rf.best_value)



# %%
rf_best = RandomForestRegressor(**study_rf.best_params, random_state=42, n_jobs=-1)
rf_best.fit(X_train, y_train)
y_preds_cv = rf_best.predict(X_test)
all_df_optimized['RF Best Opt'] = y_preds_cv

#%%

fig = go.Figure()
fig.add_scatter(x=np.arange(398), y=y_test, mode='markers', name='y test')
fig.add_scatter(x=np.arange(398), y=y_preds_cv, mode='markers', name='RFR optimized CV')
fig.update_layout(showlegend=True,
                    xaxis_title='Index',
                    yaxis_title='Stress, MPa')
fig.show()
fig.write_html('./output/RFR_opti_CV.html')
# %%

def xgb_objective(trial):
    params = {
        "objective": "reg:squarederror",
        "eval_metric": "rmse",
        "n_estimators": trial.suggest_int("n_estimators", 100, 1000),
        "max_depth": trial.suggest_int("max_depth", 3, 10),
        "learning_rate": trial.suggest_float("learning_rate", 0.005, 0.3, log=True),
        "subsample": trial.suggest_float("subsample", 0.5, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
        "reg_alpha": trial.suggest_float("reg_alpha", 0.0, 10.0),
        "reg_lambda": trial.suggest_float("reg_lambda", 0.0, 10.0),
        "random_state": 42,
        "n_jobs": -1,
    }
    model = XGBRegressor(**params)
    return _rmse_cv(model, X_train, y_train, cv=5)

#%%
# XGBoost
study_xgb = optuna.create_study(direction="maximize")
study_xgb.optimize(xgb_objective, n_trials=N_TRIALS)
print("XGB best params:", study_xgb.best_params)
print("XGB best CV RMSE:", -study_xgb.best_value)

#%%
xgb_best = XGBRegressor(**study_xgb.best_params, random_state=42, n_jobs=-1)
xgb_best.fit(X_train, y_train)
y_preds_cv = xgb_best.predict(X_test)

all_df_optimized['XGB Best Opt'] = y_preds_cv

#%%
fig = go.Figure()
fig.add_scatter(x=np.arange(398), y=y_test, mode='markers', name='y test')
fig.add_scatter(x=np.arange(398), y=y_preds_cv, mode='markers', name='XGB optimized CV')
fig.update_layout(showlegend=True,
                    xaxis_title='Index',
                    yaxis_title='Stress, MPa')
fig.show()
fig.write_html('./output/XGB_opti_CV.html')
# %%
def lgbm_objective(trial):
    params = {
        "objective": "regression",
        "metric": "rmse",
        "n_estimators": trial.suggest_int("n_estimators", 100, 1000),
        "num_leaves": trial.suggest_int("num_leaves", 16, 512),
        "max_depth": trial.suggest_int("max_depth", 3, 15),
        "learning_rate": trial.suggest_float("learning_rate", 0.005, 0.3, log=True),
        "feature_fraction": trial.suggest_float("feature_fraction", 0.4, 1.0),
        "bagging_fraction": trial.suggest_float("bagging_fraction", 0.4, 1.0),
        "bagging_freq": trial.suggest_int("bagging_freq", 1, 10),
        "min_data_in_leaf": trial.suggest_int("min_data_in_leaf", 5, 100),
        "lambda_l1": trial.suggest_float("lambda_l1", 0.0, 10.0),
        "lambda_l2": trial.suggest_float("lambda_l2", 0.0, 10.0),
        "random_state": 42,
        "n_jobs": -1,
    }
    model = LGBMRegressor(**params)
    return _rmse_cv(model, X_train, y_train, cv=5)

#%%
# LightGBM
study_lgbm = optuna.create_study(direction="maximize")
study_lgbm.optimize(lgbm_objective, n_trials=N_TRIALS)
print("LGBM best params:", study_lgbm.best_params)
print("LGBM best CV RMSE:", -study_lgbm.best_value)

#%%
lgbm_best = LGBMRegressor(**study_lgbm.best_params, random_state=42, n_jobs=-1)
lgbm_best.fit(X_train, y_train)
y_preds_cv = lgbm_best.predict(X_test)

all_df_optimized['LGBM Best Opt'] = y_preds_cv

#%%
fig = go.Figure()
fig.add_scatter(x=np.arange(398), y=y_test, mode='markers', name='y test')
fig.add_scatter(x=np.arange(398), y=y_preds_cv, mode='markers', name='LGBM_optimize_cv')
fig.update_layout(showlegend=True,
                    xaxis_title='Index',
                    yaxis_title='Stress, MPa')
fig.show()
fig.write_html('./output/LGBM_opti_CV.html')
# %%

