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
    motifs_dir = os.path.join(base_dir, "motifs")

    # Parse binding modes
    binding_modes = {}
    binding_modes_file = os.path.join(motifs_dir, "leaf_to_cluster.tab")
    with open(binding_modes_file) as handle:
        for line in handle:
            matrix_id, cluster = line.strip("\n").split("\t")
            matrix_id = matrix_id.split("_")
            binding_modes.setdefault(int(cluster), [])
            binding_modes[int(cluster)].append("%s.%s" % \
                (matrix_id[-2], matrix_id[-1]))

    # Parse profiles
    profiles = {}
    ixs = {"A":0, "C":1, "G":2, "T":3}
    jaspar_file = os.path.join(motifs_dir,
        "JASPAR2020_CORE_vertebrates_redundant_pfms_jaspar.txt")
    with open(jaspar_file) as handle:
        for m in motifs.parse(handle, "jaspar"):
            m.pseudocounts = motifs.jaspar.calculate_pseudocounts(m)
            consensus_seq = str(m.consensus)
            information_content = sum([m.pssm[ixs[consensus_seq[i]]][i] \
                for i in range(len(consensus_seq))])
            profiles.setdefault(m.matrix_id, (m, information_content))

    # For each binding mode...
    filters = {}
    for bm in sorted(binding_modes):
        binding_modes[bm].sort(key=lambda x: profiles[x][-1], reverse=True)
        m = profiles[binding_modes[bm][0]][0]
        filters.setdefault(m.matrix_id, [m.name, bm])
        pwm = [list(i) for i in m.pwm.values()]
        pwm = _resize_PWM(list(map(list, zip(*pwm))), params["filter_size"])
        filters[m.matrix_id].append(pwm)
        filters[m.matrix_id].append(np.flip(pwm))

    # Save
    with open(params["out_file"], 'wb') as handle:
        pickle.dump(filters, handle, protocol=pickle.HIGHEST_PROTOCOL)

def _resize_PWM(pwm, filter_size=19):

    # Initialize
    lpop = 0
    rpop = 0

    pwm = [[0., 0., 0., 0.]]*filter_size + pwm + [[0., 0., 0., 0.]]*filter_size

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

    return(np.array(pwm))

if __name__ == "__main__":
    main()