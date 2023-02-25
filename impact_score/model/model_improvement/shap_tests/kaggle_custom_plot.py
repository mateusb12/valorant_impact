from typing import List

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
from matplotlib.figure import Figure

from impact_score.model.model_improvement.shap_tests.kaggle_shap_decision import get_fifa_example, get_valorant_example


def scatter_plot_probabilities(ax: plt.Axes, feature_names: List[str], feature_values: List,
                               probabilities: List[float]):
    previous_x, previous_y, previous_probability = None, None, None
    for i, (feature_name, probability) in enumerate(zip(feature_names, probabilities)):
        new_x = probability - 0.5
        if i == 0:
            new_y = i + 0.03
        elif i == len(feature_names) - 1:
            new_y = i - 0.04
        else:
            new_y = i + 0.05

        # Plot the point
        ax.scatter(new_x, i, color='green', zorder=4)

        if previous_x is not None and previous_y is not None:
            coord_a, coord_b = [previous_x, new_x], [previous_y, new_y]
            ax.plot(coord_a, coord_b, color='purple', linestyle='-.', linewidth=1.5, alpha=0.56)
            ax.axhline(i, color='gray', linestyle='--', linewidth=.7)

        if i != 0:
            probability_shift = (probability - previous_probability)
            ax.annotate(f"{feature_values[i]} ({probability:.2%})", (new_x, new_y), xytext=(10, -2),
                        textcoords='offset pixels', ha='left', va='top', fontsize=11, color='black')

        previous_x, previous_y = new_x, new_y
        previous_probability = probability

    for i in range(len(probabilities) - 1):
        ax.plot([probabilities[i], probabilities[i + 1]],
                [feature_values[i], feature_values[i + 1]], color='blue', linewidth=2)


def plot_bottom_axis(ax: plt.Axes, feature_names: List[str], probabilities: List[float]):
    ax.set_yticks(range(len(feature_names)))
    ax.set_yticklabels(feature_names)
    ax.set_xlabel('Impact on Probability', fontsize=14)
    ticks = np.arange(-.5, .75, 0.25)
    ax.set_xticks(ticks)
    ax.set_xlim([-0.5, max(probabilities) - 0.3])  # Set x-limits
    ax.set_ylim([0, len(feature_names) - 1])
    ax.axvline(x=0, color='black')
    return ax


def plot_upper_axis(ax: plt.Axes, fig: Figure) -> plt.Axes:
    ax2 = ax.twiny()
    x_ticks = ax.get_xticks()
    new_labels = [100 * (x + 0.5) for x in x_ticks]
    new_labels = [f"{w}%" for w in new_labels]
    ax2.set_xticks(ax.get_xticks())
    ax2.set_xticklabels(new_labels)
    ax2.set_xlim(ax.get_xlim())
    ax2.set_ylim(ax.get_ylim())
    ax2.set_xlabel('Attackers Win Probability', fontsize=14)
    ax2.xaxis.set_label_coords(0.47, 1.1)

    plot_colored_scale_bar(fig)
    return ax2


def plot_colored_scale_bar(fig: Figure):
    cb_axes = fig.add_axes([0.125, 0.88, 0.7746, 0.015])
    color_map = plt.cm.coolwarm
    norm = Normalize(vmin=0, vmax=1)
    scalar_map = ScalarMappable(norm=norm, cmap=color_map)
    color_bar = fig.colorbar(scalar_map, cax=cb_axes, orientation='horizontal')
    color_bar.set_ticks([])
    color_bar.set_ticklabels([])
    cb_axes.set_axisbelow(True)
    cb_axes.set_zorder(1)


def custom_decision_plot(input_sample: pd.Series, probabilities: list[float]):
    input_sample_df = pd.DataFrame(input_sample).T
    input_sample_df.insert(0, " ", 70)
    feature_values = input_sample_df.values.tolist()[0]
    feature_names = input_sample_df.columns.tolist()
    fig, ax = plt.subplots(figsize=(10, 6))

    ax = plot_bottom_axis(ax, feature_names, probabilities)
    ax2 = plot_upper_axis(ax, fig)

    scatter_plot_probabilities(ax, feature_names, feature_values, probabilities)

    plt.show()


def _create_custom_example():
    custom_probabilities = [0.5, 0.1, 0.67, 0.88, 0.35, 0.12]
    custom_feature_values = [100, 120, 150, 170, 200]
    custom_feature_names = ["feature1", "feature2", "feature3", "feature4", "feature5"]
    custom_feature_sample = pd.Series(custom_feature_values, index=custom_feature_names)
    return custom_feature_sample, custom_probabilities


def __main():
    # __hidden()
    # custom_feature_sample, custom_probabilities = create_custom_example()
    sample, probabilities = get_fifa_example()
    # sample, probabilities = get_valorant_example()
    custom_decision_plot(sample, probabilities)


if __name__ == '__main__':
    __main()
