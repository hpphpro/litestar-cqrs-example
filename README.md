# Litestar CQRS Example

Welcome to the Litestar CQRS Example. This repository demonstrates a complete implementation of a CQRS architecture with event sourcing, including integration tests, pre-commit hooks, continuous integration, and various operational scripts.

## Features

- **CQRS Implementation**:
    - Separation of read and write operations.
    - Optimized command and query handling.

- **Testing**:
    - Integration tests.
    - CI integration.

- **Pre-commit Hooks & CI**:
    - Automated code quality checks.
    - Continuous integration setup for builds and tests.

- **Renewal Cert Scripts**:
    - Certbot scripts for automated certificate renewal.

- **Monitoring & Logging**:
    - Integration with Grafana, Prometheus, Loki, and Vector.
    - Node Explorer for application performance insights.

- **Database Backups**:
    - Scheduled backups for data safety and recovery strategies.

## Project Structure

```plaintext
.
├── metrics/              # Contains everything related to metrics: Grafana, Prometheus, Loki, Vector
├── migrations/           # Directory for managing database migrations (Alembic)
├── nginx/                # Nginx configuration for reverse proxy and SSL settings
├── sql/                  # Additional SQL scripts and functions
├── src/                  # Application source code: modules, endpoints, services, etc.
├── tests/                # Project tests (integration, unit, etc.)
├── .env.example          # Example environment file
├── .pre-commit-config.yaml  # Configuration for pre-commit hooks
├── docker-compose.yml    # Docker orchestration
├── dockerfile            # Docker build instructions
├── pyproject.toml        # Project configuration and dependencies
├── renew-certs.sh        # Script for generating and auto-renewing SSL certificates (Certbot)
```


## Monitoring & Observability

The application integrates with monitoring tools to provide insights into application performance:

- **Grafana/Prometheus**: Monitor metrics and performance analytics.
- **Loki/Vector**: Aggregate logs and visualize log data.
- **Node Explorer**: Interactive view of the node status and metrics.


## Dependencies
 - [Postgres](https://www.postgresql.org/docs/current/index.html) ─ Database
 - [Docker](https://docs.docker.com/) ─ Docker
    ### Metics:
    - [Grafana](https://grafana.com/docs/grafana/latest/) ─ Web view for metrics
    - [Loki](https://grafana.com/docs/loki/latest/) ─ store & query logs platform
    - [Vector.dev](https://vector.dev/) ─ tool for collecting logs and send them to loki
    - [Prometheus](https://prometheus.io/) - tool for collecting metrics from your app
    ### Optional
    - [NATS](https://nats.io/) ─ Message broker

## Libs
 - [Litestar](https://litestar.dev/) ─ API Framework
 - [SQLAlchemy](https://docs.sqlalchemy.org/en/20/) ─ ORM for working with database
 - [Alembic](https://alembic.sqlalchemy.org/en/latest/) ─ A tool for database migrations
    ### Optional
    - [NATS-Client](https://nats-io.github.io/nats.py/) - A client to interact with NATS broker

## Getting Started

1. **Clone the repository**:
     ```bash
     git clone git@github.com:hpphpro/litestar-cqrs-example.git
     cd litestar-cqrs-example
     ```
2. **Configure**:

    **rename env**
    ```bash
    mv .env.example .env
    ```
    **install (from pip) uv if does not have it**
    ```bash
    pip install uv
    ```
    - [read how to install uv](https://docs.astral.sh/uv/getting-started/installation/)
3. **Install dependencies**:
     ```bash
     uv sync --all-groups
     ```
4. **Run tests**:
     ```bash
     uv run pytest
     ```
5. **Start the application**:
     ```bash
     uv run -m src
     ```

7. **Start in docker**:

    migration
    ```bash
    docker compose --profile migration up -d
    ```
    project with metrics
    ```bash
    docker compose --profile api --profile grafana --profile prometheus up -d
    ```
    stopping
    ```bash
    docker compose --profile api --profile grafana --profile prometheus down
    ```
6. **Renew certificates using certbot (Ensure that you configure it properly)**:
     ```bash
     chmod +x renew-certs.sh && . ./renew-certs.sh
     ```
