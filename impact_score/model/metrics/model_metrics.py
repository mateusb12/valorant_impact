from matplotlib import pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.metrics import log_loss, brier_score_loss, confusion_matrix, classification_report, roc_curve, \
    roc_auc_score
from sklearn.model_selection import cross_val_score
from termcolor import colored

from impact_score.model.lgbm_model import ValorantLGBM, get_trained_model_from_csv, get_pkl_model


class ModelMetrics:
    def __init__(self, input_lgbm: ValorantLGBM):
        self.model_obj = input_lgbm
        self.model = input_lgbm.model
        self.X = input_lgbm.X
        self.X_train = input_lgbm.X_train
        self.X_test = input_lgbm.X_test
        self.Y_train = input_lgbm.Y_train
        self.Y_test = input_lgbm.Y_test
        self.pred_proba, self.pred_proba_test = [None] * 2
        self.y_score = self.get_y_score()

    def get_brier_score(self) -> float:
        y_true = self.Y_test
        if self.pred_proba is None:
            self.pred_proba = self.model.predict_proba(self.X_train)
        if self.pred_proba_test is None:
            self.pred_proba_test = self.model.predict_proba(self.X_test)
        y_prob_df = pd.DataFrame(self.pred_proba_test)
        y_prob = y_prob_df[1]
        brier = brier_score_loss(y_true, y_prob)
        print(f"Brier score → {brier}")
        return brier

    def get_brier_score_cross_validation(self):
        return cross_val_score(self.model, self.X_test, self.Y_test, scoring='neg_brier_score', cv=10)

    def get_feature_importance(self):
        feature_imp = pd.DataFrame(sorted(zip(self.model.feature_importances_, self.X.columns)),
                                   columns=['Value', 'Feature'])
        plt.figure(figsize=(10, 10))
        sns.barplot(x="Value", y="Feature", data=feature_imp.sort_values(by="Value", ascending=False))
        sns.set(font_scale=1)
        plt.title('Features')
        plt.tight_layout()
        plt.show()

    def get_model_precision(self):
        plt.figure(figsize=(10, 5))
        pred_proba = self.model.predict_proba(self.X_train)
        pred_proba_test = self.model.predict_proba(self.X_test)
        self.pred_proba = pred_proba
        self.pred_proba_test = pred_proba_test

        gmt = ["accuracy train", "accuracy test", "log loss train", "log loss test", "brier score train",
               "brier score test"]
        metrics = {'Labels': gmt,
                   'Value': [self.model.score(self.X_train, self.Y_train), self.model.score(self.X_test, self.Y_test),
                             log_loss(self.Y_train, pred_proba), log_loss(self.Y_test, pred_proba_test),
                             brier_score_loss(self.Y_train, pd.DataFrame(pred_proba)[1]),
                             brier_score_loss(self.Y_test, pd.DataFrame(pred_proba_test)[1])]
                   }
        sns.set_context(rc={'patch.linewidth': 2.0})
        sns.set(font_scale=1.3)
        ax = sns.barplot(x='Labels', y='Value', data=metrics, linewidth=2.0, edgecolor=".2", zorder=3,
                         palette=sns.color_palette("deep"))

        plt.ylabel('%')
        ax.grid(linewidth=1, color='white', zorder=0)
        ax.set_facecolor("#d7d7e0")
        plt.title("Model performance metrics")
        plt.show()

    def get_confusion_matrix(self):
        plt.figure(figsize=(8, 6))
        cm = confusion_matrix(self.Y_test, self.model.predict(self.X_test, num_iteration=50))
        cm = (cm / cm.sum(axis=1).reshape(-1, 1))

        sns.heatmap(cm, cmap="YlGnBu", vmin=0., vmax=1., annot=True, annot_kws={'size': 45})
        plt.title("wa", fontsize=5)
        plt.ylabel('Predicted label')
        plt.xlabel('True label')
        plt.show()

    def get_f1_score(self):
        Y_pred = self.model.predict(self.X_test)
        f1 = classification_report(self.Y_test, Y_pred, output_dict=True)["weighted avg"]["f1-score"]
        print(f"F1 score → {f1}")

    def get_y_score(self):
        return self.model_obj.model.predict_proba(self.model_obj.X_test)[:, 1]

    def get_tp_fp_rates(self) -> dict:
        false_positive_rate, true_positive_rate, threshold = roc_curve(self.model_obj.Y_test, self.y_score)
        return {"false_positive_rate": false_positive_rate, "true_positive_rate": true_positive_rate,
                "threshold": threshold}

    def get_roc_auc_score(self) -> float:
        y_score = self.y_score
        score = roc_auc_score(self.model_obj.Y_test, y_score)
        print('roc_auc_score for LightGBM: ', score)
        return score

    def plot_roc_curve(self):
        auc_dict = self.get_tp_fp_rates()
        plt.subplots(1, figsize=(10, 7))
        plt.title('Receiver Operating Characteristic - LightGBM')
        false_positive_rate = auc_dict["false_positive_rate"]
        true_positive_rate = auc_dict["true_positive_rate"]
        plt.plot(false_positive_rate, true_positive_rate)
        plt.plot([0, 1], ls="--")
        plt.plot([0, 0], [1, 0], c=".7"), plt.plot([1, 1], c=".7")
        plt.ylabel('True Positive Rate')
        plt.xlabel('False Positive Rate')
        plt.show()

    def show_all(self):
        self.get_feature_importance()
        self.get_model_precision()
        self.get_brier_score()
        self.get_confusion_matrix()
        self.get_f1_score()
        self.get_roc_auc_score()
        self.plot_roc_curve()


def __main():
    vm = get_trained_model_from_csv()
    mm = ModelMetrics(vm)
    mm.show_all()


if __name__ == "__main__":
    __main()
