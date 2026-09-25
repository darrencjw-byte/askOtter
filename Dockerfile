# Build stage
FROM node:22-alpine AS builder

# Install openssl for Prisma and other native modules that need it
RUN apk add --no-cache openssl

WORKDIR /app

# Copy all files first to check project type
COPY . .

# Detect if this is a Node.js project or simple static HTML
RUN if [ -f package.json ]; then \
      echo "Node.js project detected (package.json found)"; \
      echo "nodejs" > .project-type; \
    else \
      echo "Simple static HTML project detected (no package.json)"; \
      echo "static-html" > .project-type; \
    fi

# Detect package manager from lockfile presence.
# Priority: pnpm-lock.yaml > yarn.lock > package-lock.json > npm (default)
RUN if [ -f pnpm-lock.yaml ]; then \
      echo "pnpm" > .package-manager; \
    elif [ -f yarn.lock ]; then \
      echo "yarn" > .package-manager; \
    else \
      echo "npm" > .package-manager; \
    fi && \
    echo "Package manager detected: $(cat .package-manager)"

# Activate corepack for pnpm/yarn; fall back to npm install -g pnpm on failure
RUN PM=$(cat .package-manager) && \
    if [ "$PM" = "pnpm" ] || [ "$PM" = "yarn" ]; then \
      corepack enable || { if [ "$PM" = "pnpm" ]; then npm install -g pnpm; fi; }; \
    fi

# Install dependencies only if package.json exists.
# pnpm/yarn: try --frozen-lockfile first, fall back to unfrozen on mismatch.
# npm: try npm ci first, fall back to npm install with --legacy-peer-deps.
RUN PM=$(cat .package-manager) && \
    if [ -f package.json ]; then \
      if [ "$PM" = "pnpm" ]; then \
        pnpm install --frozen-lockfile --ignore-scripts 2>/dev/null || { \
          echo "⚠️  pnpm lockfile out of sync, reinstalling..."; \
          pnpm install --ignore-scripts; \
        }; \
        pnpm rebuild 2>/dev/null || true; \
        if grep -q '"postinstall"' package.json; then pnpm run postinstall; fi; \
      elif [ "$PM" = "yarn" ]; then \
        yarn install --frozen-lockfile --ignore-scripts 2>/dev/null || { \
          echo "⚠️  yarn lockfile out of sync, reinstalling..."; \
          yarn install --ignore-scripts; \
        }; \
        yarn rebuild 2>/dev/null || true; \
        if grep -q '"postinstall"' package.json; then yarn run postinstall; fi; \
      else \
        if [ -f package-lock.json ]; then \
          npm ci --ignore-scripts 2>/dev/null || { \
            echo "⚠️  package-lock.json out of sync, regenerating with npm install..."; \
            rm -f package-lock.json; \
            npm install --ignore-scripts 2>/dev/null || npm install --legacy-peer-deps --ignore-scripts; \
          }; \
        else \
          npm install --ignore-scripts 2>/dev/null || npm install --legacy-peer-deps --ignore-scripts; \
        fi; \
        npm rebuild 2>/dev/null || true; \
        if grep -q '"postinstall"' package.json; then npm run postinstall; fi; \
      fi; \
    fi

# Remove stale build artifacts that may have been copied from source
RUN rm -rf .next dist build

# Build-time placeholder env vars for common auth/db libraries.
# During next build, route modules are imported for page data collection.
# Auth libraries (better-auth, Auth.js, NextAuth) crash if their URL/secret
# env vars are undefined. These placeholders prevent that.
# They are harmless for non-Next.js apps and are cleared in the production stage.
ENV BUILD_MODE=1
ENV BETTER_AUTH_URL=http://localhost:3000
ENV BETTER_AUTH_SECRET=build-placeholder
ENV AUTH_SECRET=build-placeholder
ENV AUTH_URL=http://localhost:3000
ENV AUTH_TRUST_HOST=true
ENV NEXTAUTH_SECRET=build-placeholder
ENV NEXTAUTH_URL=http://localhost:3000
ENV MONGODB_URI=mongodb://placeholder:27017/placeholder
ENV DATABASE_URL=postgresql://placeholder:placeholder@localhost:5432/placeholder
ENV SESSION_SECRET=build_time_placeholder_min_32_chars_long

