# basket.games

```
# alpine-3.18-default_20230607_amd64.tar.xz
```
## PART 1
```
# Upgrade and update Alpine's system packages
apk upgrade

apk update

# Install basic tools and Python
apk add --no-cache \
    nano \
    python3 \
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

# /opt/games
mkdir /opt/games

# Create directory and handle errors
mkdir -p /opt/games || { echo "Failed to create /opt/games"; exit 1; }

# Create user for gunicorn
adduser gunicornuser
```
## PART 2
```
addgroup gunicornuser www-data

# Change ownership with error handling
chown -R gunicornuser:www-data /opt/games || { echo "Failed to change ownership"; exit 1; }
chmod -R 750 /opt/games || { echo "Failed to set permissions"; exit 1; }  # Owner can read, write, execute; group can read and execute

# Install virtualenv if it's not already installed
pip3 install virtualenv

# Create a virtual environment in a directory named `venv`
python3 -m venv /opt/games/venv

# Activate the virtual environment
source  /opt/games/venv/bin/activate

# Now install required Python packages inside the virtual environment
pip3 install weasyprint requests cairocffi flask gunicorn

# Re-upgrade pip if necessary
pip install --upgrade pip

# /opt/games
cd /opt/games

# Create the `templates` directory where HTML templates will be stored
mkdir templates

# Open files for editing using nano (Flask app, shared functions, and templates)
nano shared_functions.py app.py templates/index.html templates/result.html
```
## PART 3 
```
# Logging directory
mkdir -p /var/log/gunicorn || { echo "Failed to create logging directory"; exit 1; }
chown gunicornuser:gunicornuser /var/log/gunicorn || { echo "Failed to change logging directory ownership"; exit 1; }

nano /etc/init.d/gunicorn

```
## PART 4
```
chmod +x /etc/init.d/gunicorn

rc-update add gunicorn default

rc-service gunicorn start

rc-service gunicorn status
```