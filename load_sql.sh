#!/bin/bash
docker exec data-center-db psql -U postgres -d datacenter -f /prepare.sql