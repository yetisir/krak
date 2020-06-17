FROM pymesh/pymesh:py3.6-slim

WORKDIR /krak

# install vtk seperately so no need to redownload on rebuild
RUN python -m pip install vtk

COPY requirements.txt /krak/requirements.txt
RUN python -m pip install -r requirements.txt

COPY setup.py /krak/setup.py
COPY krak/* /krak/krak/
RUN python -m pip install .