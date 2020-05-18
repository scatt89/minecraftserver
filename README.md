# Minecraft server
My experiments with Ansible creating a Minecraft server.
This playbook automates an entire the installation and configuration of a Minecraft server over Raspbian or debian OS.
This is currently working on a Raspberry pi 4 with Raspbian Buster Lite.

## Previous requirements
- Install Ansible on your host
- Install Raspbian or Debian on your Raspberry
- Have a Hamachi or a Zerotier network in case you choose run play through a vpn network
- Have google drive api keys if you want backups allowed

## How to use
### Adjust the file vars.yml on your needs
Your can leave everything in this file by default but I will explain some variables (others are self explanatory).

- google_drive_backup_max_uploaded: Number of backups at the same time
- google_drive_backup_scope: Scope url of google drive api with the permissions to allow google drive access
- java_home: Java home path
- java_bin: Java bin path
- java_minecraft_server_xmx: Xmx JVM memory for the Minecraft server
- java_minecraft_server_xms: Xms JVM memory for the Minecraft server
- vpn_tool_choosed: Actually you can choose between hamachi and zerotier values depending of your vpn client
- system_timezone: Current time zone. This is important to the run the backup scrips
- home_user: Current user path

### Modify the .keys.yml file with your passwords and api keys
Most of these values are not optionals. You should place your own credentials in order to run this playbook successfully.

- rcon_password: rcon password
- hamachi_network_id: Hamachi network id (non necessary if your choose Zerotier as vpn client)
- hamachi_network_pass: Password of the Hamachi network (non necessary if your choose Zerotier as vpn client)
- zerotier_network_id: Zerotier network id (non necessary if your choose Hamachi as vpn client)
- ansible_user: The user that you want to make the ssh connection
- google_drive_client_id: Google api client id
- google_drive_project_id: Google api project id
- google_drive_client_secret: Google drive client id
- google_drive_backup_folder_id: google drive backup folder id

Run `ansible-playbook playbook.yml`
Its a good idea, once you place all your secret keys, encrypt the .keys.yml file and run ansible with this file encrypted:
```

```
