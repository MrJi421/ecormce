# README.md

# E-commerce Flask App

This is a simple e-commerce application built using Flask for the backend and MySQL for the database. The application allows users to browse products, manage their shopping cart, and place orders.

## Features

- User authentication (login and registration)
- Product listing and details
- Shopping cart management
- Order placement and history

## Project Structure

```
ecommerce-flask-app
├── src
│   ├── app.py                # Entry point of the application
│   ├── database.py           # Database connection and setup
│   ├── models                # Contains data models
│   │   ├── __init__.py
│   │   ├── product.py        # Product model
│   │   ├── user.py           # User model
│   │   └── order.py          # Order model
│   ├── routes                # Contains route handlers
│   │   ├── __init__.py
│   │   ├── auth.py           # Authentication routes
│   │   ├── products.py       # Product-related routes
│   │   ├── cart.py           # Shopping cart routes
│   │   └── orders.py         # Order-related routes
│   ├── templates             # HTML templates
│   │   ├── base.html         # Base template
│   │   ├── home.html         # Homepage
│   │   ├── products.html     # Products page
│   │   ├── cart.html         # Shopping cart page
│   │   ├── login.html        # Login page
│   │   └── register.html     # Registration page
│   └── static                # Static files (CSS, JS)
│       ├── css
│       │   └── style.css     # CSS styles
│       └── js
│           └── main.js       # JavaScript functionality
├── config.py                 # Configuration settings
├── requirements.txt          # Project dependencies
└── README.md                 # Project documentation
```

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd ecommerce-flask-app
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up the database and update the configuration in `config.py`.

4. Run the application:
   ```
   python src/app.py
   ```

## License

This project is licensed under the MIT License.