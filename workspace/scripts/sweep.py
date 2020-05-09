import os
import sys

ROOT_PATH = os.path.abspath("..")

if len(sys.argv) != 3:
    print("you should pass layer and design directory as arguments\n")
    exit(0)
LAYER_PATH = os.path.join(ROOT_PATH, 'layer_shapes', sys.argv[1])

#DESIGN_PATH = os.path.join(ROOT_PATH, 'example_designs', 'fft_convolve', 'fft_arch_optim')
DESIGN_PATH = os.path.join(ROOT_PATH, 'example_designs', sys.argv[2])

COMPONENTS_PATH = os.path.join(DESIGN_PATH, 'arch', 'components', '*')

ARCH_PATH = {}
ARCH_PATH['conv'] = os.path.join(DESIGN_PATH, 'arch', 'simple_output_stationary.yaml')
ARCH_PATH['fft'] = os.path.join(DESIGN_PATH, 'arch', 'fft_eyeriss_optim.yaml')
ARCH_PATH['gemm'] = os.path.join(DESIGN_PATH, 'arch', 'gemm_eyeriss.yaml')

ARCH_CONSTRAINTS_PATH = {}
ARCH_CONSTRAINTS_PATH['conv'] = os.path.join(DESIGN_PATH, 'constraints', 'conv_arch_constraints.yaml')
ARCH_CONSTRAINTS_PATH['fft'] = os.path.join(DESIGN_PATH, 'constraints', 'fft_arch_constraints.yaml')
ARCH_CONSTRAINTS_PATH['gemm'] = os.path.join(DESIGN_PATH, 'constraints', 'gemm_arch_constraints.yaml')

MAP_CONSTRAINTS_PATH = {}
MAP_CONSTRAINTS_PATH['conv'] = os.path.join(DESIGN_PATH, 'constraints', 'conv_map_constraints.yaml')
MAP_CONSTRAINTS_PATH['fft'] = os.path.join(DESIGN_PATH, 'constraints', 'fft_map_constraints.yaml')
MAP_CONSTRAINTS_PATH['gemm'] = os.path.join(DESIGN_PATH, 'constraints', 'gemm_map_constraints.yaml')

MAPPER_PATH = os.path.join(DESIGN_PATH, 'mapper', 'mapper.yaml')

def run_timeloop_mapper(layer_path, ltype):
    os.chdir(ROOT_PATH)
    os.system("mkdir -p output && cd output")
    cmd_list = ["timeloop-mapper"]
    cmd_list.append(COMPONENTS_PATH)
    cmd_list.append(MAPPER_PATH)

    cmd_list.append(ARCH_CONSTRAINTS_PATH[ltype])
    cmd_list.append(ARCH_PATH[ltype])

    cmd_list.append(layer_path)
    cmd = " ".join(cmd_list)
    print(cmd)
    os.system(cmd)
    os.system("echo timeloop-mapper.map.txt")

if __name__ == "__main__":
    print("Project path: ", ROOT_PATH)
    print("Layers path: ", LAYER_PATH)
    print("Sweep list: ", os.listdir(LAYER_PATH))
    for layer_name in os.listdir(LAYER_PATH):
        layer_path = os.path.join(LAYER_PATH, layer_name)
        if "_conv.yaml" in layer_name:
            ltype = "conv"
        elif "_fft.yaml" in layer_name or "ifft" in layer_name:
            ltype = "fft"
        elif "_gemm.yaml" in layer_name:
            ltype = "gemm"
        run_timeloop_mapper(layer_path, ltype)

