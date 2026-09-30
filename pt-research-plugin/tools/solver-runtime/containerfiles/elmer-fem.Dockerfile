FROM ubuntu:24.04
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y git cmake gfortran g++ make && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 --branch release-9.0 https://github.com/ElmerCSC/elmerfem.git /opt/elmerfem && cmake -S /opt/elmerfem -B /opt/elmerfem/build && cmake --build /opt/elmerfem/build -j2 && cmake --install /opt/elmerfem/build
CMD ["ElmerSolver"]
