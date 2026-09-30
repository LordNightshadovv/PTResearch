FROM ubuntu:24.04
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y curl gnupg ca-certificates && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL https://dl.openfoam.org/gpg.key | gpg --dearmor > /usr/share/keyrings/openfoam.gpg && echo "deb [signed-by=/usr/share/keyrings/openfoam.gpg] https://dl.openfoam.org/ubuntu noble main" > /etc/apt/sources.list.d/openfoam.list
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y openfoam14 && rm -rf /var/lib/apt/lists/*
CMD ["/bin/bash"]
