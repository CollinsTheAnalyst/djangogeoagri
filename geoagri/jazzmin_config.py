# geoagri/jazzmin_config.py

JAZZMIN_SETTINGS = {
    "site_title": "GeoAgri Admin",
    "site_header": "🌾 GeoAgri Dashboard",
    "site_brand": "GeoAgri",
    "welcome_sign": "🌱 Manage farms, crops, and agronomy insights in one place",
    "copyright": "© 2025 GeoAgri | Powered by Django & Jazzmin",

    # === Navbar ===
    "topmenu_links": [
        {"name": "Dashboard", "url": "admin:index", "icon": "fas fa-tachometer-alt"},
    ],

    # === Sidebar Settings ===
    "show_sidebar": True,
    "navigation_expanded": True,

    # === Sidebar Grouping ===
    "app_list": [
        {
            "label": "User Access & Roles",
            "icon": "fas fa-user-shield",
            "models": [
                {"model": "auth.User", "name": "Users"},
                {"model": "auth.Group", "name": "Groups"},
                {"model": "auth.Permission", "name": "Permissions"},
            ],
        },
        {
            "label": "Farm Management",
            "icon": "fas fa-tractor",
            "models": [
                {"model": "agrigeo.FarmBoundary", "name": "Farms"},
                {"model": "agrigeo.CropApplication", "name": "Crop Applications"},
                # Add if exists:
                # {"model": "agrigeo.FarmReport", "name": "Farm Reports"},
            ],
        },
        {
            "label": "Agronomy",
            "icon": "fas fa-seedling",
            "models": [
                {"model": "agrigeo.Crop", "name": "Crops"},
                {"model": "agrigeo.Fertilizer", "name": "Fertilizers"},
                {"model": "agrigeo.FertilizerStageMapping", "name": "Fertilizer Stages"},
                # You can add these later:
                # {"model": "agrigeo.Nutrient", "name": "Nutrients"},
                # {"model": "agrigeo.CropModel", "name": "Crop Models"},
                # {"model": "agrigeo.CropYield", "name": "Crop Yield & Output"},
            ],
        },
        {
            "label": "Blog & Updates",
            "icon": "fas fa-newspaper",
            "models": [
                {"model": "blog.BlogPost", "name": "Blog Posts"},
            ],
        },
    ],

    # === Icons ===
    "icons": {
        "agrigeo.FarmBoundary": "fas fa-draw-polygon",
        "agrigeo.Crop": "fas fa-leaf",
        "agrigeo.Fertilizer": "fas fa-vial",
        "agrigeo.FertilizerStageMapping": "fas fa-list-ol",
        "agrigeo.CropApplication": "fas fa-clipboard-list",
        "auth.User": "fas fa-user",
        "auth.Group": "fas fa-users",
        "auth.Permission": "fas fa-key",
        "blog.BlogPost": "fas fa-newspaper",
    },

    # === Themes & UI tweaks ===
    "theme": "flatly",
    "show_ui_builder": False,
}

JAZZMIN_UI_TWEAKS = {
    "theme": "flatly",
    "dark_mode_theme": "darkly",
    "navbar": "navbar-dark navbar-success",
    "accent": "accent-green",
    "sidebar": "sidebar-dark-success",
    "sidebar_nav_flat_style": True,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": True,  # tighter spacing
    "sidebar_nav_small_text": True,     # smaller text/icons
    "actions_sticky_top": True,
    "brand_colour": "navbar-success",
}
