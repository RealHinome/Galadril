FROM node:24-alpine AS builder

WORKDIR /src

COPY package*.json ./
RUN npm install

COPY ./app                  ./app
COPY ./i18n                 ./i18n
COPY ./public               ./public
COPY ./nuxt.config.ts       ./nuxt.config.ts
COPY ./tailwind.config.ts   ./tailwind.config.ts
COPY ./package.json         ./package.json

RUN npm run build

FROM node:24-alpine AS runner

WORKDIR /src

COPY --from=builder /src/.output ./.output

ENV HOST=0.0.0.0
ENV PORT=3000
ENV NODE_ENV=production

EXPOSE 3000

CMD ["node", ".output/server/index.mjs"]
