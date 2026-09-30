FROM ubuntu:24.04
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y build-essential cmake git python3-dev libboost-all-dev && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 --branch 2024.02a https://gitlab.com/yade-dev/trunk.git /opt/yade && cmake -S /opt/yade -B /opt/yade/build && cmake --build /opt/yade/build -j2 && cmake --install /opt/yade/build
CMD ["yade", "--version"]
