"""Import all callback modules to register them with the Dash app.

Each module's ``@app.callback`` decorators execute on import, binding
the callbacks to the app instance created in ``serving.py``.
"""

from callbacks import (  # noqa: F401
    navigation,
    kpi_query,
    run_sql,
    ingestion,
    reports,
    health,
    clientside,
)