# Resolve build root: checks root package.json, well-known subfolders, and workspaces.
# Writes the resolved path (relative, no trailing slash) to .build-root.
RUN has_build_script() { \
      grep -A200 '"scripts"' "$1" 2>/dev/null | grep -q '"build":'; \
    }; \
    has_start_script() { \
      grep -A200 '"scripts"' "$1" 2>/dev/null | grep -q '"start":'; \
    }; \
    \
    # Priority 1: root package.json has a build script \
    if [ -f package.json ] && has_build_script package.json; then \
      echo "." > .build-root; \
      echo "Build root: ./ (root package.json)"; \
    else \
      FOUND=""; \
      # Priority 2+3: only scan subfolders/workspaces if root has no start script \
      # (a root start-only app is a backend at . — skip subfolder descent) \
      if [ ! -f package.json ] || (! has_build_script package.json && ! has_start_script package.json); then \
        for SUBFOLDER in client frontend app web; do \
          if [ -f "$SUBFOLDER/package.json" ] && has_build_script "$SUBFOLDER/package.json"; then \
            echo "$SUBFOLDER" > .build-root; \
            echo "Build root: ./$SUBFOLDER/ (subfolder detected)"; \
            FOUND="1"; \
            break; \
          fi; \
        done; \
        \
        if [ -z "$FOUND" ]; then \
          # Priority 3: workspace detection \
          IS_WORKSPACE=""; \
          if [ -f pnpm-workspace.yaml ]; then \
            IS_WORKSPACE="1"; \
          elif [ -f package.json ] && grep -q '"workspaces"' package.json; then \
            IS_WORKSPACE="1"; \
          fi; \
          \
          if [ -n "$IS_WORKSPACE" ]; then \
            WS_FOUND=""; \
            # Collect all workspace package.json files (excluding node_modules and hidden dirs) \
            WS_PKGS=$(find . -name 'package.json' -not -path './node_modules/*' -not -path './.*/package.json' -not -path './package.json'); \
            # Check priority basenames first: web, frontend, app \
            for PRIORITY_NAME in web frontend app; do \
              for PKG in $WS_PKGS; do \
                PKG_DIR=$(dirname "$PKG"); \
                BASENAME=$(basename "$PKG_DIR"); \
                if [ "$BASENAME" = "$PRIORITY_NAME" ] && has_build_script "$PKG"; then \
                  echo "$PKG_DIR" | sed 's|^\./||' > .build-root; \
                  echo "Build root: ./$PKG_DIR/ (workspace package detected)"; \
                  WS_FOUND="1"; \
                  break 2; \
                fi; \
              done; \
            done; \
            # Then check remaining packages \
            if [ -z "$WS_FOUND" ]; then \
              for PKG in $WS_PKGS; do \
                if has_build_script "$PKG"; then \
                  PKG_DIR=$(dirname "$PKG"); \
                  echo "$PKG_DIR" | sed 's|^\./||' > .build-root; \
                  echo "Build root: ./$PKG_DIR/ (workspace package detected)"; \
                  WS_FOUND="1"; \
                  break; \
                fi; \
              done; \
            fi; \
          fi; \
        fi; \
      fi; \
      \
      # Fallback: nothing found (including start-only root apps — they stay at .) \
      if [ ! -f .build-root ]; then \
        echo "." > .build-root; \
        echo "No build script found in root or subfolders"; \
      fi; \
    fi

