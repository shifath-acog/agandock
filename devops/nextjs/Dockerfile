# Stage 1: Build Next.js
FROM node:18 AS nextjs-builder
WORKDIR /app/devops/nextjs
COPY devops/nextjs/package*.json ./
COPY devops/nextjs/ ./
RUN npm install --legacy-peer-deps && npm run build

# Stage 2: Main image
FROM nvidia/cuda:12.2.0-devel-ubuntu22.04

# Set Label
LABEL maintainer="Kailash Lohar <kailashlohariitkgp@gmail.com>"

# Set Working Directory
WORKDIR /app

# Install system dependencies and Miniconda
RUN apt-get update && \
    apt-get install -y make cmake wget curl git parallel gcc g++ ocl-icd-libopencl1 opencl-headers clinfo gnupg python3 python3-pip \
    libboost-system-dev libboost-thread-dev libboost-serialization-dev libboost-filesystem-dev libboost-program-options-dev libboost-timer-dev \
    python3-distutils python3-lxml python3-openbabel libgl1 libxrender1 libxext6 && \
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    bash Miniconda3-latest-Linux-x86_64.sh -b -p /miniconda && \
    rm -rf /var/lib/apt/lists/* && rm Miniconda3-latest-Linux-x86_64.sh
ENV PATH=/miniconda/bin:$PATH

# Copy environment file
COPY devops/nextjs/nextjs.yaml .

# Accept ToS for all channels and clean Conda cache
RUN conda config --set channel_priority flexible && \
    conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main && \
    conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r && \
    conda tos accept --override-channels --channel https://conda.anaconda.org/nvidia && \
    conda tos accept --override-channels --channel https://conda.anaconda.org/pytorch && \
    conda tos accept --override-channels --channel https://conda.anaconda.org/conda-forge && \
    conda clean --all --yes && rm -rf /miniconda/pkgs/*

# Create Conda environment and clean up
RUN conda env create -f nextjs.yaml && \
    conda clean --all --yes && \
    pip install posebusters lxml && \
    rm -rf /miniconda/pkgs/*

# Install Boost 1.77.0
RUN wget https://sourceforge.net/projects/boost/files/boost/1.77.0/boost_1_77_0.tar.gz/download -O boost_1_77_0.tar.gz && \
    tar -xzf boost_1_77_0.tar.gz && rm boost_1_77_0.tar.gz

# Install NVIDIA Container Toolkit
RUN curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg && \
    curl -s -L https://nvidia.github.io/libnvidia-container/stable/ubuntu22.04/libnvidia-container.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    tee /etc/apt/sources.list.d/nvidia-container-toolkit.list && \
    apt-get update && \
    mkdir -p /etc/OpenCL/vendors && echo "libnvidia-opencl.so.1" > /etc/OpenCL/vendors/nvidia.icd && \
    rm -rf /var/lib/apt/lists/*

# Copy and compile Uni-Dock
COPY devops/nextjs/unidock /app
RUN cmake -B build && cmake --build build -j$(nproc) && cmake --install build

# Copy Next.js build artifacts
COPY --from=nextjs-builder /app/devops/nextjs/.next /app/devops/nextjs/.next

# Install Node.js via conda
RUN conda install -y -c conda-forge nodejs=18

# Set AGANDOCK_SCRIPTS environment variable
ENV AGANDOCK_SCRIPTS=/app/main/nextjs/scripts

# Copy and set up startup script
COPY devops/nextjs/start.sh /start.sh
RUN chmod +x /start.sh

# Expose Next.js port
EXPOSE 3000

# Set working directory
WORKDIR /app

# Start Next.js application
CMD ["/start.sh"]