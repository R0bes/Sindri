"""Default configuration template."""

def get_default_config_template() -> str:
    """Get the default config template."""
    return """# Sindri Configuration
# This file defines commands and workflows for your project

version = "1.0"
project_name = "my-project"

[[commands]]
id = "setup"
title = "Setup Project"
description = "Install dependencies and set up the project"
shell = "pip install -e ."
tags = ["setup", "install"]

[[commands]]
id = "install"
title = "Install Dependencies"
description = "Install project dependencies"
shell = "pip install -r requirements.txt"
tags = ["setup", "install"]

[[commands]]
id = "start"
title = "Start Service"
description = "Start the main service"
shell = "python -m myproject.main"
tags = ["run", "start"]

[[commands]]
id = "stop"
title = "Stop Service"
description = "Stop the running service"
shell = "pkill -f 'python -m myproject.main'"
tags = ["run", "stop"]

[[commands]]
id = "restart"
title = "Restart Service"
description = "Restart the service"
shell = "pkill -f 'python -m myproject.main' && sleep 1 && python -m myproject.main"
tags = ["run", "restart"]
dependencies = { before = ["stop"] }

[[commands]]
id = "docker-build"
title = "Docker Build"
description = "Build Docker image"
shell = "docker build -t myproject:latest ."
tags = ["docker", "build"]

[[commands]]
id = "docker-run"
title = "Docker Run"
description = "Run Docker container"
shell = "docker run -p 8000:8000 myproject:latest"
tags = ["docker", "run"]

[[commands]]
id = "compose-up"
title = "Docker Compose Up"
description = "Start services with Docker Compose"
shell = "docker compose up -d"
tags = ["docker", "compose"]

[[commands]]
id = "compose-down"
title = "Docker Compose Down"
description = "Stop services with Docker Compose"
shell = "docker compose down"
tags = ["docker", "compose"]

[[commands]]
id = "compose-restart"
title = "Docker Compose Restart"
description = "Restart services with Docker Compose"
shell = "docker compose restart"
tags = ["docker", "compose"]

[[commands]]
id = "compose-logs"
title = "Docker Compose Logs"
description = "View Docker Compose logs"
shell = "docker compose logs -f"
tags = ["docker", "compose", "logs"]
watch = true

[[commands]]
id = "tail-logs"
title = "Tail Logs"
description = "Tail application logs"
shell = "tail -f logs/app.log"
tags = ["logs", "watch"]
watch = true

[[groups]]
id = "setup"
title = "Setup"
description = "Setup and installation commands"
order = 1
commands = ["setup", "install"]

[[groups]]
id = "run"
title = "Run"
description = "Start, stop, and restart commands"
order = 2
commands = ["start", "stop", "restart"]

[[groups]]
id = "docker"
title = "Docker"
description = "Docker and Docker Compose commands"
order = 3
commands = ["docker-build", "docker-run", "compose-up", "compose-down", "compose-restart", "compose-logs"]

[[groups]]
id = "logs"
title = "Logs"
description = "Log viewing commands"
order = 4
commands = ["tail-logs", "compose-logs"]
"""

