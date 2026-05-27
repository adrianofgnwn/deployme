# DeployMe frontend image — pinned base, runs as the built-in non-root `node` user.
FROM node:20-alpine

WORKDIR /app

# Install dependencies from the lockfile first for reproducible, cached builds.
COPY package.json package-lock.json* ./
RUN npm ci || npm install

# Copy the rest of the source and hand ownership to the unprivileged user.
COPY . .
RUN chown -R node:node /app

USER node

EXPOSE 5173

# --host makes Vite listen on 0.0.0.0 so the container is reachable.
CMD ["npm", "run", "dev", "--", "--host"]
