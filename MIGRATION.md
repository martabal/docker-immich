# Unraid: Migrate from docker-compose

> [!IMPORTANT]  
> Pre-read all these steps before doing anying, if you are confused open an issue

When using the official Immich docker-compose, the PostgreSQL data is stored in a docker volume which _should_ be located at `/var/lib/docker/volumes/pgdata/_data`. Before preceeding you **must** stop the docker-compose stack.

## 1. Move the database

Install `PostgreSQL_Immich` from the Unraid CA and remove these variables from the template: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`.
The database is already initialised and these variables don't do anything.
Also set `Database Storage Path` to `/mnt/user/appdata/PostgreSQL_Immich`.

## 2. Setup the `martabal/immich` container

Instal the unraid CA for <https://github.com/martabal/unraid-templates/blob/main/templates/immich.xml>

> [!WARNING]  
> You must configure the template to the values listed in the docker-compose .env

Ensure that the template matches the `DB_USERNAME`, `DB_PASSWORD`, `DB_DATABASE_NAME` from the .env. Add a new env `IMMICH_MEDIA_LOCATION` and set it to `/usr/src/app/upload`, then set `Path: /photos` to your previous `UPLOAD_LOCATION` path.

Click Apply, Open the WebUI and login. Everything _Should_ be as it was.
