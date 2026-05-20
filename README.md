# PaintShop Django E-Commerce & Service Booking Platform

A full-featured, robust full-stack web application built using Python and Django. This platform provides a dual-purpose business solution for a modern paint retail shop: a complete product e-commerce catalog with a structured cart system and custom payment tracking, alongside an interactive home painting service booking module.

The project also features a completely custom, configuration-driven Administrative Dashboard built from the ground up to handle tailored business workflows, operational user roles, data snapshots, and granular CRUD permissions.

---

## 🚀 Key Features

### 🛒 E-Commerce Lifecycle
* **Product Catalog:** Grouped dynamically by **Categories** (e.g., Emulsions, Primers, Tools) and **Brands** (e.g., Asian Paints, Berger) with multiple product images.
* **Smart Cart System:** Fully functional relational database-driven shopping cart maintaining item states, colors, quantities, and real-time subtotal calculations.
* **Order & Payment Flow:** Handled through a distinct multi-stage lifecycle mapping (`pending` ➡️ `confirmed` ➡️ `processing` ➡️ `out_for_delivery` ➡️ `completed`).
* **Enhanced Payment Processing:** Supports **UPI** (capturing explicit transaction IDs and Bank UTR reference numbers) and **Cash on Delivery (COD)** options.
* **Automated Invoices:** Generates single-relationship historical invoice records mapping total amounts, specific payment instances, and incremental invoice numbering conventions (`INV-2026-001`).

### 🎨 Painting Service Bookings
* **Dynamic Material Estimation:** Users input their required area coverage in square feet (`area_sqft`), and the system automatically calculates the estimated price and required paint quantity (`required_qty`).
* **Operational Lifecycle Tracking:** Manages job workflows from customer request to worker assignment, through execution (`in_progress`) to final closeout.

### 🛠️ Custom Config-Driven Admin Panel
* **Workflow Over Database Raw Syncing:** Built to show clean business actions rather than raw data dumps, keeping sensitive tables like auth layers hidden.
* **Granular Permission Arrays:** Utilizes an `ADMIN_MODULES` metadata layout mapping clear operational bounds:
  * **Full CRUD:** Products, Categories, Colors, Brands, Offers, Services, and Staff.
  * **Status Edit Only:** Orders, Bookings, and Deliveries (protects historical itemized snapshots).
  * **Read-Only Reporting:** Customers and Payment history.
  * **Moderation Only:** Deletion flags for user feedback/spam.
* **Operational Metrics Dashboard:** At-a-glance analytics reflecting real-time inventory counts (low stock/out of stock alerts), pending order thresholds, overdue delivery flags, and recent customer onboardings.

---

## 📊 Database Architecture (MySQL)

The system relies on an optimized, highly relational relational schema ensuring complete data safety across high-impact business interactions:
* **Historical Snapshots:** Order items freeze individual product prices at the exact time of purchase to ensure database shifts or price updates don't alter past revenue logs.
* **Data Integrity Restraints:** Critical customer profiles and booking records use `on_delete=models.PROTECT` rules to ensure active transactional lines are never orphaned by accidental cascading user account deletions.

---

## 🛠️ Tech Stack

* **Backend:** Python, Django Web Framework
* **Database:** MySQL
* **Frontend:** HTML5, CSS3, Bootstrap 5, Bootstrap Icons
* **Environment Security:** Python-Decouple (`.env` configuration structure hiding secret keys and database root credentials)

---

## ⚙️ Installation & Setup Instruction

### 1. Clone the Repository
```bash
git clone [https://github.com/kuldipprajapati3108/paintshop-django.git](https://github.com/kuldipprajapati3108/paintshop-django.git)
cd paintshop-django
```

### 2. Set Up a Virtual Environment
```bash
python -m venv venv
# Activate on Windows:
venv\Scripts\activate
# Activate on macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a .env file in the project directory root level (alongside manage.py):

```bash
SECRET_KEY=your_secure_django_secret_key
DEBUG=True
DB_NAME=paintshop_db
DB_USER=your_mysql_user
DB_PASSWORD=your_mysql_password
DB_HOST=127.0.0.1
DB_PORT=3306
```

### 5. Setup Database Schemas
Ensure your local MySQL server is running, build the target schema name matching your .env, and apply structural migrations:

```Bash
python manage.py check
```

### 6. Run the Application
```Bash
python manage.py runserver
Access the application at http://127.0.0.1:8000/.
```
---