import os
import sys
import mpu

ROOT_PATH = os.path.abspath("..")

if len(sys.argv) != 3:
    print("you should pass layer and design directory as arguments\n")
    exit(0)
LAYER_TYPE=sys.argv[1]
ARCH_TYPE=sys.argv[2]

LAYER_PATH = os.path.join(ROOT_PATH, 'layer_shapes', LAYER_TYPE)

#DESIGN_PATH = os.path.join(ROOT_PATH, 'example_designs', 'fft_convolve', 'fft_arch_optim')
DESIGN_PATH = os.path.join(ROOT_PATH, 'example_designs', ARCH_TYPE)

COMPONENTS_PATH = os.path.join(DESIGN_PATH, 'arch', 'components', '*')

ARCH_PATH = {}
ARCH_PATH['conv'] = os.path.join(DESIGN_PATH, 'arch', 'eyeriss_like.yaml')
ARCH_PATH['fft'] = os.path.join(DESIGN_PATH, 'arch', 'fft_eyeriss_optim.yaml')
ARCH_PATH['gemm'] = os.path.join(DESIGN_PATH, 'arch', 'fft_eyeriss_optim.yaml')

ARCH_CONSTRAINTS_PATH = {}
ARCH_CONSTRAINTS_PATH['conv'] = os.path.join(DESIGN_PATH, 'constraints', 'conv_arch_constraints.yaml')
ARCH_CONSTRAINTS_PATH['fft'] = os.path.join(DESIGN_PATH, 'constraints', 'fft_arch_constraints.yaml')
ARCH_CONSTRAINTS_PATH['gemm'] = os.path.join(DESIGN_PATH, 'constraints', 'gemm_arch_constraints.yaml')

MAP_CONSTRAINTS_PATH = {}
MAP_CONSTRAINTS_PATH['conv'] = os.path.join(DESIGN_PATH, 'constraints', 'conv_map_constraints.yaml')
MAP_CONSTRAINTS_PATH['fft'] = os.path.join(DESIGN_PATH, 'constraints', 'fft_map_constraints.yaml')
MAP_CONSTRAINTS_PATH['gemm'] = os.path.join(DESIGN_PATH, 'constraints', 'gemm_map_constraints.yaml')

MAPPER_PATH = os.path.join(DESIGN_PATH, 'mapper', 'mapper.yaml')

OUTPUT_DIR=os.path.join(ROOT_PATH,"output",LAYER_TYPE,ARCH_TYPE)

def run_timeloop_mapper(layer_path, ltype,output_dir):
    os.system("mkdir -p {}".format(output_dir))
    os.chdir(output_dir)
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

def parse_timeloop_stats(output_dir):
    stats_filename = os.path.join(output_dir, "timeloop-mapper.stats.txt")

    # Which sections to parse
    sections = ["Summary Stats"]

    # Holds output stats for each section
    stats_d = {}
    in_section = False
    current_section = ""
    with open(stats_filename) as stats_f:
        for line in stats_f:
            found_sec = [x for x in sections if x in line]
            if len(found_sec) > 0:
                current_section = found_sec[0]
                in_section = True
            elif in_section:
                pass
            else:
                in_section = False
                continue

            # Major atributes
            if ":" in line:
                [attribute, value] = line.split(':')
                if current_section not in stats_d:
                    stats_d[current_section] = {}
                stats_d[current_section][attribute] = value.strip()
            elif "MACCs" in line:
                [_,value] = line.split('=')
                stats_d[current_section]["MACCs"] = value.strip()
            elif "pJ/MACC" in line:
                while "Total" not in line:
                    line = stats_f.next()
                [attribute, value] = line.split('=')
                stats_d[current_section]["Total"] = value.strip()

    art_file = os.path.join(output_dir, "timeloop-mapper.ART.yaml")
    area_key = "Areas (us)"
    stats_d[area_key] = {}
    total_area = 0
    with open(art_file) as art_f:
        for line in art_f:
            if "name:" in line:
                name = line.split(':')[1]
                line = art_f.next()
                area = float(line.split(':')[1].strip())

                # Probably more readble with a Regex
                if "[0.." in name:
                    # Add 1 since we start with 0, e.g., PE[0..255]
                    num_components = int(name.split("..")[1].split("]")[0]) + 1
                    area = num_components * area
                stats_d[area_key][name.strip()] = area
                total_area += area
    stats_d[area_key]["Total"] = total_area
    return stats_d

if __name__ == "__main__":
    print("Project path: ", ROOT_PATH)
    print("Layers path: ", LAYER_PATH)
    print("Sweep list: ", os.listdir(LAYER_PATH))
    stats = {}
    for layer_name in os.listdir(LAYER_PATH):
        layer_path = os.path.join(LAYER_PATH, layer_name)
        layer = layer_name.split('.')[0].strip()
        output_dir = os.path.join(OUTPUT_DIR,layer)

        if "_conv.yaml" in layer_name:
            ltype = "conv"
        elif "_fft.yaml" in layer_name or "ifft" in layer_name:
            ltype = "fft"
        elif "_gemm.yaml" in layer_name:
            ltype = "gemm"

        if os.path.isfile(os.path.join(output_dir,"timeloop-mapper.stats.txt")):
            print("WARNING: output already exists at {}...not re-running timeloop".format(output_dir))
            stats[layer] = mpu.io.read(os.path.join(output_dir, layer) + ".pickle")
        else:
            run_timeloop_mapper(layer_path, ltype, output_dir)
            stats[layer] = parse_timeloop_stats(output_dir)
            mpu.io.write(os.path.join(output_dir, layer) + ".pickle", stats[layer])

    for layer,results in stats.items():
        print("=== " + layer + " results ===")
        for section,values in results.items():
            print("\t" + section)
            for k,v in values.items():
                print("\t\t{}: {}".format(k,v))
