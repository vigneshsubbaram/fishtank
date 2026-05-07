FROM golang:1.23 AS fetch-artifact-builder
RUN git clone https://android.googlesource.com/tools/fetch_artifact /src/fetch_artifact
WORKDIR /src/fetch_artifact
RUN go build -o /usr/local/bin/fetch_artifact .

FROM ota-base:container_utils_1.1.1 AS ota-server

COPY --from=fetch-artifact-builder /usr/local/bin/fetch_artifact /usr/local/bin/fetch_artifact
COPY resources/parse_ota_metadata.py /usr/local/bin/parse_ota_metadata.py
