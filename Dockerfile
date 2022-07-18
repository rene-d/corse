FROM texlive/texlive:latest

RUN apt-get update && apt-get install -y python3-numpy
COPY corsetex.py /
WORKDIR /out
ENTRYPOINT ["/corsetex.py"]