# EcoTrace — Micro-Logistics & Shelf-Life Tracker

## 1. Project Overview

EcoTrace is a database-driven inventory management application designed to track stock quantities, inventory batches, product shelf life, consumption, suppliers, and purchases. It helps users monitor stock availability, identify low-stock items, and maintain inventory movement records.

## 2. Objectives

- Manage products and inventory categories.
- Track received and available stock by batch.
- Monitor expiry dates and shelf life.
- Record consumption and stock adjustments.
- Maintain supplier and purchase records.
- Generate inventory reports and CSV exports.
- Store application data in a MySQL relational database.

## 3. Technologies Used

- **Programming Language:** Python
- **User Interface:** Streamlit
- **Database:** MySQL 8.0+
- **Database Connectivity:** Python MySQL connector
- **Development Environment:** Visual Studio Code
- **Data Processing:** Pandas

## 4. Main Features

- Dark-themed dashboard with inventory summaries.
- Product and category management.
- Batch-wise stock tracking.
- Consumption logging and stock movement history.
- Supplier directory and purchase management.
- Low-stock monitoring.
- Inventory reporting and CSV downloads.

## 5. Database Design

The MySQL database is named `ecotrace_db` and contains nine tables:

1. `categories` — stores inventory categories.
2. `items` — stores product information and reorder levels.
3. `inventory_batches` — tracks received and available quantities by batch.
4. `usage_logs` — records consumption history.
5. `stock_movements` — records receipts, consumption, and stock adjustments.
6. `suppliers` — stores supplier contact information.
7. `purchases` — stores purchase order details.
8. `purchase_items` — stores the individual products in each purchase.
9. `app_settings` — stores configurable application settings.

## 6. Project Structure

```text
EcoTrace/
├── app.py
├── db.py
├── config.py
├── schema.sql
├── seed_data.sql
├── setup_database.py
├── requirements.txt
├── .env
├── .env.example
├── README.md
├── assets/
├── modules/
├── services/
└── tests/
```

## 7. Prerequisites

Install the following before running the application:

- Python 3.13
- MySQL Server 8.0 or compatible
- Visual Studio Code
- Python packages listed in `requirements.txt`

## 8. Installation and Setup

### Step 1: Open the project

Open the `C:\EcoTrace` folder in Visual Studio Code.

### Step 2: Activate the virtual environment

Open the VS Code PowerShell terminal and run:

```powershell
cd C:\EcoTrace
.\.venv\Scripts\Activate.ps1
```

### Step 3: Configure database credentials

Check the `.env` file and ensure it contains the correct MySQL connection settings expected by `config.py`. Keep credentials private and do not publish `.env`.

### Step 4: Set up the database

If the database has not already been initialized, use the project's database setup script:

```powershell
python setup_database.py
```

This project has already been configured with its schema and sample data. Avoid rerunning setup unnecessarily if you are unsure whether it will modify existing data.

### Step 5: Install dependencies if needed

```powershell
python -m pip install -r requirements.txt
```

## 9. Run the Application

Activate the virtual environment and execute:

```powershell
python -m streamlit run app.py --server.port 8503
```

Open this address in your browser:

http://localhost:8503

Keep the terminal open while using the application.

If the port is already occupied, use another available port, such as `8504`, and open the corresponding localhost address.

## 10. Testing

The following application functions have been tested during development:

- Dashboard loading and database connectivity.
- Product and category management.
- Stock adjustment validation.
- Consumption and stock movement recording.
- Supplier listing.
- Inventory report CSV export.

Additional testing should be performed after any code changes.

## 11. Future Enhancements

- Improved inventory forecasting.
- More advanced analytics and visualizations.
- Automated expiry notifications.
- Enhanced authentication and role-based access.
- Expanded automated testing.

## 12. Conclusion

EcoTrace demonstrates how Python, Streamlit, and MySQL can be integrated to create a relational database application for inventory tracking, shelf-life monitoring, stock movement management, and reporting.
