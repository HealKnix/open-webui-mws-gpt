def build_openapi_document() -> dict:
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Terminal Orchestrator",
            "version": "0.1.0",
            "description": "Per-user container orchestrator for Open Terminal.",
        },
        "paths": {
            "/api/v1/policies": {
                "get": {
                    "summary": "List orchestrator policies",
                    "responses": {"200": {"description": "OK"}},
                }
            },
            "/api/v1/policies/{policy_id}": {
                "put": {
                    "summary": "Upsert an orchestrator policy",
                    "parameters": [
                        {
                            "in": "path",
                            "name": "policy_id",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {"200": {"description": "OK"}},
                }
            },
            "/p/{policy_id}/{path}": {
                "parameters": [
                    {"in": "path", "name": "policy_id", "required": True, "schema": {"type": "string"}},
                    {"in": "path", "name": "path", "required": True, "schema": {"type": "string"}},
                ],
                "get": {"summary": "Proxy to per-user terminal container", "responses": {"200": {"description": "OK"}}},
                "post": {"summary": "Proxy to per-user terminal container", "responses": {"200": {"description": "OK"}}},
                "put": {"summary": "Proxy to per-user terminal container", "responses": {"200": {"description": "OK"}}},
                "patch": {"summary": "Proxy to per-user terminal container", "responses": {"200": {"description": "OK"}}},
                "delete": {"summary": "Proxy to per-user terminal container", "responses": {"200": {"description": "OK"}}},
            },
        },
        "components": {
            "securitySchemes": {
                "bearer": {"type": "http", "scheme": "bearer"}
            }
        },
        "security": [{"bearer": []}],
    }
