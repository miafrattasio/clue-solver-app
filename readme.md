# Clue Board Game Deduction Engine

## Project Overview

The Clue Solver is a full-stack, serverless web application designed to track and solve the classic board game, Clue (Cluedo), in real-time. Moving beyond simple paper tracking, this platform employs a custom-built, intelligent algorithm to deduce the three hidden solution cards (Suspect, Weapon, and Room) based on observed game events.

The application is deployed on Google Cloud Run, providing a stable, scalable public link that can be shared and used during live gameplay.

## Features

* **Intelligent Deduction Engine:** Implements a proprietary algorithm using a Knowledge Matrix to track the status of every card (Suspect, Weapon, Room) for every player and the solution envelope.
* **Smart Elimination:** Automatically applies complex deduction rules on every turn, including the **Single Possibility Rule** and **Hand Completion Logic** to accelerate solution discovery.
* **Persistent State:** Uses **Flask Sessions** to securely maintain the entire game's state (the Knowledge Matrix) across stateless HTTP requests via JSON serialization.
* **Custom Rules Support:** Features a dedicated interface to handle custom gameplay variations, such as house rules where multiple players may show a card on a single suggestion.
* **User History Tracking:** Displays a dedicated section summarizing which cards the user has shown to specific opponents, aiding player recall.
* **Flexible Card Sets:** Supports both the **Original Clue** and **Master Detective** game versions.

## Technologies Used

| Category | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend** | **Python 3.11** | Core logic and server-side processing. |
| **Web Framework** | **Flask** | Handling HTTP routing, requests, and session management. |
| **Deployment** | **Google Cloud Run** | Serverless hosting, auto-scaling, and managed environment. |
| **Containerization** | **Docker** & **Dockerfile** | Packaging the Python application for deployment. |
| **Data Storage** | **Flask Sessions** | Securely storing the persistent game state (Knowledge Matrix) via JSON serialization. |
| **Frontend** | **HTML5, CSS3, Jinja2** | Templating, data visualization, and user interface. |


## Link to project

https://clue-solver-app-893725019972.us-central1.run.app/

## Code Structure

* **`clue_solver.py`**: Contains the core `ClueDeductionEngine` class, including the Knowledge Matrix and all deduction methods.
* **`app.py`**: The Flask application entry point. Handles routing, form data processing, and session management.
* **`templates/`**: Directory containing the HTML files (`setup.html`, `game.html`).
* **`Dockerfile`**: Instructions for packaging the Python application and Gunicorn server into a deployable container image.

## Author

Mia Frattasio

