# Use the official Python 3.11 image as the base image
FROM python:3.11

# Set the working directory
WORKDIR /usr/src/app

# Update the apt package list and install system dependencies
RUN apt-get update && \
    apt-get install -y \
    curl \
    python3-gi \
    python3-gi-cairo \
    python3-debian \
    gir1.2-gtk-3.0 \
    gir1.2-webkit2-4.1 \
    libgl1-mesa-glx \
    qt5-qmake \
    qtbase5-dev \
    build-essential \
    python3-pyqt5 \
    gobject-introspection \
    pkg-config \
    cmake \
    libffi-dev \
    libgirepository1.0-dev \
    libxkbcommon-x11-0 && \
    apt-get clean

ENV NVM_DIR /root/.nvm
ENV NODE_VERSION 20

RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash \
    && . "$NVM_DIR/nvm.sh" \
    && nvm install $NODE_VERSION \
    && nvm use $NODE_VERSION \
    && nvm alias default $NODE_VERSION

ENV PATH $NVM_DIR/versions/node/v$NODE_VERSION/bin:$PATH


# Install Python dependencies via pip
RUN pip install pywui pywui_cli

#RUN pip install pywebview[qt]

# Copy the application files into the container
COPY . .

# Set the default command to run your application
#CMD ["pywui", "pack"]

# Keep the container running to maintain the session open
CMD tail -f /dev/null



