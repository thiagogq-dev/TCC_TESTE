FROM python:3.9-slim-bullseye

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        openjdk-11-jre-headless \
        wget libarchive13 libcurl4 libxml2 python3-magic git software-properties-common && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN wget https://github.com/srcML/srcML/releases/download/v1.0.0/srcml_1.0.0-1_ubuntu18.04.deb && \
    apt-get update && \
    apt-get install -y ./srcml_1.0.0-1_ubuntu18.04.deb && \
    rm srcml_1.0.0-1_ubuntu18.04.deb

    
WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY tools tools
RUN chmod +x tools/RefactoringMiner-2.0/bin/RefactoringMiner

COPY szz szz
COPY options.py .
COPY main.py .

ENTRYPOINT [ "python", "-u", "main.py" ]