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
model_list = ['mdl_RFR','mdl_XGR','mdl_LGR']
model_sel=[RandomForestRegressor(),XGBRegressor(),LGBMRegressor()]
model_scores_r2 = []
model_score_mae = []
model_score_rmse = []
y_preds = []
all_vals = {}
##################
## Function for scoring
def mdl_metrics(model_name,model,X_train,y_train,y_test):
    name = model_name
    model_name = model.fit(X_train, y_train)
    y_pred = model_name.predict(X_test)
    print(model_name.score(X_test,y_test))
    r2 = model_name.score(X_test,y_test)
    mae = mean_absolute_error(y_test,y_pred)
    rmse = root_mean_squared_error(y_test, y_pred)
    print(r2,rmse)
    y_preds.append(y_pred)
    model_scores_r2.append(r2)
    model_score_mae.append(mae)
    model_score_rmse.append(rmse)
    all_vals[name] = y_pred

#%%
for x in range(len(model_list)):
    mdl_metrics(model_list[x],model_sel[x],X_train,y_train,y_test)

# %%
import matplotlib.pyplot as plt

#plt.bar(x=y_test.index, height=y_test)
#plt.bar(x=y_test.index, height=all_vals[list(all_vals.keys())[0]])
#############
fig, ax = plt.subplots()
ax.bar(np.arange(398), y_test,width=5, label='y test')
ax.bar(np.arange(398), all_vals[list(all_vals.keys())[0]], width=5,label='y Preds')
#ax.set_xticks(x)
ax.legend()
plt.show()
# %%
for x in range(3):
    fig, ax = plt.subplots()
    ax.scatter(np.arange(398), y_test, label='y test')
    ax.scatter(np.arange(398), all_vals[list(all_vals.keys())[x]],label=list(all_vals.keys())[x])
    #ax.set_xticks(x)
    ax.set_xlabel('Index')
    ax.set_ylabel('Stress, MPa')
    ax.legend()
    name = list(all_vals.keys())[x]+'.png'
    plt.savefig('./output/'+name)
    plt.show()

# %%
import plotly.graph_objects as go
for x in range(3):
    fig = go.Figure()
    fig.add_scatter(x=np.arange(398), y=y_test, mode='markers', name='y test')
    fig.add_scatter(x=np.arange(398), y=all_vals[list(all_vals.keys())[x]], mode='markers', name=list(all_vals.keys())[x])
    fig.update_layout(showlegend=True,
                      xaxis_title='Index',
                      yaxis_title='Stress, MPa')
    fig.show()
    name = list(all_vals.keys())[x]+'.html'
    fig.write_html('./output/'+name)

# %%
fig, ax = plt.subplots()
ax.bar(model_list, model_score_mae)
ax.legend()
ax.set_xlabel('Model')
ax.set_ylabel('MAE')
plt.savefig('./output/model_scores_mae.png')
plt.show()


# %%
fig, ax = plt.subplots()
ax.bar(model_list, model_score_rmse)
ax.legend()
ax.set_xlabel('Model')
ax.set_ylabel('RMSE')

plt.savefig('./output/model_scores_rmse.png')
plt.show()
# %%