# Detect app type and conditionally build
RUN has_build_script() { \
      grep -A200 '"scripts"' "$1" 2>/dev/null | grep -q '"build":'; \
    }; \
    PM=$(cat .package-manager) && \
    BUILD_ROOT=$(cat .build-root) && \
    if [ "$(cat .project-type)" = "static-html" ]; then \
      echo "Simple static HTML - no build needed"; \
      echo "static-html" > .app-type; \
    elif [ "$BUILD_ROOT" != "." ] || grep -A200 '"scripts"' package.json 2>/dev/null | grep -q '"build":'; then \
      echo "Build script found, running build..."; \
      if [ "$BUILD_ROOT" != "." ]; then \
        # Install deps in subfolder if it has its own lockfile \
        if [ -f "$BUILD_ROOT/pnpm-lock.yaml" ] || [ -f "$BUILD_ROOT/yarn.lock" ] || [ -f "$BUILD_ROOT/package-lock.json" ]; then \
          (cd "$BUILD_ROOT" && $PM install --ignore-scripts); \
        else \
          # no lockfile in subfolder, rely on hoisted root node_modules \
          : ; \
        fi; \
        (cd "$BUILD_ROOT" && $PM run build) || { echo "Build failed in $BUILD_ROOT (exit $?)"; exit 1; }; \
        # Normalize output: copy subfolder build artifacts to /app root \
        if [ -d "$BUILD_ROOT/dist" ]; then \
          cp -a "$BUILD_ROOT/dist" /app/dist; \
        elif [ -d "$BUILD_ROOT/build" ]; then \
          cp -a "$BUILD_ROOT/build" /app/build; \
        elif [ -d "$BUILD_ROOT/.next" ] && [ -f "$BUILD_ROOT/.next/BUILD_ID" ]; then \
          cp -a "$BUILD_ROOT/.next" /app/.next; \
        elif [ -d /app/dist ] || [ -d /app/build ] || ([ -d /app/.next ] && [ -f /app/.next/BUILD_ID ]); then \
          echo "Build output already at root (subfolder build wrote to parent)"; \
        fi; \
        cd /app; \
      else \
        (cd "$BUILD_ROOT" && $PM run build) || { echo "Build failed in $BUILD_ROOT (exit $?)"; exit 1; }; \
      fi; \
      if [ -d .next/standalone ]; then \
        echo "nextjs-standalone" > .app-type; \
      elif [ -d .next ] && [ -f .next/BUILD_ID ]; then \
        echo "nextjs" > .app-type; \
      elif [ -d dist ]; then \
        if [ -d dist/public ] && ([ -f dist/index.cjs ] || [ -f dist/index.js ]); then \
          echo "Detected Replit project (dist/public + dist/index.cjs)"; \
          echo "Serving frontend only from dist/public/"; \
          echo "replit-frontend" > .app-type; \
        elif [ -f dist/index.cjs ] || [ -f dist/index.js ]; then \
          echo "Detected Node.js backend (dist/index.cjs without dist/public)"; \
          echo "nodejs-backend" > .app-type; \
        else \
          echo "static-dist" > .app-type; \
        fi; \
      elif [ -d build ]; then \
        echo "static-build" > .app-type; \
      elif DIST_DIR=$(find . -maxdepth 1 -type d -name 'dist-*' | head -1) && [ -n "$DIST_DIR" ]; then \
        # Some Vite/Rollup configs emit to dist-vite/, dist-rollup/, etc.
        # Rename the first match to dist/ so the static-dist serve path picks it up.
        DIST_DIR=$(basename "$DIST_DIR"); \
        echo "Detected custom dist folder: $DIST_DIR"; \
        mv "$DIST_DIR" dist; \
        echo "static-dist" > .app-type; \
      else \
        echo "ERROR: No build output found in .next, dist, build, or dist-*" && exit 1; \
      fi; \
    else \
      echo "No build script found, assuming Node.js/Express backend"; \
      echo "nodejs-backend" > .app-type; \
    fi

# Prune dev dependencies (except for Next.js standard mode which may need them at runtime)
RUN PM=$(cat .package-manager) && APP_TYPE=$(cat .app-type) && \
    if [ "$APP_TYPE" != "nextjs" ] && [ "$APP_TYPE" != "nextjs-standalone" ] && [ "$APP_TYPE" != "static-html" ]; then \
      if [ "$PM" = "pnpm" ]; then \
        pnpm prune --prod 2>/dev/null || true; \
      elif [ "$PM" = "yarn" ]; then \
        yarn install --production --ignore-scripts 2>/dev/null || true; \
      else \
        npm prune --omit=dev 2>/dev/null || true; \
      fi; \
    fi

