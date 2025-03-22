# Claude Guidelines for Trigger Project

## Project Purpose

The Triggers application is a Change Data Capture (CDC) service that watches for changes to the Monitors API database and sends notifications to configured endpoints. This allows for event-driven actions based on data changes.

## Core Functionality

1. CDC using PostgreSQL logical replication
2. Configurable triggers with filtering
3. API endpoints for trigger management
4. Event history and tracking

## Key Features

- Monitor changes to specific entities (monitors, statuses, tags)
- Filter events by type (insert, update, delete)
- Apply custom filtering conditions
- Configure notification endpoints
- Track event processing history

## Key Components

- **CDC Connection**: Manages PostgreSQL logical replication
- **CDC Listener**: Background thread that listens for database changes
- **Event Processor**: Processes change events and sends notifications
- **Trigger API**: Manages trigger configurations

## Key Files and Their Purpose

- `app/main.py`: FastAPI application entry point
- `app/models/trigger.py`: Data models for triggers and events
- `app/schemas/trigger.py`: Pydantic schemas for API validation
- `app/cdc/connection.py`: PostgreSQL logical replication setup
- `app/cdc/listener.py`: Background thread for listening to changes
- `app/events/processor.py`: Event processing and notification logic
- `app/api/v1/endpoints/triggers.py`: API endpoints for trigger management
- `app/api/v1/endpoints/events.py`: API endpoints for event history

## Database Schema

1. `triggers` table:
   - Configurable triggers for watching database changes
   - Fields: id, name, entity_type, change_types, filter_condition, endpoint, is_active

2. `trigger_events` table:
   - History of detected changes and notification status
   - Fields: id, trigger_id, entity_id, change_type, old_data, new_data, processed, response_status

## Relationship with Other Components

- Depends on **monitors-api** database for CDC source
- Could be integrated with **monitors-terraform** for deployment

## Deployment Considerations

- PostgreSQL must be configured for logical replication
- Requires database permissions for replication
- Stateful service that maintains replication slots

## Testing Strategy

- Unit tests for API endpoints
- Mock testing for CDC functionality (difficult to test CDC directly)
- Integration tests with a real PostgreSQL database (optional)