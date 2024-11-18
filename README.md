# basket.games

## PART 1
```
### Install besket.games on alpine

CONTAINER_ID=184
CONTAINER_NAME='basket.games'
$CONTAINER_PWD=
IP_ADDRESS=192.168.0.84
GW_ADDRESS=192.168.0.1

# Stop & destroy LXC container if needed
pct stop $CONTAINER_ID && pct destroy $CONTAINER_ID

# Create LXC container Munki
pct create $CONTAINER_ID /var/lib/vz/template/cache/alpine-3.18-default_20230607_amd64.tar.xz \
  --hostname $CONTAINER_NAME \
  --password $CONTAINER_PWD \
  --ostype alpine \
  --arch amd64 \
  --unprivileged 1 \
  --storage local-lvm \
  --cores 1 \
  --memory 1024 \
  --swap 0 \
  --net0 name=eth0,bridge=vmbr0,ip=$IP_ADDRESS/24,gw=$GW_ADDRESS \
  --rootfs local-lvm:64

# Start LXC container
pct start $CONTAINER_ID

# PART I 
lxc-attach -n $CONTAINER_ID -- sh -c "
# Upgrade and update Alpine's system packages
apk upgrade

apk update

# Install basic tools and Python
apk add --no-cache \
    nano \
    curl \
    python3 \
    openssl \
    py3-pip

# Install build tools and libraries required for WeasyPrint and Flask
apk add --no-cache \
    build-base \
    libc-dev \
    libffi-dev \
    libxml2-dev \
    libxslt-dev \
    cairo \
    cairo-dev \
    gdk-pixbuf-dev \
    glib-dev \
    gobject-introspection-dev \
    pango-dev \
    py3-cairocffi \
    py3-lxml \
    fontconfig \
    ttf-dejavu

apk add \
    build-base \
    libc-dev \
    libffi-dev \
    libxml2-dev \
    libxslt-dev \
    cairo \
    cairo-dev \
    gdk-pixbuf-dev \
    glib \
    glib-dev \
    gobject-introspection \
    gobject-introspection-dev \
    pango-dev \
    py3-cairocffi \
    py3-lxml \
    fontconfig \
    ttf-dejavu

# Upgrade system packages again just to ensure they are up-to-date
apk upgrade
apk update

# Upgrade pip to the latest version
pip install --upgrade pip

# Create directory and handle errors
mkdir -p /opt/games || { echo \"Failed to create /opt/games\"; exit 1; }

# Create user for gunicorn
adduser gunicornuser
"
```
## PART 2
```
lxc-attach -n $CONTAINER_ID -- sh -c "
addgroup gunicornuser www-data

# Change ownership with error handling
chown -R gunicornuser:www-data /opt/games || { echo \"Failed to change ownership\"; exit 1; }
chmod -R 750 /opt/games || { echo \"Failed to set permissions\"; exit 1; }  # Owner can read, write, execute; group can read and execute

# Install virtualenv if it's not already installed
pip3 install virtualenv

# Create a virtual environment in a directory named venv
python3 -m venv /opt/games/venv

# Activate the virtual environment
source  /opt/games/venv/bin/activate

# Now install required Python packages inside the virtual environment
pip3 install weasyprint requests cairocffi flask gunicorn

# Re-upgrade pip if necessary
pip install --upgrade pip

# Create the templates directory where HTML templates will be stored
mkdir /opt/games/templates

curl -o /opt/games/app.py https://raw.githubusercontent.com/dieteroo/basket.games/refs/heads/main/opt/games/app.py
curl -o /opt/games/shared_functions.py https://raw.githubusercontent.com/dieteroo/basket.games/refs/heads/main/opt/games/shared_functions.py

curl -o /opt/games/templates/index.html https://raw.githubusercontent.com/dieteroo/basket.games/refs/heads/main/opt/games/templates/index.html
curl -o /opt/games/templates/result.html https://raw.githubusercontent.com/dieteroo/basket.games/refs/heads/main/opt/games/templates/result.html

# Logging directory
mkdir -p /var/log/gunicorn || { echo \"Failed to create logging directory\"; exit 1; }
chown gunicornuser:gunicornuser /var/log/gunicorn || { echo \"Failed to change logging directory ownership\"; exit 1; }

# Create init.d file
curl -o /etc/init.d/gunicorn https://raw.githubusercontent.com/dieteroo/basket.games/refs/heads/main/etc/init.d/gunicorn

chmod +x /etc/init.d/gunicorn

rc-update add gunicorn default

rc-service gunicorn start

rc-service gunicorn status
"
```
