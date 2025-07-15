# Base image
FROM nvidia/cuda:12.2.0-devel-ubuntu22.04

# Set Label
LABEL maintainer="Kailash Lohar <kailashlohariitkgp@gmail.com>"

# Set Working Directory
WORKDIR /app

RUN apt-get update && \
    apt-get install -y make cmake wget curl git parallel gcc g++ ocl-icd-libopencl1 opencl-headers clinfo gnupg python3 python3-pip \
    libboost-system-dev libboost-thread-dev libboost-serialization-dev libboost-filesystem-dev libboost-program-options-dev libboost-timer-dev \
    python3-distutils python3-lxml python3-openbabel libgl1 libxrender1 libxext6 && \
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    bash Miniconda3-latest-Linux-x86_64.sh -b -p /miniconda && \
    rm -rf /var/lib/apt/lists/* && rm Miniconda3-latest-Linux-x86_64.sh
ENV PATH=/miniconda/bin:$PATH
COPY devops/nextjs/nextjs.yaml .
RUN conda env create -f nextjs.yaml && conda clean --all --yes \
    && pip install posebusters lxml

# Install Boost 1.77.0
RUN wget https://sourceforge.net/projects/boost/files/boost/1.77.0/boost_1_77_0.tar.gz/download -O boost_1_77_0.tar.gz && \
    tar -xzf boost_1_77_0.tar.gz && rm boost_1_77_0.tar.gz

# Install NVIDIA Container Runtime
RUN curl -s -L https://nvidia.github.io/nvidia-container-runtime/gpgkey | apt-key add - \
    && distribution=$(. /etc/os-release; echo $ID$VERSION_ID) \
    && curl -s -L https://nvidia.github.io/nvidia-container-runtime/$distribution/nvidia-container-runtime.list | tee /etc/apt/sources.list.d/nvidia-container-runtime.list
RUN mkdir -p /etc/OpenCL/vendors && echo "libnvidia-opencl.so.1" > /etc/OpenCL/vendors/nvidia.icd

# Copy and Compile Uni-Dock
COPY devops/nextjs/unidock /app
RUN cmake -B build && cmake --build build -j`nprocs` && cmake --install build

# Set AGANDOCK_SCRIPTS environment variable
ENV AGANDOCK_SCRIPTS=/app/main/nextjs/scripts

WORKDIR /app

# Expose Streamlit Port
CMD ["tail", "-f", "/dev/null"]