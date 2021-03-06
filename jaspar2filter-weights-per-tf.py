#!/usr/bin/env python

from Bio import motifs
import click
import numpy as np
import os
import pickle

CONTEXT_SETTINGS = {
    "help_option_names": ["-h", "--help"],
}

@click.command(no_args_is_help=True, context_settings=CONTEXT_SETTINGS)
@click.argument(
    "out_file",
    type=click.Path(resolve_path=True),
)
@click.option(
    "-f", "--filter-size",
    help="Filter size.",
    type=int,
    default=19,
    show_default=True,
)

def main(**params):

    # Initialize
    base_dir = os.path.dirname(os.path.realpath(__file__))
    data_dir = os.path.join(base_dir, "data")

    # Parse profiles
    profiles = {}
    jaspar_file = os.path.join(data_dir,
        "JASPAR2020_CORE_vertebrates_non-redundant_pfms_jaspar.txt")
    with open(jaspar_file) as handle:
        for m in motifs.parse(handle, "jaspar"):
            profiles.setdefault(m.matrix_id, m)

    # For each profile...
    filters = {}
    for matrix_id in profiles:
        m = profiles[matrix_id]
        tfs = m.name.upper().split("(")[0].split("::")
        pwm = [list(i) for i in m.pwm.values()]
        pwm = _PWM_to_filter_weights(list(map(list, zip(*pwm))), params["filter_size"])
        for tf in tfs:
            filters.setdefault(tf, [])
            filters[tf].append([matrix_id, pwm, np.flip(pwm)])

    # Save
    with open(params["out_file"], "wb") as handle:
        pickle.dump(filters, handle, protocol=pickle.HIGHEST_PROTOCOL)

def _PWM_to_filter_weights(pwm, filter_size=19):

    # Initialize
    lpop = 0
    rpop = 0

    pwm = [[.25,.25,.25,.25]]*filter_size+pwm+[[.25,.25,.25,.25]]*filter_size

    while len(pwm) > filter_size:
        if max(pwm[0]) < max(pwm[-1]):
            pwm.pop(0)
            lpop += 1
        elif max(pwm[-1]) < max(pwm[0]):
            pwm.pop(-1)
            rpop += 1
        else:
            if lpop > rpop:
                pwm.pop(-1)
                rpop += 1
            else:
                pwm.pop(0)
                lpop += 1

    return(np.array(pwm) - .25)

if __name__ == "__main__":
    main()