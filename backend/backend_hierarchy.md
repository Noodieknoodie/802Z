backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   └── models.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── endpoints/
│   │   │   ├── __init__.py
│   │   │   ├── clients.py
│   │   │   ├── payments.py
│   │   │   ├── providers.py
│   │   │   └── documents.py
│   │   └── dependencies.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── security.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── client_service.py
│   │   ├── payment_service.py
│   │   └── document_service.py
│   └── utils/
│       ├── __init__.py
│       └── format.py
├── tests/
└── requirements.txt