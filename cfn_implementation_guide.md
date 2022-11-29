
# Run project using CloudFormation

* In CloudFormation, upload `cloudformation.yaml` file an create a new stack

Once the creation is complete:

* From the local machine, connect via SSH to the EC2 instance (Bastion host)
* From the bastion host, connect via SSH to principal server in private subnet (ServerInstance)
* Clone this repo
* Config ~/.aws/credentials
* Create a new virtual environment and install requirements.txt


        mkdir /home/ec2-user/venv
        python3 -m venv venv
        source venv/bin/activate
        pip3 install -r <cloned-repo-name>/airflow_spark/src/app/requirements.txt

* Create a MySQL RDS and change endpoint and connections in <cloned-repo-name>/airflow_spark/src/app/dbconnect.py
* Config all app files and services:

`sudo nano /etc/systemd/system/app.service`

        [Unit]
        Description=Gunicorn instance for Flask app
        After=network.target

        [Service]
        User=ec2-user
        Group=ec2-user
        WorkingDirectory=/home/ec2-user/itba-cde-final/airflow_spark/src/app
        ExecStart=/home/ec2-user/venv/bin/gunicorn -b localhost:5000 app:app
        Restart=always

        [Install]
        WantedBy=multi-user.target

`sudo nano /etc/systemd/system/gunicorn.service`

        [Unit]
        Description=gunicorn daemon
        #Requires=gunircorn.socket
        After=network.target

        [Service]
        User=ec2-user
        Group=ec2-user
        WorkingDirectory=/home/ec2-user/itba-cde-final/airflow_spark/src/app
        ExecStart=/home/ec2-user/venv/bin/gunicorn --access-logfile - --workers 3 --bind localhost:5000 app:app

        [Install]
        WantedBy=multi-user.target
        ' > gunicorn.service

`sudo nano /etc/nginx/nginx.conf`

        # For more information on configuration, see:
        #   * Official English Documentation: http://nginx.org/en/docs/
        #   * Official Russian Documentation: http://nginx.org/ru/docs/

        user nginx;
        worker_processes auto;
        error_log /var/log/nginx/error.log;
        pid /run/nginx.pid;

        # Load dynamic modules. See /usr/share/doc/nginx/README.dynamic.
        include /usr/share/nginx/modules/*.conf;

        events {
            worker_connections 1024;
        }

        http {
            log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                            '$status $body_bytes_sent "$http_referer" '
                            '"$http_user_agent" "$http_x_forwarded_for"';

            access_log  /var/log/nginx/access.log  main;

            sendfile            on;
            tcp_nopush          on;
            tcp_nodelay         on;
            keepalive_timeout   65;
            types_hash_max_size 4096;

            include             /etc/nginx/mime.types;
            default_type        application/octet-stream;

            # Load modular configuration files from the /etc/nginx/conf.d directory.
            # See http://nginx.org/en/docs/ngx_core_module.html#include
            # for more information.
            include /etc/nginx/conf.d/*.conf;

            server {
                listen       80;
                listen       [::]:80;
                server_name  _;

                location / {
                proxy_pass http://127.0.0.1:5000;
                }
            }

        # Settings for a TLS enabled server.
        #
        #    server {
        #        listen       443 ssl http2;
        #        listen       [::]:443 ssl http2;
        #        server_name  _;
        #        root         /usr/share/nginx/html;
        #
        #        ssl_certificate "/etc/pki/nginx/server.crt";
        #        ssl_certificate_key "/etc/pki/nginx/private/server.key";
        #        ssl_session_cache shared:SSL:1m;
        #        ssl_session_timeout  10m;
        #        ssl_ciphers PROFILE=SYSTEM;
        #        ssl_prefer_server_ciphers on;
        #
        #        # Load configuration files for the default server block.
        #        include /etc/nginx/default.d/*.conf;
        #
        #        error_page 404 /404.html;
        #            location = /40x.html {
        #        }
        #
        #        error_page 500 502 503 504 /50x.html;
        #            location = /50x.html {
        #        }
        #    }

        }

        cd

* Activate created services

        sudo systemctl enable nginx
        sudo systemctl enable app
        sudo systemctl enable gunicorn
        sudo systemctl daemon-reload
        sudo systemctl start gunicorn
        sudo systemctl start nginx
        sudo systemctl start app
        sudo systemctl status gunicorn
        sudo systemctl status nginx
        sudo systemctl status app

* Config Airflow server

            cd airflow_spark
            # Set user
            echo -e "AIRFLOW_UID=$(id -u)\nAIRFLOW_GID=0" > .env
            echo -e "AWS_ACCESS_KEY_ID=$(aws configure get aws_access_key_id --profile default)`
            `\nAWS_SECRET_ACCESS_KEY=$(aws configure get aws_secret_access_key_id --profile default)`
            `\nAWS_SESSION_TOKEN=$(aws configure get aws_session_token --profile default)`
            `\nAWS_DEFAULT_REGION=$(aws configure get aws_default_region --profile default)" >> .env

            # Init airflow db metadata
            docker-compose up airflow-init
            # Run airflow
            docker-compose up -d

* Create an AMI of the ready-to-use EC2
* Use that AMI's Id as a parameter in CloudFormation's second script 
* In CloudFormation, upload `elb-asg.yaml` file an create a new stack using the running services Ids as the requested parameters