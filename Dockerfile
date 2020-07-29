FROM pymesh/pymesh:py3.6-slim

WORKDIR /krak

# install vtk seperately so no need to redownload on rebuild
RUN python -m pip install vtk


RUN apt-get update && apt -y install libstdc++6 python-qt4 libgl1-mesa-glx

# Temporary
RUN echo "deb http://ftp.us.debian.org/debian testing main contrib non-free" >> /etc/apt/sources.list.d/testing.list
RUN apt-get update && apt -y install libstdc++6 
COPY requirements.txt /krak/requirements.txt

RUN python -m pip install -r requirements.txt

COPY setup.py /krak/setup.py
COPY krak/* /krak/krak/

# TEMP
COPY examples/* /krak/examples/

RUN python -m pip install -e .
