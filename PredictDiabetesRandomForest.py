import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from sklearn.metrics.pairwise import cosine_similarity
import shap
from lime.lime_tabular import LimeTabularExplainer
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
from collections import defaultdict
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Optional: suppress feature name warnings
warnings.filterwarnings("ignore", category=UserWarning)

# Load the dataset
df = pd.read_csv("diabetes-dataset.csv")

# Split into features and target
X = df.drop('Outcome', axis=1)
y = df['Outcome']

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Total features
total_features = X.shape[1]

# --- FIG 2: Correlation Matrix ---
plt.figure(figsize=(10, 8))
sns.heatmap(df.corr(), annot=True, cmap="magma")
plt.title("Fig. 2. Correlation coefficient matrix of diabetes")
plt.tight_layout()
plt.savefig("fig2_correlation_matrix.png")
plt.close()

# --- FIG 3: Histograms of Features ---
df.hist(figsize=(12, 10), bins=20)
plt.suptitle("Fig. 3. Histogram of data set features", y=1.02)
plt.tight_layout()
plt.savefig("fig3_histograms.png")
plt.close()

# --- FIG 4: Scatter Plot (Glucose vs Age) ---
plt.figure(figsize=(8, 6))
sns.scatterplot(data=df, x='Glucose', y='Age', hue='Outcome', palette='coolwarm')
plt.title("Fig. 4. Scatter plot of two classes")
plt.tight_layout()
plt.savefig("fig4_scatter_plot.png")
plt.close()

# --- FIG 5: Global Variable Importance (Random Forest) ---
importances = model.feature_importances_
indices = np.argsort(importances)[::-1]
features_sorted = X.columns[indices]

plt.figure(figsize=(8, 6))
sns.barplot(x=importances[indices], y=features_sorted)
plt.title("Fig. 5. Global variable importance")
plt.tight_layout()
plt.savefig("fig5_global_importance.png")
plt.close()

# SHAP explanations using correct interface
explainer_shap = shap.Explainer(model, X_train)
shap_values = explainer_shap(X_train)

# --- FIG 6: SHAP Mean SHAP Value by Class Plot ---
shap_class0 = np.abs(shap_values.values[:, :, 0]).mean(axis=0)
shap_class1 = np.abs(shap_values.values[:, :, 1]).mean(axis=0)

# Create DataFrame
df_mean = pd.DataFrame({
    'Class 0': shap_class0,
    'Class 1': shap_class1
}, index=X.columns)

# Plot horizontal bar chart
df_mean.plot(kind='barh', figsize=(10, 6), colormap='coolwarm')
plt.title("Fig. 6. Mean Absolute SHAP Values by Feature and Class")
plt.xlabel("Mean |SHAP Value|")
plt.tight_layout()
plt.savefig("fig6_mean_shap_summary.png")
plt.close()

# --- FIG 7: SHAP Bar Plot ---
shap.summary_plot(shap_values, X_train, plot_type="bar", show=False)
plt.title("Fig. 7. SHAP value of the model")
plt.savefig("fig7_shap_bar_summary.png", bbox_inches='tight')
plt.close()

# --- FIG 8: SHAP Dependence Plots for Top Features ---
for feature in ["Glucose", "BMI", "Age"]:
    shap.dependence_plot(feature, shap_values.values[:, :, 1], X_train, show=False)
    plt.title(f"SHAP Dependence Plot for {feature}")
    plt.tight_layout()
    plt.savefig(f"fig8_dependence_{feature.lower()}.png")
    plt.close()

# LIME explanations
explainer_lime = LimeTabularExplainer(X_train.values,
                                      feature_names=X.columns.tolist(),
                                      class_names=['No Diabetes', 'Diabetes'],
                                      mode='classification')

# --- FIG 10–12: SHAP vs LIME Dependence Plots for Glucose, BMI, Age ---
for idx, feature in enumerate(["Glucose", "BMI", "Age"], start=11):
    lime_contributions = []
    shap_contributions = []
    feature_values = []

    for i in range(100):
        exp = explainer_lime.explain_instance(X_test.iloc[i].values, model.predict_proba, num_features=total_features)
        weight = 0
        for feat, val in exp.as_list():
            if feature in feat:
                weight = val
                break
        lime_contributions.append(weight)
        shap_contributions.append(shap_values.values[i, X.columns.get_loc(feature), 1])
        feature_values.append(X_test.iloc[i][feature])

    plt.figure(figsize=(10, 6))
    plt.scatter(feature_values, shap_contributions, alpha=0.7, label="SHAP", color="blue")
    plt.scatter(feature_values, lime_contributions, alpha=0.7, label="LIME", color="orange")
    plt.xlabel(f"{feature} Value")
    plt.ylabel("Contribution")
    plt.title(f"Fig. {idx}. SHAP vs LIME Dependence Plot for {feature}")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"fig{idx}_shap_vs_lime_dependence_{feature.lower()}.png")
    plt.close()

