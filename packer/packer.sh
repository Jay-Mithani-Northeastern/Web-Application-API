#!/bin/sh

sudo yum -y update
sudo yum -y upgrade
sudo yum -y clean all

sudo yum install -y postgresql postgresql-server

sudo postgresql-setup initdb

sudo systemctl start postgresql
sudo systemctl enable postgresql
sudo systemctl status postgresql

sudo -i -u postgres psql -c "CREATE DATABASE webapp;"


sudo yum update -y
sudo yum groupinstall "Development Tools" -y
sudo yum erase openssl-devel -y
sudo yum install openssl11 openssl11-devel  libffi-devel bzip2-devel wget -y
wget https://www.python.org/ftp/python/3.10.4/Python-3.10.4.tgz
tar -xf Python-3.10.4.tgz
cd Python-3.10.4/ || ./configure --enable-optimizations
sudo make altinstall
sudo yum install python3-pip -y

sudo yum install zip

sudo mkdir /home/webapp
sudo unzip /tmp/app.zip -d /home/webapp/

sudo cp /home/webapp/packer/webapp.service /lib/systemd/system
export DATABASE_URL="postgresql://postgres:admin@localhost/webapp"
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'admin'";
sudo sed -i 's/ident/md5/' /var/lib/pgsql/data/pg_hba.conf
sudo systemctl restart postgresql


pip3 install -r /home/webapp/requirements.txt

sudo systemctl daemon-reload
sudo systemctl start webapp.service
sudo systemctl enable webapp.service





