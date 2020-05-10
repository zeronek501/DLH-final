# Overview
This repo contains our problem descriptions and architecture for evaluating the feasibility *FFT-CNNs* (CNNs in which the convolution operation in the time domain is swapped with matrix multiplication in the Fourier domain by the convolution theorem) in Timeloop/Accelergy. The motivation behind *FFT-CNNs* is the fact that overall operation is reduced compared to conventional CNNs. This project attempts a first step towards a rigorous study of *FFT-CNNs* accelerators. Timeloop was designed for CNN accelerator simulation which restricted the variants of FFT algorithms we considered. We settled on representing the constant-geomtery FFT algorithm based on our intuition that it maps more appropriately to hardware but also because it was less challenging to map to Timeloop's loop-nest representation.

## Infrastructure changes
### Modified MAC
Our primitive operation in FFT-Convolution is more than a single integer MAC. We model it as 3 integer multiplications and 2 integer, i.e., similar to a complex multiplication. We model this by scaling the energy and latency requirements of an intmac in our MAC unit appropriately. The logic is found in [aladdin_table.py](workspace/estimation_plug_ins/accelergy-aladdin-plug-in/aladdin_table.py) which reads our new energy estimation data for [multiplication](workspace/estimation_plug_ins/accelergy-aladdin-plug-in/data/fft_mult.csv) and [multiplication](workspace/estimation_plug_ins/accelergy-aladdin-plug-in/data/fft_add.csv).

### Workload Generation
Script to generate FFT, GEMM and Convolution workloads for alexnet and sweep simulations for eyeriss and a custom architecture

python construct_workloads conv_alexnet eyeriss_like
python construct_fft_workloads conv_alexnet eyeriss_like

### FFT-CNN Architecture
	now need to store real, imaginary
	large memory requirements for gemm

# Run Instructions
accelergyTables -r PIM_estimation_plugins
python sweep.py fft_alexnet fft_convolve/fft_arch_optim
	generates to output directory

# Baseline
We use an [architecture based on Eyeriss](workspace/example_designs/eyeriss_like) as our baseline comparison. In our experiments we run the [AlexNet workloads](workspace/layer_shapes/AlexNet) through the Timeloop simulation.
