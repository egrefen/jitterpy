# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.4.2
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# +
import numpy as np
import pickle
import os

import datetime
import matplotlib.dates as mdates

import ipywidgets as widgets
from ipywidgets import interact, interactive, fixed, interact_manual
import glob

from matplotlib import pyplot as plt


# -

def get_segments(seq, span):
    segments = []
    buffer = []
    start = seq[0][0]
    for time, icmp, val in seq:
        if (time-start).total_seconds() >= span:
            width = (buffer[-1][0]-buffer[0][0]).total_seconds() + 1
            segments.append((buffer, width))
            buffer = []
            start = time
        buffer.append((time, icmp, val))
    if buffer:
        width = (buffer[-1][0]-buffer[0][0]).total_seconds() + 1
        segments.append((buffer, width))
    return segments


# +
def plot(filename, span, tolerance):
    
    pings, jitter, missed = pickle.load(open(filename, "rb"))

    if not pings:
        raise Exception("No pings found!")

    start_time = pings[0][0]
    end_time = pings[-1][0]
    total_span = (end_time-start_time)

    def seconds_from_start(time):
        return int((time-start_time).total_seconds())

    print("total time spanned:", total_span)

    ping_segments = get_segments(pings, span)
    ping_data, ping_widths = zip(*ping_segments)
    ping_times = [d[0][0] for d in ping_data]
    ping_xs_times = [t.strftime("%d/%m %H:%M:%S") for t in ping_times]
    ping_xs_secs = np.array([seconds_from_start(t) for t in ping_times])
    ping_y_vals = [np.array([v for _, _, v in d]) for d in ping_data]
    ping_ys = [a.mean() for a in ping_y_vals]
    ping_ys_std = [a.std() for a in ping_y_vals]

    jitter_segments = get_segments(jitter, span)
    jitter_data, jitter_widths = zip(*jitter_segments)
    jitter_times = [d[0][0] for d in jitter_data]
    jitter_xs_times = [t.strftime("%d/%m %H:%M:%S") for t in jitter_times]
    jitter_xs_secs = np.array([seconds_from_start(t) for t in jitter_times])
    jitter_y_vals = [np.array([v for _, _, v in d]) for d in jitter_data]
    jitter_ys = [a.mean() for a in jitter_y_vals]
    jitter_ys_std = [a.std() for a in jitter_y_vals]

    fig, ax = plt.subplots(figsize=(16, 8), constrained_layout=False)
    ax.bar(jitter_xs_secs, jitter_ys, yerr=jitter_ys_std, width=jitter_widths, align='edge', label="jitter", alpha=.5)
    ax.errorbar(ping_xs_secs+int(span/2)-1, ping_ys, yerr=ping_ys_std, label="pings", alpha=.5)
    ax.hlines(tolerance, 0, 80, label="jitter tolerance", alpha=.5, linestyles='dashed')

    ax.set_xlabel("seconds from start")
    ax.set_ylabel("ms")
    ax.legend()

    ax2 = ax.twiny()
    ax2.spines["bottom"].set_position(("axes", -0.1))
    ax2.set_xlim(ax.get_xlim())
    ax2.set_xticks(jitter_xs_secs)
    ax2.set_xticklabels(jitter_xs_times, rotation=20)
    ax2.xaxis.set_ticks_position('bottom') # set the position of the second x-axis to bottom
    ax2.xaxis.set_label_position('bottom')
    ax2.set_xlabel('timestamp', labelpad=10)



# +
filename = "/Users/egrefen/Desktop/jitter/jitter_200520_10h02.pkl"
span = widgets.BoundedIntText(10, min=1)
span = widgets.BoundedIntText(10, min=1)

interactive(plot, filename=filename, span=span, tolerance=tolerance)
# -


