FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies
# Use `npm install` here because `npm ci` requires a package-lock.json to be present
# If you prefer `npm ci` for reproducible installs, add a `package-lock.json` to the repo.
COPY package*.json ./
RUN npm install

# Copy source and build
COPY . .
RUN npm run build

FROM nginx:stable-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
