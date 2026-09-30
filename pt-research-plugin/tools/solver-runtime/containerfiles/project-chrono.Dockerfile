FROM ubuntu:24.04
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y git cmake g++ python3 python3-dev && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 --branch 10.0.0 https://github.com/projectchrono/chrono.git /opt/chrono && cmake -S /opt/chrono -B /opt/chrono/build -DENABLE_MODULE_PYTHON=ON && cmake --build /opt/chrono/build -j2
CMD ["/bin/bash"]
