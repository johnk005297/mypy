from .models import MenuItem

MENU = [
    MenuItem("git", "GitLab"),
    MenuItem("database", "Database"),
    MenuItem("docker", "Docker Images"),
    MenuItem("vsphere", "vSphere"),
    MenuItem(
        "bimeister",
        "Bimeister",
        children=[
            MenuItem("feature_toggle", "Feature Toggles"),
            MenuItem("license", "Licenses"),
            MenuItem("import", "Import"),
            MenuItem("export", "Export"),
        ],
    ),
]