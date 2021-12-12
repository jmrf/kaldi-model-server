FROM jmrf/pykaldi:2-py38


WORKDIR /app

# Install python deps
COPY requirements.txt ./
RUN pip3 install -r requirements.txt

# Copy the repo code
COPY kserver ./kserver

VOLUME ["/app/models"]
VOLUME ["/app/conf"]
# CMD [ "python3", "-m", "kserver.run", "-l" ]
CMD [ "python", "-m", "kserver.run", "-m", "12" ]