# Replace this block in your file to fix LIME/SHAP logic

def get_shap_vector(shap_values, i):
    vals = shap_values[i].values
    if vals.ndim == 2 and vals.shape[0] == 2:
        return vals[1]
    return vals

def explanation_to_vector(explanation, feature_names):
    vec = np.zeros(len(feature_names))
    for feat, weight in explanation.as_list():
        matched = [f for f in feature_names if f in feat]
        if matched:
            idx = list(feature_names).index(matched[0])
            vec[idx] = abs(weight)
    return vec

def calculate_sparsity_score(explanation_features, total_features):
    return 1 - (len(explanation_features) / total_features)

shap_vec_1 = get_shap_vector(shap_values, 0)
shap_vec_2 = get_shap_vector(shap_values, 1)

# Updated LIME explanations with num_features=5
num_features_lime = 5
exp1 = explainer_lime.explain_instance(X_test.iloc[0].values, model.predict_proba, num_features=num_features_lime)
exp2 = explainer_lime.explain_instance(X_test.iloc[1].values, model.predict_proba, num_features=num_features_lime)
exp1.save_to_file('lime_instance1_explanation.html')

lime_vec_1 = explanation_to_vector(exp1, X.columns)
lime_vec_2 = explanation_to_vector(exp2, X.columns)

# Sparsity fix: top 5 SHAP features
shap_explained_features = [X.columns[i] for i in np.argsort(np.abs(shap_vec_1))[-5:]]
lime_explained_features = [feat.split(' ')[0] for feat, _ in exp1.as_list()]

shap_sparsity = calculate_sparsity_score(shap_explained_features, total_features)
lime_sparsity = calculate_sparsity_score(lime_explained_features, total_features)

# Stability
shap_stability = cosine_similarity(shap_vec_1.reshape(1, -1), shap_vec_2.reshape(1, -1))[0][0]
lime_stability = cosine_similarity(lime_vec_1.reshape(1, -1), lime_vec_2.reshape(1, -1))[0][0]

# Fidelity: using exp.local_pred
model_preds = model.predict_proba(X_test.iloc[:2])[:, 1]
lime_preds = np.array([exp1.local_pred[0], exp2.local_pred[0]])
shap_fidelity_score = 1 - mean_squared_error(model_preds, model_preds)
lime_fidelity_score = 1 - mean_squared_error(model_preds, lime_preds)

# Composite score
w1, w2, w3 = 0.3, 0.3, 0.4
shap_interpretability_score = w1 * shap_sparsity + w2 * shap_stability + w3 * shap_fidelity_score
lime_interpretability_score = w1 * lime_sparsity + w2 * lime_stability + w3 * lime_fidelity_score

# Conclusion
conclusion = "SHAP is more interpretable than LIME (Reject H0, Accept H1)" if shap_interpretability_score > lime_interpretability_score else "SHAP is not more interpretable than LIME (Fail to reject H0)"

# Output
print(f"\nSHAP Sparsity Score: {shap_sparsity:.4f}")
print(f"LIME Sparsity Score: {lime_sparsity:.4f}")
print(f"SHAP Stability Score: {shap_stability:.4f}")
print(f"LIME Stability Score: {lime_stability:.4f}")
print(f"SHAP Fidelity Score: {shap_fidelity_score:.4f}")
print(f"LIME Fidelity Score: {lime_fidelity_score:.4f}")
print(f"SHAP Interpretability Score (e1): {shap_interpretability_score:.4f}")
print(f"LIME Interpretability Score (e2): {lime_interpretability_score:.4f}")
print("Conclusion:", conclusion)


# Predict on test set
y_pred = model.predict(X_test)

# Calculate performance metrics
accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred, zero_division=0)
recall = recall_score(y_test, y_pred, zero_division=0)
f1 = f1_score(y_test, y_pred, zero_division=0)

# Print results in table format
print("\nModel Performance Metrics:")
print(f"{'Metric':<10} | {'Score':<10}")
print("-" * 25)
print(f"{'Accuracy':<10} | {accuracy:.4f}")
print(f"{'Precision':<10} | {precision:.4f}")
print(f"{'Recall':<10} | {recall:.4f}")
print(f"{'F1 Score':<10} | {f1:.4f}")
