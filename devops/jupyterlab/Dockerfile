# Base Image
FROM nvidia/cuda:12.2.0-devel-ubuntu22.04

# Set Label
LABEL maintainer="Kailash Lohar <kailash@aganitha.ai>"

# Set Working Directory
WORKDIR /home

# Install Utilities & Miniconda Conda Environment
RUN apt-get update && \
    apt-get install -y make cmake wget curl git parallel gcc g++ ocl-icd-libopencl1 opencl-headers clinfo gnupg python3 python3-pip \
    libboost-system-dev libboost-thread-dev libboost-serialization-dev libboost-filesystem-dev libboost-program-options-dev libboost-timer-dev \
    python3-distutils python3-lxml python3-openbabel libgl1 libxrender1 libxext6 && \
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    bash Miniconda3-latest-Linux-x86_64.sh -b -p /miniconda && \
    rm -rf /var/lib/apt/lists/* && rm Miniconda3-latest-Linux-x86_64.sh
ENV PATH=/miniconda/bin:$PATH
COPY environment.yaml .
RUN conda env create -f environment.yaml && conda clean --all --yes

# Install Boost 1.77.0
RUN wget https://sourceforge.net/projects/boost/files/boost/1.77.0/boost_1_77_0.tar.gz && \
    tar -xzf boost_1_77_0.tar.gz && rm boost_1_77_0.tar.gz && cd /home/boost_1_77_0 && ./bootstrap.sh && ./b2 -d2 install

# Install NVIDIA Container Runtime
RUN curl -s -L https://nvidia.github.io/nvidia-container-runtime/gpgkey | apt-key add - \
    && distribution=$(. /etc/os-release; echo $ID$VERSION_ID) \
    && curl -s -L https://nvidia.github.io/nvidia-container-runtime/$distribution/nvidia-container-runtime.list | tee /etc/apt/sources.list.d/nvidia-container-runtime.list
RUN mkdir -p /etc/OpenCL/vendors && echo "libnvidia-opencl.so.1" > /etc/OpenCL/vendors/nvidia.icd

# Set IOPub message rate limit
ENV JUPYTER_IOPUB_MSG_RATE_LIMIT=10000

# Copy and Compile Uni-Dock
COPY /unidock /home
RUN cmake -B build && cmake --build build -j`nprocs` && cmake --install build 

WORKDIR /home
EXPOSE 7777

CMD ["bash", "-c", "source activate agandock && jupyter lab --ip=0.0.0.0 --port=7777 --no-browser --allow-root --NotebookApp.token='' --NotebookApp.password=''"]