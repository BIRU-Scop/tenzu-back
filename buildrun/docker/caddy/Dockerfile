FROM caddy:2.9-builder AS builder
RUN xcaddy build --with github.com/caddy-dns/ovh

FROM caddy:2.9
COPY --from=builder /usr/bin/caddy /usr/bin/caddy