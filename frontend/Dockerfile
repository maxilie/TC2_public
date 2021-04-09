### Stage 1: build angular ###

FROM node:11.4.0-alpine as builder

# Set working directory
RUN mkdir /app
WORKDIR /app

# Copy over app dependencies list
COPY angular-app/package.json angular-app/package-lock.json /app/angular-app/

# Install app dependencies
RUN npm install --prefix angular-app
RUN npm install -s jwt-decode
RUN npm install -s @types/jwt-decode
RUN npm install --save jquery
RUN npm install -D @types/jquery
RUN npm install i @types/jquery
RUN npm install @types/d3@4.11.0 --save
RUN npm install d3@4.11.0 --save
RUN npm install d3-selection --save
RUN npm install @types/d3-selection --save

# Copy over app files
COPY . /app

# Build app
RUN npm run build --prefix angular-app -- --output-path=./dist/out


### Stage 2: deploy on nginx ###

FROM nginx:1.15.7-alpine

# Expose the nginx/angular port for the frontend container
EXPOSE 9100

# Remove html files for default nginx website
RUN rm -rf /usr/share/nginx/html/*

# Use html files for our angular website (from Stage 1)
COPY --from=builder /app/angular-app/dist/out /usr/share/nginx/html

# Copy over static files (icons, scripts, etc.)
COPY ./django-static-files/ /usr/share/nginx/html/staticfiles
RUN ls /usr/share/nginx/html
RUN ls /usr/share/nginx/html/staticfiles

# Use our nginx config file
COPY ./nginx/nginx.conf /etc/nginx/conf.d/default.conf