# Production stage
FROM node:22-alpine

RUN apk add --no-cache openssl

WORKDIR /app

# Copy built app and production dependencies from builder
COPY --from=builder /app ./

# For Next.js standalone: set up the standalone server without overwriting .next/ manifests
# Standalone output lives in .next/standalone/ but does NOT include:
#   - .next/routes-manifest.json, build-manifest.json, and other manifests
#   - .next/static/ (static assets)
#   - public/ (public assets)
# So we selectively copy standalone's server.js and node_modules, then merge
# its .next/server/ into the existing .next/ which already has manifests and static.
RUN if [ -f .app-type ] && [ "$(cat .app-type)" = "nextjs-standalone" ]; then \
      cp .next/standalone/server.js . && \
      if [ -d .next/standalone/node_modules ]; then \
        rm -rf node_modules && \
        cp -a .next/standalone/node_modules ./node_modules; \
      fi && \
      if [ -d .next/standalone/.next/server ]; then \
        cp -a .next/standalone/.next/server .next/server; \
      fi && \
      rm -rf .next/standalone; \
    fi

# Install serve globally for static apps (Vite/CRA/Replit-frontend/simple HTML) only
RUN APP_TYPE=$(cat .app-type) && \
    if [ "$APP_TYPE" = "static-html" ] || [ "$APP_TYPE" = "static-dist" ] || [ "$APP_TYPE" = "static-build" ] || [ "$APP_TYPE" = "replit-frontend" ]; then \
      npm install -g serve; \
    fi

# Create entrypoint script based on detected app type
RUN APP_TYPE=$(cat .app-type) && PM=$(cat .package-manager 2>/dev/null || echo "npm") && \
    printf '#!/bin/sh\n' > /entrypoint.sh && \
    if [ "$APP_TYPE" = "static-html" ]; then \
      printf 'exec serve . -s -l 3000\n' >> /entrypoint.sh; \
    elif [ "$APP_TYPE" = "nextjs-standalone" ]; then \
      printf 'exec node server.js\n' >> /entrypoint.sh; \
    elif [ "$APP_TYPE" = "nextjs" ]; then \
      printf 'exec node_modules/.bin/next start -p 3000\n' >> /entrypoint.sh; \
    elif [ "$APP_TYPE" = "replit-fullstack" ]; then \
      printf 'exec npm start\n' >> /entrypoint.sh; \
    elif [ "$APP_TYPE" = "replit-frontend" ]; then \
      printf 'exec serve dist/public -s -l 3000\n' >> /entrypoint.sh; \
    elif [ "$APP_TYPE" = "static-dist" ]; then \
      printf 'exec serve dist -s -l 3000\n' >> /entrypoint.sh; \
    elif [ "$APP_TYPE" = "static-build" ]; then \
      printf 'exec serve build -s -l 3000\n' >> /entrypoint.sh; \
    elif [ "$APP_TYPE" = "nodejs-backend" ]; then \
      printf "exec %s start\n" "$PM" >> /entrypoint.sh; \
    fi && \
    chmod +x /entrypoint.sh

# Clear build-time placeholders so they don't leak into runtime.
# Actual values are injected by the platform (Northflank secrets) at container start.
ENV BUILD_MODE=
ENV BETTER_AUTH_URL=
ENV BETTER_AUTH_SECRET=
ENV AUTH_SECRET=
ENV AUTH_URL=
ENV AUTH_TRUST_HOST=
ENV NEXTAUTH_SECRET=
ENV NEXTAUTH_URL=
ENV MONGODB_URI=
ENV DATABASE_URL=
ENV SESSION_SECRET=

ENV PORT=3000
ENV HOSTNAME=0.0.0.0

EXPOSE 3000

CMD ["/entrypoint.sh"]
