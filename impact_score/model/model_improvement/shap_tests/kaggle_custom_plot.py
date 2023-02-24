from typing import List

import numpy as np
from matplotlib import pyplot as plt


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
        ax.scatter(new_x, new_y, color='blue')

        if previous_x is not None and previous_y is not None:
            ax.plot([previous_x, new_x], [previous_y, new_y], color='gray', linestyle='--', linewidth=1)

        if i != 0:
            probability_shift = (probability - previous_probability)
            ax.annotate(f"{feature_values[i]} ({probability_shift:.2%})", (new_x, new_y), xytext=(10, -2),
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


def plot_upper_axis(ax: plt.Axes) -> plt.Axes:
    ax2 = ax.twiny()
    x_ticks = ax.get_xticks()
    new_labels = [100 * (x + 0.5) for x in x_ticks]
    new_labels = [f"{w}%" for w in new_labels]
    ax2.set_xticks(ax.get_xticks())
    ax2.set_xticklabels(new_labels)
    ax2.set_xlim(ax.get_xlim())
    ax2.set_ylim(ax.get_ylim())
    ax2.set_xlabel('Probability', fontsize=14)
    return ax2


def custom_decision_plot():
    probabilities = [0.5, 0.1, 0.67, 0.88, 0.35, 0.12]
    feature_values = [70, 100, 120, 150, 170, 200]
    feature_names = [" ", "feature1", "feature2", "feature3", "feature4", "feature5"]
    fig, ax = plt.subplots(figsize=(10, 6))

    scatter_plot_probabilities(ax, feature_names, feature_values, probabilities)

    ax = plot_bottom_axis(ax, feature_names, probabilities)
    ax2 = plot_upper_axis(ax)

    plt.show()


def __main():
    custom_decision_plot()


if __name__ == '__main__':
    __main()
