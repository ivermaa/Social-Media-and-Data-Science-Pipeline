## Pull and Run Docker container for Postgresql

docker pull timescale/timescaledb-ha:pg16
docker run -d --name timescaledb -p 5432:5432 -e POSTGRES_PASSWORD=testpassword timescale/timescaledb-ha:pg16

Database used: postgres
DATABASE_URL='postgres://postgres:testpassword@localhost:5432/postgres'

## Pull and Run Docker container for Faktory

Install from docker: `docker pull contribsys/faktory`

```
docker run -it --name faktory \
  -v ~/projects/docker-disks/faktory-data:/var/lib/faktory/db \
  -e "FAKTORY_PASSWORD=password" \
  -p 127.0.0.1:7419:7419 \
  -p 127.0.0.1:7420:7420 \
  contribsys/faktory:latest \
  /faktory -b :7419 -w :7420
```

After the containers are installed


## Setup required tables and Schema before the script initilization

cmd: sudo docker exec -i timescaledb psql -U postgres < <project_path>/script.sql

# CREATE virtual env in env folder

cmd: python3 -m venv env/

Activate the env by source env/bin/activate to install requirements

# Install all Required libraries: pip install -r requirements.txt

You dont need to activate the virtual env again whenever you log in to the server again as the 'run_crawler.sh' script activates it when called. 

# Edit .cfg file

The .cfg file is used for dynamic configurations of URLs, 4chan boards, Subreddits and other server configurations

# Finally you run ./run_crawler.sh <proj_dir_name> to run continuous polling of my Data collection System






