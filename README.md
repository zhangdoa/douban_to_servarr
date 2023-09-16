# Overview
An automated scraper tool to send entries from your [Douban](https://www.douban.com/) lists to [Servarr](https://wiki.servarr.com/) servers.

# Requirements
- Properly configured [Sonarr](https://sonarr.tv/), [Radarr](https://radarr.video/) and [Lidarr](https://lidarr.audio/) servers.
- A Douban user account, of which you must possess full legal rights before running this script with it. Any violation of the EULA of Douban is not the responsibility of the project.

# How to use
## Configuration
1. Copy `user_config_template.yml` to `user_config.yml` and set all the options to the actual values from your environment.
2. Run the script.

## Launch
### In Visual Studio Code
- Open the workspace folder and launch with your launching option.

### In Docker
1. Build the Docker image by `docker build -t douban_to_servarr . -f Dockerfile --platform linux/amd64`.
2. Start the container with either docker-compose (recommended):
   ```
    version: "2.1"
    services:
    douban_to_servarr:
        container_name: douban_to_servarr
        network_mode: 'host'
        environment:
        - PUID=1000
        - PGID=1000
        - TZ=Etc/UTC
   ```
3. Or start with docker-cli:
    ```
    docker run -d \
    --name=douban_to_servarr \
    -e PUID=1000 \
    -e PGID=1000 \
    --network="host" \
    -e TZ=Etc/UTC \
    docker.io/library/douban_to_servarr
    ```
# Trouble shooting: 
- Check the log file and see if there are any warnings or errors. 
- Check your Servarr configurations.