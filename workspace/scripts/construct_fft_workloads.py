# Copyright (c) 2019, NVIDIA CORPORATION. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#  * Neither the name of NVIDIA CORPORATION nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY
# OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import functools
import yaml
import math

def prod (l):
    return functools.reduce(lambda x, y: x*y, l)

def rewrite_dict(src, dst, bdict):
    print('Workload Dimensions:')
    for k, v in bdict.items():
        print('  %s         = %s' % (k,v))
    print()

    with open(src, "r") as f:
        config = yaml.load(f, Loader = yaml.SafeLoader)

    for k, v in bdict.items():
        config['problem']['instance'][k] = v

    with open(dst, "w") as f:
        f.write(yaml.dump(config))

def rewrite_convolve_bounds(src, dst, workload_bounds):
    w, h, c, n, m, s, r, wpad, hpad, wstride, hstride = workload_bounds
    q = int((w - s + 2 * wpad) / wstride) + 1
    p = int((h - r + 2 * hpad) / hstride) + 1
    bdict = {'W':w, 'H': h, 'C': c, 'M': m, \
            'S': s, 'R': r, 'P': p, 'Q': q, \
            'N': n, 'W-pad':wpad, 'H-pad':hpad, \
            'W-stride': wstride, 'H-stride': hstride}
    rewrite_dict(src, dst, bdict)

def get_nearest_upper_power_two(n):
    x = (int)(math.log(n, 2))
    return 2**(x+1)

def rewrite_fft_bounds(src, dst, workload_bounds, forward=True):
    w, h, c, n, m, s, r, wpad, hpad, wstride, hstride = workload_bounds
    padded_w = get_nearest_upper_power_two(w + s - 1)
    padded_h = get_nearest_upper_power_two(h + s - 1)

    nn = n
    cc = c
    hh = padded_h
    ss = (int)(math.log(padded_h, 2))
    jj = padded_h // 2
    oo = jj

    if not forward:
        cc = m

    #constants
    #tt, uu, vv, xx, yy, zz, ll = 2

    bdict = {'N': nn, 'C': cc, 'H': hh, 'S': ss, 'J': jj, 'O':oo}

    rewrite_dict(src, dst, bdict)

def rewrite_gemm_bounds(src, dst, workload_bounds, forward=True):
    w, h, c, n, m, s, r, wpad, hpad, wstride, hstride = workload_bounds
    padded_w = get_nearest_upper_power_two(w + s - 1)
    padded_h = get_nearest_upper_power_two(h + s - 1)
    nn = n
    cc = c
    mm = m
    ww = padded_w
    hh = padded_h
    ss = math.log(padded_h, 2)
    jj = padded_h // 2
    oo = jj

    bdict = {'N': nn, 'C': cc, 'M': mm, 'W': ww, 'H': hh,
            'S': ss, 'J': jj, 'O':oo}
    #constants
    #xx, yy, zz = 2

    rewrite_dict(src, dst, bdict)

def rewrite_workload_bounds(src, dst, workload_bounds):
    w, h, c, n, m, s, r, wpad, hpad, wstride, hstride = workload_bounds
    if wstride != 1:
        return
    rewrite_fft_bounds(src[:-5] + "_fft.yaml", dst[:-5] + "_fft.yaml", workload_bounds, forward=True)
    rewrite_gemm_bounds(src[:-5] + "_gemm.yaml", dst[:-5] + "_gemm.yaml", workload_bounds)
    rewrite_fft_bounds(src[:-5] + "_fft.yaml", dst[:-5] + "_ifft.yaml", workload_bounds, forward=False)

def create_folder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print('ERROR: Creating directory. ' + directory)
        sys.exit()

if __name__=="__main__":

    import os, inspect, sys
    this_file_path = os.path.abspath(inspect.getfile(inspect.currentframe()))
    this_directory = os.path.dirname(this_file_path)

    sys.path.append(this_directory)
    from cnn_layers import *

    if len(sys.argv) < 2:
        print('Usage: python3 construct_workloads.py <dnn_model_name>')
        sys.exit(0)
    net_name = sys.argv[1]

    # construct appropriate folder and file paths
    create_folder(os.path.abspath(os.path.join(this_directory, '..', 'layer_shapes', net_name)))
    config_abspath = os.path.join(this_directory, 'sample.yaml')

    # just test that path points to a valid config file.
    with open(config_abspath, 'r') as f:
        config = yaml.load(f, Loader = yaml.SafeLoader)

    # construct problem shapes for each layer
    for i in range(0, len(fft_layers)):
        problem = fft_layers[i]
        file_name = net_name + '_' + 'layer' + str(i+1) + '.yaml'
        file_path = os.path.abspath(os.path.join(this_directory, '..', 'layer_shapes', net_name, file_name))
        rewrite_workload_bounds(config_abspath, file_path, problem)
