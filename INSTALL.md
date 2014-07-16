# Install Guide



## Prerequisities

    virtualenv .env
    source .env/bin/activate
    pip install -r requirements.txt


## Nginx Reverse Proxy


    server {

            listen 127.0.0.1;
            server_name api.pgxn-tester.org;

            access_log /var/log/nginx/api.access_log main;
            error_log /var/log/nginx/api.error_log info;

            location / {
                    proxy_pass http://127.0.0.1:5000;
            }

    }

    server {

            listen 127.0.0.1;
            server_name pgxn-tester.org;

            access_log /var/log/nginx/web.access_log main;
            error_log /var/log/nginx/web.error_log info;

            location / {
                    proxy_pass http://127.0.0.1:6000;
            }

    }