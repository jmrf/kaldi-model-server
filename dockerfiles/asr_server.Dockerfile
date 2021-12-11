FROM jmrf/pykaldi:2-py38


WORKDIR /app

# Install python deps
COPY requirements.txt ./
RUN pip3 install -r requirements.txt

# Copy the repo code
COPY kserver ./kserver

# CMD [ "python", "-m", "kserver.run", "-m", "12" ]
VOLUME ["/app/models"]
CMD [ "python3", "-m", "kserver.run", "-l" ]
