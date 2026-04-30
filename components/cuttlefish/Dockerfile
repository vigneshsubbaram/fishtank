# syntax=docker/dockerfile:1

FROM golang:1.23 AS fetch-artifact-builder
RUN git clone https://android.googlesource.com/tools/fetch_artifact /src/fetch_artifact
WORKDIR /src/fetch_artifact
RUN go build -o /usr/local/bin/fetch_artifact .

FROM us-docker.pkg.dev/android-cuttlefish-artifacts/cuttlefish-orchestration/cuttlefish-orchestration:stable AS cuttlefish-with-image

COPY --from=fetch-artifact-builder /usr/local/bin/fetch_artifact /usr/local/bin/fetch_artifact

ARG BUILD_ID
ARG ARCH=x86_64
ARG BRANCH=aosp-android13-gsi
ARG TARGET_x86_64=aosp_cf_x86_64_only_phone-userdebug
ARG TARGET_arm64=aosp_cf_arm64_only_phone-userdebug

WORKDIR /opt/cuttlefish-android

RUN apt-get update && apt-get install -y --no-install-recommends \
    unzip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    if [ "$ARCH" = "arm64" ]; then \
        TARGET="$TARGET_arm64"; \
        IMG_PREFIX="aosp_cf_arm64_only_phone"; \
    else \
        TARGET="$TARGET_x86_64"; \
        IMG_PREFIX="aosp_cf_x86_64_only_phone"; \
    fi; \
    \
    # Resolve fetch mode: pin to BUILD_ID if provided, else use BRANCH \
    if [ -n "${BUILD_ID:-}" ]; then \
        BUILD_FLAG="-build_id=${BUILD_ID}"; \
        IMG_ZIP="${IMG_PREFIX}-img-${BUILD_ID}.zip"; \
    else \
        BUILD_FLAG="-branch=${BRANCH}"; \
        IMG_ZIP="${IMG_PREFIX}-img.zip"; \
    fi; \
    \
    echo "Fetching host package (target=${TARGET}, ${BUILD_FLAG})..."; \
    fetch_artifact \
        -target="${TARGET}" \
        ${BUILD_FLAG} \
        -artifact=cvd-host_package.tar.gz \
        -output=cvd-host_package.tar.gz; \
    \
    echo "Fetching device image (${IMG_ZIP})..."; \
    fetch_artifact \
        -target="${TARGET}" \
        ${BUILD_FLAG} \
        -artifact="${IMG_ZIP}" \
        -output=device-img.zip; \
    \
    echo "Extracting artifacts..."; \
    tar -xvf cvd-host_package.tar.gz; \
    unzip device-img.zip; \
    \
    echo "Cleaning up archives..."; \
    rm cvd-host_package.tar.gz device-img.zip

WORKDIR /opt/cuttlefish-android

ENV HOME=/opt/cuttlefish-android

COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
