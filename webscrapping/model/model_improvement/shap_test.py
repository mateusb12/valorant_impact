from webscrapping.model.lgbm_model import get_trained_model
from pathlib import Path
import os
import pandas as pd
import shap

vm = get_trained_model()
model = vm.model


def get_dataset_reference():
    current_folder = Path(os.getcwd())
    model_folder = current_folder.parent
    webscrapping_folder = model_folder.parent
    return Path(webscrapping_folder, "matches", "datasets")


filename = "4500.csv"
df = pd.read_csv(f"{get_dataset_reference()}\\{filename}")

# Create object that can calculate shap values
explainer = shap.TreeExplainer(model)

# Calculate Shap values
#shap_values = explainer.shap_values(df)
