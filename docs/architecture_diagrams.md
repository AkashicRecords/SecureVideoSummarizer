# Architecture Diagrams

This document contains the visual representations of the Secure Video Summarizer's architecture and data flow.

## System Architecture

![System Architecture](images/system_architecture.png)

The three-tier architecture of the Secure Video Summarizer:
1. Browser Extension (Chrome)
2. Frontend Application (Port 8080)
3. Backend Service (Port 8081)

## Data Flow

![Data Flow](images/data_flow.png)

The complete data flow showing:
- User interactions
- Component communication
- Data processing steps
- Response flow

## Component Communication

![Component Communication](images/component_communication.png)

Sequence diagram showing the interaction between:
- User
- Extension
- Frontend
- Backend

## Port Configuration

![Port Configuration](images/port_configuration.png)

Visual representation of port assignments and communication paths:
- Frontend: Port 8080
- Backend: Port 8081
- Extension: Browser messaging system 