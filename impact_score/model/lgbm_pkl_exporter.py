from impact_score.model.lgbm_model import ValorantLGBM


def update_pkl():
    """
    Update the pickle file with the new model
    """
    vm = ValorantLGBM()
    vm.setup_dataframe("2000.csv")
    vm.train_model(optuna_study=True)
    vm.export_model_to_pkl()
    # vm.show_all_metrics()


if __name__ == "__main__":
    update_pkl()
