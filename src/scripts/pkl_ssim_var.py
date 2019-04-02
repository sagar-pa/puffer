#!/usr/bin/env python3

import os
import sys
import yaml
import json
import pickle
import argparse
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from helpers import (
    ssim_index_to_db, get_abr_cc,
    pretty_names, pretty_colors, abr_order)
from collect_data import VIDEO_DURATION


def collect_ssim_var(d, expt_id_cache, args):
    x = {}

    for session in d:
        expt_id = session[-1]

        # exclude contaminated experiments
        if int(expt_id) == 343 or int(expt_id) == 344:
            continue

        if not args.emu:
            expt_config = expt_id_cache[int(expt_id)]
            abr_cc = get_abr_cc(expt_config)
        else:
            abr_cc = tuple(expt_id.split('+'))

        if abr_cc not in x:
            x[abr_cc] = []

        for video_ts in d[session]:
            dsv = d[session][video_ts]

            curr_ssim_index = dsv['ssim_index']
            if curr_ssim_index == 1:
                continue

            prev_ts = video_ts - VIDEO_DURATION
            if prev_ts not in d[session]:
                continue

            prev_ssim_index = d[session][prev_ts]['ssim_index']
            if prev_ssim_index == 1:
                continue

            curr_ssim_db = ssim_index_to_db(curr_ssim_index)
            prev_ssim_db = ssim_index_to_db(prev_ssim_index)

            x[abr_cc].append(abs(curr_ssim_db - prev_ssim_db))

    ssim_var_mean = {}
    ssim_var_std = {}

    print('(ABR, CC), SSIM var mean, SSIM var median')
    for abr_cc in x:
        ssim_var_mean[abr_cc] = np.mean(x[abr_cc])
        ssim_var_std[abr_cc] = np.std(x[abr_cc])
        print('{}, {}, {}'.format(abr_cc, np.mean(x[abr_cc]), np.median(x[abr_cc])))

    return ssim_var_mean, ssim_var_std


def plot_ssim_var_bar(d, stds, plot_cc):
    fig, ax = plt.subplots()

    bar_width = 0.25

    labels = {}

    cnt = 0

    for abr in abr_order:
        if (abr, plot_cc) not in d:
            continue
        pos = cnt

        cnt += 1
        ax.bar(pos, d[(abr, plot_cc)], 1,
               color=pretty_colors[abr],
               label=pretty_names[abr])

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(direction='in')
    ax.set_xticks([])
    ax.set_ylabel('SSIM Variation (dB)')
    ax.set_xlabel(pretty_names[plot_cc])

    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width, box.height * 0.9])
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.25),
                      ncol=3)

    output = 'ssim_var_' + plot_cc + '.png'
    fig.savefig(output)
    sys.stderr.write('Saved plot to {}\n'.format(output))


def plot(expt_id_cache, args):

    if args.pre_dp != None and os.path.isfile(args.pre_dp):
        with open(args.pre_dp, 'rb') as fp:
            ssim_var_mean, ssim_var_std = pickle.load(fp)
    else:
        with open(args.video_data_pickle, 'rb') as fh:
            video_data = pickle.load(fh)

        ssim_var_mean, ssim_var_std = collect_ssim_var(
                video_data, expt_id_cache, args)

        with open('ssim_var.pickle', 'wb') as fp:
            pickle.dump((ssim_var_mean, ssim_var_std), fp)

    #plot_ssim_var_bar(ssim_var_mean, ssim_var_std, 'bbr')
    #plot_ssim_var_bar(ssim_var_mean, ssim_var_std, 'cubic')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--video-data-pickle', required=True)
    parser.add_argument('-e', '--expt-id-cache',
                        default='expt_id_cache.pickle')
    parser.add_argument('-o', '--output', default='tmp')
    parser.add_argument('--emu', action='store_true')
    parser.add_argument('--pre-dp', default='ssim_var.pickle')

    args = parser.parse_args()

    if not args.emu:
        with open(args.expt_id_cache, 'rb') as fh:
            expt_id_cache = pickle.load(fh)

        plot(expt_id_cache, args)
    else:
        # emulation
        plot(None, None, args)


if __name__ == '__main__':
    main()
