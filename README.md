# Overview
An automated scraper tool to send entries from your [Douban](https://www.douban.com/) lists to [Servarr](https://wiki.servarr.com/) servers.

# Requirements
- Properly configured [Sonarr](https://sonarr.tv/), [Radarr](https://radarr.video/), and [Lidarr](https://lidarr.audio/) servers.
- A Douban user account, with full legal rights to access and manage the account.  
  **Note:** Any violation of Douban's EULA is solely the user's responsibility.

# How to Use

## Configuration
1. Copy `config_template.yml` to `config.yml` and update it with values specific to your environment.
2. Ensure `config.yml` is accessible to the script or container at runtime.

## Launch

### In Visual Studio Code
- Open the workspace folder in VSCode and launch the script using your preferred debug configuration.

### In Docker
1. **Build the Docker Image:**
   ```bash
   docker build -t douban_to_servarr . --platform linux/amd64
   ```
   *(Replace `linux/amd64` with a platform compatible with your environment.)*

2. **Run the Container with Docker Compose (Recommended):**
   ```yaml
   services:
     douban_to_servarr:
       image: douban_to_servarr
       container_name: douban_to_servarr
       network_mode: "host"
       environment:
        - PUID=1000  # Optional user ID for permissions
        - PGID=1000  # Optional group ID for permissions
        - TZ=Etc/UTC  # Set the time zone
        - DOWNLOAD_CRON=0 1,13 * * *  # Optional: Custom cron schedule
       volumes:
        - ./config.yml:/app/config.yml  # Map your local config file
        - ./logs:/app/logs  # The log files directory
   ```

3. **Run the Container with Docker CLI:**
   ```bash
   docker run -d \
     --name=douban_to_servarr \
     -e PUID=1000 \
     -e PGID=1000 \
     -e TZ=Etc/UTC \
     -e DOWNLOAD_CRON="0 1,13 * * *" \
     --network="host" \
     -v $(pwd)/config.yml:/app/config.yml \
     douban_to_servarr
   ```

## Verify Cron Schedule
If you override the `DOWNLOAD_CRON` schedule, ensure it is formatted correctly. The default schedule runs every two hours.

# Troubleshooting
- **Logs:** Check the log file (`/var/log/cron.log` inside the container or mapped location) for warnings or errors.
- **Servarr Configuration:** Ensure your Sonarr, Radarr, or Lidarr servers are correctly configured and accessible from the script/container.
- **Environment Variables:** Verify that required variables like `DOWNLOAD_CRON` and `TZ` are set properly.
- **File Paths:** Ensure `config.yml` is correctly mapped to `/app/config.yml` in the container.
