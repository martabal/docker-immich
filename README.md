# [martabal/immich](https://github.com/martabal/docker-immich)

[![Docker build](https://github.com/martabal/docker-immich/actions/workflows/docker.yml/badge.svg)](https://github.com/martabal/docker-immich/actions/workflows/docker.yml)
[![Test suites](https://github.com/martabal/docker-immich/actions/workflows/test.yml/badge.svg)](https://github.com/martabal/docker-immich/actions/workflows/test.yml)
[![Check for new version](https://github.com/martabal/docker-immich/actions/workflows/external-trigger.yml/badge.svg)](https://github.com/martabal/docker-immich/actions/workflows/external-trigger.yml)

[Immich](https://immich.app/) is a high performance self-hosted photo and video backup solution.

[![immich](./immich-logo.png)](https://immich.app/)

## What is it ?

This repo is a fork of the official [AIO image for Immich](https://github.com/imagegenius/docker-immich). Its main goal is to provide docker images with pre-installed machine learning support for CUDA and openvino.

## Supported Architectures

This image supports the following architectures:

| Architecture | Available |
| :----------: | :-------: |
|    x86-64    |    ✅     |
|    arm64     |    ✅     |
|    armhf     |    ❌     |

## Version Tags

This image offers different versions via tags. Be cautious when using unstable or development tags, and read their descriptions carefully.

|   Tag    | Available | Description                                                                                                                               |
| :------: | :-------: | ----------------------------------------------------------------------------------------------------------------------------------------- |
|  latest  |    ✅     | Latest Immich release with an Ubuntu base.                                                                                                |
| openvino |    ✅     | Latest Immich release with an Ubuntu base and support for openvino for machine-learning acceleration.                                     |
|   cuda   |    ✅     | Latest Immich release with an Ubuntu base and support for cuda for machine-learning acceleration.                                         |
|   noml   |    ✅     | Latest Immich release with an Ubuntu base. Machine-learning is completely removed, making it still compatible with hardware accelaration. |

## Application Setup

The WebUI can be accessed at `http://your-ip:8080` Follow the wizard to set up Immich.

To use Immich, you need to have PostgreSQL 14/15/16 server with [pgvecto.rs](https://github.com/tensorchord/pgvecto.rs) set up externally, and Redis set up externally or within the container using a docker mod.

To use a SSL connection to your PostgreSQL database, include a PostgreSQL URL in the `DB_URL` environment variable.

## Hardware Acceleration for videos

### Intel - QSV/VAAPI

To use Intel Quicksync hardware acceleration:

1. Ensure your container has access to the `/dev/dri` video device.
2. Add the device to your container by including the following option in your Docker run command:

```bash
docker run --device=/dev/dri:/dev/dri ...
```

### Nvidia - NVENC/VAAPI

To use Nvidia hardware acceleration:

1. First, install the Nvidia container runtime on your host machine. Follow the [installation instructions here](<https://github.com/NVIDIA/> nvidia-docker).

2. After installing `nvidia-docker2`, recreate or create a new Docker container using the Nvidia runtime. This can be done in two ways:

- Add both `--runtime=nvidia` and `NVIDIA_VISIBLE_DEVICES=all` to your Docker run command. Replace `all` with a specific GPU's UUID if needed. Example:

```bash
docker run --runtime=nvidia -e NVIDIA_VISIBLE_DEVICES=all
```

- Alternatively, use `--gpus=all` in your Docker run command. Example:

```bash
docker run --gpus=all ...
```

### Machine-learning acceleration

#### Intel - OpenVINO

To use OpenVINO:

1. Make sure your [CPU supports OpenVINO](https://docs.openvino.ai/2024/about-openvino/system-requirements.html)

2. Add a new path `-p /dev/bus/usb:/dev/bus/usb` and add `--device=/dev/dri --device-cgroup-rule='c 189:* rmw'` in your Docker run command. Example:

```bash
docker run --device=/dev/dri --device-cgroup-rule='c 189:* rmw' -p /dev/bus/usb:/dev/bus/usb ...
```

#### Nvidia - CUDA

For Nvidia GPUs with Nvidia/CUDA hardware acceleration, use the same commands used for video transcoding.

## Import your existing libraries into Immich

- Mount your existing library folder to `/import`
- In your administration settings, go to "External Libraries", add a library owner, and set the import paths starting (it must start with `/import`)

## Usage

Example snippets to start creating a container:

### Docker Compose

```yaml
---
version: "2.1"
services:
  immich:
    image: ghcr.io/martabal/immich:latest
    container_name: immich
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Etc/UTC
      - DB_HOSTNAME=192.168.1.x
      - DB_USERNAME=postgres
      - DB_PASSWORD=postgres
      - DB_DATABASE_NAME=immich
      - REDIS_HOSTNAME=192.168.1.x
      - DB_PORT=5432 #optional
      - REDIS_PORT=6379 #optional
      - REDIS_PASSWORD= #optional
      - MACHINE_LEARNING_WORKERS=1 #optional
      - MACHINE_LEARNING_WORKER_TIMEOUT=120 #optional
    volumes:
      - path_to_appdata:/config
      - path_to_photos:/photos
      - path_to_imports:/import:ro #optional
    ports:
      - 8080:8080
    restart: unless-stopped
  # This container requires an external application to be run separately to be run separately.
  # By default, ports for the databases are opened, be careful when deploying it
  # Redis:
  redis:
    image: redis
    ports:
      - 6379:6379
    container_name: redis
  # PostgreSQL 14:
  postgres14:
    image: tensorchord/pgvecto-rs:pg14-v0.2.0
    ports:
      - 5432:5432
    container_name: postgres14
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: immich
    volumes:
      - path_to_postgres:/var/lib/postgresql/data
```

### Docker CLI ([Click here for more info](https://docs.docker.com/engine/reference/commandline/cli/))

```bash
docker run -d \
  --name=immich \
  -e PUID=1000 \
  -e PGID=1000 \
  -e TZ=Etc/UTC \
  -e DB_HOSTNAME=192.168.1.x \
  -e DB_USERNAME=postgres \
  -e DB_PASSWORD=postgres \
  -e DB_DATABASE_NAME=immich \
  -e REDIS_HOSTNAME=192.168.1.x \
  -e DB_PORT=5432 `#optional` \
  -e REDIS_PORT=6379 `#optional` \
  -e REDIS_PASSWORD= `#optional` \
  -e MACHINE_LEARNING_WORKERS=1 `#optional` \
  -e MACHINE_LEARNING_WORKER_TIMEOUT=120 `#optional` \
  -p 8080:8080 \
  -v path_to_appdata:/config \
  -v path_to_photos:/photos \
  -v path_to_imports:/import:ro `#optional` \
  --restart unless-stopped \
  ghcr.io/martabal/immich:latest

# This container requires an external application to be run separately.
# By default, ports for the databases are opened, be careful when deploying it
# Redis:
docker run -d \
  --name=redis \
  -p 6379:6379 \
  redis

# PostgreSQL 14:
docker run -d \
  --name=postgres14 \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=immich \
  -v path_to_postgres:/var/lib/postgresql/data \
  -p 5432:5432 \
  tensorchord/pgvecto-rs:pg14-v0.2.0

```

## Variables

To configure the container, pass variables at runtime using the format `<external>:<internal>`. For instance, `-p 8080:80` exposes port `80` inside the container, making it accessible outside the container via the host's IP on port `8080`.

|                 Variable                 | Description                                                                                                    |
| :--------------------------------------: | -------------------------------------------------------------------------------------------------------------- |
|                `-p 8080`                 | WebUI Port                                                                                                     |
|              `-e PUID=1000`              | UID for permissions - see below for explanation                                                                |
|              `-e PGID=1000`              | GID for permissions - see below for explanation                                                                |
|             `-e TZ=Etc/UTC`              | Specify a timezone to use, see this [list](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List). |
|       `-e DB_HOSTNAME=192.168.1.x`       | PostgreSQL Host                                                                                                |
|        `-e DB_USERNAME=postgres`         | PostgreSQL Username                                                                                            |
|        `-e DB_PASSWORD=postgres`         | PostgreSQL Password                                                                                            |
|       `-e DB_DATABASE_NAME=immich`       | PostgreSQL Database Name                                                                                       |
|     `-e REDIS_HOSTNAME=192.168.1.x`      | Redis Hostname                                                                                                 |
|            `-e DB_PORT=5432`             | PostgreSQL Port                                                                                                |
|           `-e REDIS_PORT=6379`           | Redis Port                                                                                                     |
|           `-e REDIS_PASSWORD=`           | Redis password                                                                                                 |
|     `-e MACHINE_LEARNING_WORKERS=1`      | Machine learning workers                                                                                       |
| `-e MACHINE_LEARNING_WORKER_TIMEOUT=120` | Machine learning worker timeout                                                                                |
|               `-v /config`               | Contains machine learning models (~1.5GB with default models)                                                  |
|               `-v /photos`               | Contains all the photos uploaded to Immich                                                                     |
|             `-v /import:ro`              | This folder will be periodically scanned, contents will be automatically imported into Immich                  |

## Umask for running applications

The image allow overriding the default umask setting for services started within the containers using the optional -e UMASK=022 option. Note that umask works differently than chmod and subtracts permissions based on its value, not adding. For more information, please refer to the Wikipedia article on umask [here](https://en.wikipedia.org/wiki/Umask).

## User / Group Identifiers

To avoid permissions issues when using volumes (`-v` flags) between the host OS and the container, you can specify the user (`PUID`) and group (`PGID`). Make sure that the volume directories on the host are owned by the same user you specify, and the issues will disappear.

Example: `PUID=1000` and `PGID=1000`. To find your PUID and PGID, run `id user`.

```bash
  $ id username
    uid=1000(dockeruser) gid=1000(dockergroup) groups=1000(dockergroup)
```

## Updating the Container

Check the [Application Setup](#application-setup) section for recommendations for the specific image.

Instructions for updating the container:

### Via Docker Compose

- Update all images: `docker-compose pull` or update a single image: `docker-compose pull immich`
- Let compose update all containers as necessary: `docker-compose up -d` or update a single container: `docker-compose up -d immich`
- You can also remove the old dangling images: `docker image prune`

### Via Docker Run

- Update the image: `docker pull ghcr.io/martabal/immich:latest`
- Stop the running container: `docker stop immich`
- Delete the container: `docker rm immich`
- Recreate a new container with the same docker run parameters as instructed above (if mapped correctly to a host folder, your `/config` folder and settings will be preserved)
- You can also remove the old dangling images: `docker image prune`
