# Triggers API

This service provides CDC (Change Data Capture) functionality for the monitors API database. It watches for changes to database tables and sends notifications to configurable endpoints.

## Features

- PostgreSQL logical replication for capturing database changes
- Configurable triggers for different entity types and change types
- Filtering capability to match specific conditions
- REST API for managing triggers
- Event history and tracking

## Requirements

- Python 3.10+
- PostgreSQL 12+ with logical replication enabled
- monitors API database

## Setup

1. Clone the repository
2. Create a virtual environment and install dependencies:

```bash
make setup
```

3. Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run the application:

```bash
make run
```

## Configure PostgreSQL for Logical Replication

To use CDC functionality, you need to configure PostgreSQL for logical replication:

1. Update `postgresql.conf`:

```
wal_level = logical
max_replication_slots = 10  # at least 1, but more if you have multiple apps using replication
max_wal_senders = 10        # at least 1, but more if you have multiple apps using replication
```

2. Restart PostgreSQL:

```bash
sudo systemctl restart postgresql
```

## API Endpoints

### Triggers

- `GET /api/v1/triggers` - List all triggers
- `POST /api/v1/triggers` - Create a new trigger
- `GET /api/v1/triggers/{id}` - Get a specific trigger
- `PUT /api/v1/triggers/{id}` - Update a trigger
- `DELETE /api/v1/triggers/{id}` - Delete a trigger
- `POST /api/v1/triggers/{id}/activate` - Activate a trigger
- `POST /api/v1/triggers/{id}/deactivate` - Deactivate a trigger

### Events

- `GET /api/v1/events` - List all events
- `GET /api/v1/events/{id}` - Get a specific event
- `GET /api/v1/events/trigger/{id}` - Get events for a specific trigger

### Health Check

- `GET /api/v1/health` - Health check endpoint

## Development

### Running Tests

```bash
make test
```

### Linting and Formatting

```bash
make lint
make format
```

### Database Migrations

To create a new migration:

```bash
. trigger/bin/activate && alembic revision --autogenerate -m "description"
```

To run migrations:

```bash
. trigger/bin/activate && alembic upgrade head
```

## License

See the [LICENSE](LICENSE) file for details.