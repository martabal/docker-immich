# How to migrate

> [!IMPORTANT]  
> Pre-read all these steps before doing anying, if you are confused open an issue

## Migrate from docker-compose

### 1. Move the database

Install `PostgreSQL_Immich` from the Unraid CA and remove these variables from the template: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`.
The database is already initialised and these variables don't do anything.
Change the `Database Storage Path` to match the `DB_DATA_LOCATION` value

### 2. Setup the `martabal/immich` container

If you use unraid, instal the unraid CA for <https://github.com/martabal/unraid-templates/blob/main/templates/immich.xml>

> [!WARNING]  
> You must configure the template to the values listed in the docker-compose .env

Ensure that the template matches the `DB_USERNAME`, `DB_PASSWORD`, `DB_DATABASE_NAME` from the .env.

#### If you have uploaded assets after migrating from the docker-compose

Add a new env `IMMICH_MEDIA_LOCATION` and set it to `/usr/src/app/upload`, then set `Path: /photos` to your previous `UPLOAD_LOCATION` path.

```yaml
services:
  immich:
    image: ghcr.io/martabal/immich:latest
    environment: ...
      - IMMICH_MEDIA_LOCATION=/usr/src/app/upload
    volumes:
      - path_to_appdata:/config
      - path_to_photos:/app/immich/server/upload
      - path_to_libraries:/libraries
```

#### If you didn't uploaded assets after migrating from the docker-compose

Add a new volume where the host path is the same as the one mounted to `/photos` and mount it to `/app/immich/server/upload`

```yaml
services:
  immich:
    image: ghcr.io/martabal/immich:latest
    ...
    volumes:
      - path_to_appdata:/config
      - path_to_photos:/photos
      - path_to_libraries:/libraries
      - path_to_photos:/app/immich/server/upload
```

## Migrate to docker-compose

### 1. Setup

Install the official containers following the official guide [here](https://immich.app/docs/developer/setup/)

### 2. Edit the `.env`

Edit the `DB_USERNAME` and `DB_DATABASE_NAME` environment variables to match the one you had with the `martabal/immich` container:

Change `DB_DATA_LOCATION` and `UPLOAD_LOCATION` to match the previous host volumes:

- `path_to_postgres` &rarr; `DB_DATA_LOCATION`
- `path_to_photos` &rarr; `UPLOAD_LOCATION`

#### If you have not uploaded assets after migrating to the docker-compose

Add a new env `IMMICH_MEDIA_LOCATION=/photos` to your `.env` and replace the volume from `- ${UPLOAD_LOCATION}:/usr/src/app/upload` to `- ${UPLOAD_LOCATION}:/photos`

#### If you have uploaded assets after migrating to the docker-compose

Add a new volume to the immich-server container `${UPLOAD_LOCATION}:/photos`

```yaml
services:
  immich-server:
    ...
    volumes:
      - ${UPLOAD_LOCATION}:/usr/src/app/upload
      - /etc/localtime:/etc/localtime:ro
      - ${UPLOAD_LOCATION}:/photos
```

Everything _should_ be as it was.
