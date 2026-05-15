## 1. Infrastructure Update
- [x] 1.1 Update `docker-compose.yml` to add `SITE_DOMAIN`, `SITE_SCHEME`, `SITE_NAME`, and `DEBUG` to the `celery_worker` service.
- [x] 1.2 Update `docker-compose.yml` to add `SITE_DOMAIN`, `SITE_SCHEME`, `SITE_NAME`, and `DEBUG` to the `celery_beat` service.

## 2. Verification
- [x] 2.1 Verify that `docker-compose.yml` has consistent environment variables across `web`, `celery_worker`, and `celery_beat`.
