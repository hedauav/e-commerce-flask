# E-Commerce Website

An eCommerce platform for buying and selling products online. This project is designed to provide a seamless shopping experience for users and an efficient management system for sellers and admins.

## Features

- User-friendly interface for customers
- Secure authentication system
- Product search and filtering
- Shopping cart and checkout functionality
- Order history and tracking
- Admin dashboard for inventory and order management
- Payment gateway integration

## Tech Stack

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Flask (Python)
- **Database**: SQLite (or any other database of your choice)
- **Others**: Flask-Login (for authentication), Flask-WTF (for forms)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/hedauav/e-commerce-flask.git
   ```
2. Navigate to the project directory:
   ```bash
   cd e-commerce-flask
   ```
3. Set up a virtual environment:
   ```bash
   python -m venv venv
   ```
4. Activate the virtual environment:

   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

5. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

6. Set up environment variables in a `.env` file:
   ```env
   FLASK_APP=run.py
   FLASK_ENV=development
   SECRET_KEY=your_secret_key
   DATABASE_URL=sqlite:///site.db
   ```

7. Run the application:
   ```bash
   flask run
   ```

8. Open your browser and navigate to `http://127.0.0.1:5000`.

## Usage

1. Register or log in as a user.
2. Browse products, add items to your cart, and proceed to checkout.
3. Admins can log in to the admin dashboard to manage inventory and orders.

## Project Structure

```plaintext
ecommerce-website/
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── templates/
│   ├── base.html
│   ├── index.html
│   └── ...
├── app.py
│── schema.sql
│── db.py   
│   
│   
├── requirements.txt

```







