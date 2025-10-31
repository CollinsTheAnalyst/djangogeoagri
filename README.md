DjangoGeoAgri: Geospatial Agriculture Platform

## Overview

DjangoGeoAgri is a robust, full-stack web application built on the Django framework, designed to empower farmers, agronomists, and researchers with advanced geospatial and agronomic data tools. This platform integrates modern remote sensing data, soil science, and precise location-based services to drive efficient farm management and optimal crop yields.

It leverages GeoDjango and PostGIS for handling complex spatial data, ensuring highly accurate calculations and analyses.

## ✨ Key Features

DjangoGeoAgri provides a suite of tools centered around five core functions:

Farm Boundary and Area Calculation:

Utilizes interactive mapping tools (e.g., Leaflet/OpenLayers) to allow users to draw or upload farm boundaries.

Calculates the precise area (in acres, hectares, or custom units) using geospatial algorithms.

Stores farm geometries in the PostGIS database for persistent, accurate data.

NDVI/EVI Explorer (Vegetation Indices):

Allows users to explore Normalized Difference Vegetation Index (NDVI) and Enhanced Vegetation Index (EVI) imagery for defined farm boundaries.

Integrates with external satellite data APIs (e.g., Sentinel, Landsat) to fetch and visualize vegetation health over time.

Provides color-coded maps showing crop vigor, helping identify stress zones and areas needing attention.

Soil Taxonomy and Classification:

Provides access to a database of regional and global soil classifications (e.g., USDA Soil Taxonomy).

Allows users to query soil types based on location, providing detailed information on composition, structure, and land capability.

Soil Nutrient Data Management:

Enables users to input, store, and visualize laboratory results for key soil nutrients (e.g., N, P, K, pH, Organic Matter).

Visualizes nutrient levels across different farm zones, highlighting deficiencies or excesses on a map interface.

Intelligent Fertilizer Recommendations:

Combines data from Farm Boundary, Soil Nutrient Data, and Crop Type to generate highly specific fertilizer recommendations.

Calculates optimal nutrient application rates (Variable Rate Technology-ready) to maximize yield while minimizing waste and environmental impact.

## 🛠️ Tech Stack

Backend: Python, Django, GeoDjango

Database: PostgreSQL with PostGIS extension (for spatial data)

Frontend: HTML5, Tailwind CSS, JavaScript

Mapping: Leaflet.js / OpenLayers (for interactive map components)
