# BUSINESS REQUIREMENT SPECIFICATION (BRS)

## Custom Blouse Tailoring & Order Management Web Application

**Document Version:** 1.1 (updated to reflect the current implementation - see Section 46)  
**Application Type:** Python Web Application  
**Hosting Environment:** Windows Server + IIS  
**Database:** Microsoft SQL Server  
**Primary Users:** Admin / Customer  
**Application Purpose:** Customer Measurement, Blouse Design, Order Management, Trial Management, Customer Communication and Order Tracking

---

# 1. Business Objective

The objective of this application is to develop a modern web-based tailoring management system for managing customer measurements, blouse designs, orders, payments, trial images, delivery dates and customer communication.

The system will provide two major interfaces:

1. **Admin Portal**
2. **Customer Portal / Website**

The application will allow the admin to manage the complete lifecycle of a blouse order, starting from customer registration/measurement collection through design selection, order processing, trial, payment and final delivery.

Customers will be able to:

- Register/Login
- View available blouse designs
- View design images and pricing
- Maintain their measurements
- Place orders
- Make online/offline payments
- Track order status
- Receive trial notifications through email
- View their order history

---

# 2. Technology & Infrastructure Requirements

| Component | Requirement |
|---|---|
| Application | Python Web Application |
| Web Server | IIS on Windows Server |
| Database | Microsoft SQL Server |
| Frontend | Modern responsive Web UI |
| Backend | Python |
| Database Access | Secure SQL connection |
| Email | Gmail API / approved email service |
| Hosting | IIS initially; architecture should support future migration |
| Image Storage | Server/File Storage |
| Payment | QR Code / Online Payment Integration |
| Authentication | Secure Login / Registration |
| Browser | Chrome, Edge and modern browsers |

### Important Data Storage Rule

All **business/transactional data must be stored in MS SQL Server**.

Examples:

- Customer information
- Mobile number
- Email
- Measurements
- Blouse designs
- Design pricing
- Orders
- Order status
- Payment information
- Trial information
- Delivery date
- Email notification history
- Admin activity/audit information

Images should be stored in structured server/file storage, while the **image path, unique file name, type and related entity/order ID must be stored in MS SQL Server**.

---

# 3. Image Storage Structure

The system should maintain a standard folder structure.

Example:

```text
/ApplicationRoot
│
├── Images
│   │
│   ├── HomePage
│   ├── Brand
│   ├── Logo
│   ├── Gallery
│   ├── BlouseDesign
│   ├── CustomerReference
│   ├── Trial
│   └── Order
│
├── Logs
├── Config
└── Application
```

For customer/order-specific images:

```text
Images
│
├── CustomerReference
│   └── CUST000001
│       └── REF_20260911_001.jpg
│
├── Trial
│   └── ORD000001
│       └── TRIAL_20260911_001.jpg
│
└── Order
    └── ORD000001
        └── ORDER_20260911_001.jpg
```

### Image Naming Convention

Images should never be stored using the original customer file name.

Recommended format:

```text
<IMAGE_TYPE>_<ORDER_ID>_<TIMESTAMP>_<UNIQUE_ID>.<EXTENSION>
```

Example:

```text
TRIAL_ORD000125_20260911153025_A8F21.jpg
```

This will prevent duplicate file names and make images easier to identify.

### Database Image Record

MS SQL should maintain:

- Image ID
- Customer ID
- Order ID
- Image Type
- File Name
- File Path
- Uploaded Date
- Uploaded By
- Active/Deleted Flag

---

# 4. User Roles

## 4.1 Admin

Admin will have complete access to:

- Customer management
- Measurement management
- Blouse design management
- Pricing
- Order management
- Payment management
- Trial management
- Delivery management
- Customer communication
- Website content
- Gallery management
- Brand/logo management
- Dashboard
- Reports
- Settings
- Audit information

## 4.2 Customer

Customer will have access to:

- Registration
- Login
- Profile
- Measurements
- Browse designs
- View pricing
- Place orders
- Payment
- Order history
- Track order
- Trial status
- Delivery status

---

# 5. Website – Home Page

The public website should have a modern, premium and professional tailoring-business appearance.

### Home Page Sections

1. Brand Logo
2. Brand Image / Banner
3. About Us
4. Services
5. Blouse Designs
6. Customisation Gallery
7. Pricing
8. How It Works
9. Customer Reviews
10. Contact Us
11. Address
12. Contact Number
13. Email
14. Login
15. Sign Up
16. Track Order

### Recommended Website Navigation

```text
HOME
│
├── ABOUT US
├── DESIGNS
├── GALLERY
├── PRICING
├── HOW IT WORKS
├── CONTACT
├── LOGIN
├── SIGN UP
└── TRACK ORDER
```

---

# 6. Customer Registration

Customer registration should require:

### Mandatory

- Mobile Number
- Password

### Optional

- Email Address
- Customer Name

Mobile number should be **unique**.

Example:

```text
Mobile Number → 9876543210
                 ↓
          Check Customer
                 ↓
       Existing Customer?
          /           \
        YES            NO
        ↓               ↓
   Login/Continue   Create Customer
```

Email should also be validated if provided.

### Validation

- Mobile number must contain valid digits.
- Duplicate mobile numbers must not be allowed.
- Password must satisfy minimum security requirements.
- Email must be validated.
- OTP verification can be implemented as an additional security feature.

---

# 7. Customer First-Time Measurement Logic

After registration, the system should check whether measurement information already exists.

### Scenario A – New Customer

```text
Customer Registration
        ↓
Check Customer
        ↓
No Measurement Found
        ↓
Ask Customer to Enter Measurement
        ↓
Save Measurement
        ↓
Customer Can Place Order
```

### Scenario B – Existing Customer With Measurement

```text
Customer Login
      ↓
Check Measurement
      ↓
Measurement Available
      ↓
Show Existing Measurement
      ↓
Customer Selects Design
      ↓
Place Order
```

The customer should **not be forced to enter measurements repeatedly**.

The customer can optionally update measurements before placing a new order.

---

# 8. Admin – Login

Admin login should be separate from customer login.

Admin authentication should include:

- Username
- Password
- Account status
- Failed login protection
- Session timeout
- Logout
- Optional OTP / 2FA

Password must never be stored as plain text.

Passwords should be stored using a secure hashing mechanism.

---

# 9. Admin Dashboard

After successful admin login, the admin dashboard should display important business information.

### Dashboard KPIs

- Total Customers
- Total Orders
- New Orders
- Orders in Cutting
- Orders in Stitching
- Orders in Trial
- Orders Ready for Delivery
- Completed Orders
- Cancelled Orders
- Total Order Amount
- Amount Received
- Amount Pending
- Today's Deliveries
- Upcoming Deliveries

### Dashboard Example

```text
-----------------------------------------------------
| Customers | Total Orders | Pending Orders |
-----------------------------------------------------
|   250     |      480     |       35        |
-----------------------------------------------------

-----------------------------------------------------
| Received Amount | Pending Amount | Completed |
-----------------------------------------------------
| ₹2,50,000       | ₹45,000        | 420       |
-----------------------------------------------------

Upcoming Deliveries
-----------------------------------------------------
| Order ID | Customer | Delivery Date | Status |
-----------------------------------------------------
```

---

# 10. Customer Management

Admin should have an option:

**Customer Management**

Functions:

- Add Customer
- Search Customer
- View Customer
- Modify Customer
- Delete/Deactivate Customer
- View Customer Orders
- View Customer Measurements
- View Payment History
- View Trial History

> **Current implementation note**: the customer detail screen shows the
> customer's measurement versions and order list directly; payment
> history and trial history are viewed per-order (open an order from
> that list to see its payments/trial images) rather than as a single
> consolidated list across all of a customer's orders.

### Search Criteria

Admin should be able to search using:

- Mobile Number
- Customer Name
- Email
- Order ID

---

# 11. Customer Measurement Module

Admin can create and maintain customer measurements.

### Customer Information

- Customer ID
- Customer Name
- Mobile Number
- Email
- Address
- Created Date

### Blouse Measurement

The system should support configurable measurement fields.

Example:

- Blouse Length
- Shoulder
- Bust
- Waist
- Armhole
- Sleeve Length
- Sleeve Round
- Neck Front
- Neck Back
- Neck Width
- Neck Depth
- Shoulder Length
- Other Custom Measurement

The measurement module should allow future measurement fields to be added without major application changes.

### Measurement Versioning

Recommended:

```text
Customer
   ↓
Measurement V1
   ↓
Measurement V2
   ↓
Measurement V3
```

Every order should retain the **measurement version used at the time of order**.

This is important because changing a customer's current measurement should not change historical orders.

---

# 12. Blouse Design Module

Admin should be able to create and maintain blouse designs.

### Design Fields

- Design ID
- Design Name
- Design Description
- Category
- Neck Style
- Sleeve Style
- Blouse Length
- Customisation Details
- Base Price
- Additional Charges
- Design Image
- Status
- Created Date
- Modified Date

### Example

```text
Design Name: Royal V-Neck
Category: Party Wear
Base Price: ₹1,200
Customisation: Available
Status: Active
```

Customers can browse available designs.

---

# 13. Gallery Module

Admin should be able to upload gallery images.

Categories can include:

- Bridal
- Party Wear
- Traditional
- Designer
- Simple
- Wedding
- Customised
- Latest Designs

Each gallery image should have:

- Gallery ID
- Image
- Category
- Description
- Display Order
- Active/Inactive

---

# 14. Order Creation

Customer can select:

```text
Design
   ↓
Measurement
   ↓
Customisation
   ↓
Price
   ↓
Delivery Date
   ↓
Payment Option
   ↓
Confirm Order
```

### Order should generate a unique Order ID.

Example:

```text
ORD202609110001
```

The Order ID must never be reused.

---

# 15. Pricing Logic

Each order should maintain three primary amounts:

```text
Total Amount
Amount Received
Amount Pending
```

Formula:

```text
Amount Pending = Total Amount - Amount Received
```

Example:

```text
Total Amount       ₹2,000
Amount Received    ₹1,000
Amount Pending     ₹1,000
```

The system should calculate the pending amount automatically.

Admin should not manually enter pending amount.

---

# 16. Payment Options

Customer should have the following options:

### Option 1 – Online Payment

Customer selects:

**Pay Online**

System displays:

- Order Amount
- QR Code / Payment option
- Payment reference/instructions

Payment status should be:

```text
Pending
Success
Failed
Verified
Refunded
```

For a QR/manual payment approach, customer should ideally upload the payment reference/UTR and admin should verify it.

> **Current implementation note**: there is no live payment gateway and no
> customer-facing upload of a payment reference/UTR - the customer only
> *selects* Pay Online/At Shop/After Delivery when placing the order.
> Admin then manually records the actual payment received (amount, mode,
> optional reference number, status) against the order once money has
> changed hands (in person, via UPI, etc.) - see Section 25 Actions.

### Option 2 – Pay at Shop

Order payment status:

```text
PAYMENT_PENDING
```

### Option 3 – Pay After Delivery

Payment can remain pending until delivery.

---

# 17. Order Status / Production Workflow

The order should follow a controlled workflow.

### Recommended Statuses

```text
ORDER_RECEIVED
       ↓
MEASUREMENT_CONFIRMED
       ↓
CUTTING
       ↓
STITCHING
       ↓
TRIAL_PENDING
       ↓
TRIAL_READY
       ↓
ALTERATION_REQUIRED
       ↓
FINAL_STITCHING
       ↓
READY_FOR_DELIVERY
       ↓
DELIVERED
       ↓
COMPLETED
```

Additional status:

```text
CANCELLED
ON_HOLD
```

---

# 18. Order Progress Module

Admin can open any order and update its progress.

Each status update should store:

- Order ID
- Previous Status
- New Status
- Status Date/Time
- Remarks
- Updated By

Example:

```text
ORD202609110001

11-Sep 10:00 AM → Order Received
11-Sep 11:00 AM → Measurement Confirmed
12-Sep 02:00 PM → Cutting
13-Sep 05:00 PM → Stitching
15-Sep 11:00 AM → Trial
16-Sep 03:00 PM → Final Stitching
17-Sep 05:00 PM → Ready for Delivery
18-Sep 06:00 PM → Delivered
```

This creates a complete order history.

---

# 19. Trial Management

When an order reaches:

**TRIAL_READY**

the system should enable the trial functionality.

### Trial Flow

```text
Order Status = TRIAL_READY
             ↓
     Upload Trial Image
             ↓
       Image Uploaded?
          /       \
        NO         YES
        ↓           ↓
 Button Disabled   Enable
                   "Send Trial Message"
```

The **Send Trial Message** button should remain disabled until a valid trial image is uploaded.

---

# 20. Trial Image

Admin uploads the customer's trial image.

The system should:

1. Validate file type.
2. Validate maximum file size.
3. Generate unique file name.
4. Save image in the appropriate order folder.
5. Store image metadata in MS SQL.
6. Update trial status.
7. Enable Send Trial Message.

Example:

```text
Trial Image
     ↓
Validate
     ↓
Generate Unique Name
     ↓
Save File
     ↓
Save DB Record
     ↓
Enable Email Button
```

---

# 21. Customer Trial Email

Admin clicks:

**Send Trial Message**

System will use the configured Gmail API/email service.

### Email Flow

```text
Admin
 ↓
Click Send Trial Message
 ↓
Check Customer Email
 ↓
Check Trial Image
 ↓
Generate Predefined Message
 ↓
Send Email
 ↓
Save Email Log
 ↓
Display Success/Failure
```

Email log should store:

- Order ID
- Customer ID
- Email ID
- Email Type
- Sent Date/Time
- Status
- Error Message
- Retry Count

### Important Rule

If customer email is unavailable:

```text
Send Button → Disabled / Show "Email Not Available"
```

Admin should still be able to manually contact the customer.

### 21.1 Admin-Configurable Order-Status Emails

Beyond the trial-invite email above, admin can configure **which order
statuses automatically email the customer** as the order progresses
(e.g. Order Received, Ready for Delivery) - see Section 26.1 for where
this is set. Each status is opted in independently; a status with no
email configured simply does not send one when an order reaches it.

```text
Order reaches Status X
       ↓
Is Status X enabled for auto-email?  (Admin > Settings)
     /              \
   NO               YES
     ↓                ↓
No email sent    Send email + log to Email Log
```

Every attempt (enabled statuses only) is recorded in the Email Log the
same way as the trial invite - Order ID, Customer ID, Email ID, Status,
Sent Date/Time, Error Message.

---

# 22. Order Tracking

Customer can track an order using:

**Track Order**

Customer enters:

```text
Order ID
```

Example:

```text
ORD202609110001
```

The system displays:

```text
Order Received       ✓
Measurement          ✓
Cutting              ✓
Stitching            ✓
Trial                CURRENT
Final Stitching      -
Ready for Delivery   -
Delivered            -
```

Customer should not be able to modify order status.

Only authorized admin users can update order status.

---

# 23. Customer Order History

After login, customer should be able to see:

- Current Orders
- Previous Orders
- Order ID
- Design
- Order Date
- Delivery Date
- Total Amount
- Amount Paid
- Pending Amount
- Current Status

Customer can click an order to view complete details.

---

# 24. Delivery Date Management

Admin should have a calendar-based delivery date selection.

### Rules

- Delivery date cannot normally be before order date.
- System should show current date.
- Admin can select future date.
- Upcoming delivery dates should be visible on dashboard.
- Delivery date changes should be logged.
- Optional: system can prevent booking beyond daily capacity.

### Recommended Enhancement – Daily Capacity

Example:

```text
Maximum Orders per Day = 10

18-Sep
Booked = 10
Status = FULL

19-Sep
Booked = 6
Available = 4
```

This prevents overbooking.

---

# 25. Admin Order Management

Admin should have an **All Orders** screen.

Columns:

| Field |
|---|
| Order ID |
| Customer |
| Mobile |
| Design |
| Order Date |
| Delivery Date |
| Total Amount |
| Received |
| Pending |
| Status |
| Last Updated |
| Action |

Actions:

- View
- Update Status
- Payment
- Trial
- Send Email
- Cancel
- Delete (permanent - see BR-022)
- Change Delivery Date
- View History

> **Current implementation note**: "Edit", "Update Measurement" and
> "Update Design" on an *existing* order are intentionally not offered -
> doing so would contradict BR-006/BR-013/BR-014 (an order must keep the
> exact design price and measurement snapshot it was created with).
> To change design or measurement for a customer going forward, update
> the customer's design choice or measurement version for their *next*
> order instead; the current order stays as originally placed.

---

# 26. Admin Settings

Admin Settings should contain:

### Website Settings

- Brand Name
- Brand Logo
- Brand Image
- Home Page Banner
- About Us
- Address
- Contact Number
- Email
- Social Media Links

### Image Management

```text
Logo Image
Brand Image
Home Page Image
Gallery Image
Design Image
```

### Pricing

Admin can configure:

- Design price
- Customisation price
- Additional charges
- Urgent order charges
- Other services

Pricing changes should preferably affect **new orders only**.

Historical orders should retain the price at the time they were created.

### 26.1 Email Trigger Settings

Admin should be able to choose **which order statuses automatically send
the customer a notification email** (see Section 21.1) - a simple
checklist of the order-status workflow (Section 17), independent of the
always-manual trial-invite email.

Example:

```text
Email Trigger Settings
-----------------------------------------------------
| Status              | Auto-email on reaching status |
-----------------------------------------------------
| ORDER_RECEIVED       |  ☑ Enabled                    |
| MEASUREMENT_CONFIRMED|  ☐ Disabled                   |
| CUTTING               |  ☐ Disabled                   |
| STITCHING             |  ☐ Disabled                   |
| READY_FOR_DELIVERY    |  ☑ Enabled                    |
| DELIVERED             |  ☑ Enabled                    |
-----------------------------------------------------
```

No code change should be required to enable/disable a status - it is a
saved setting, not a hard-coded list.

---

# 27. Audit Trail

All important admin activities should be logged.

Example:

```text
Admin User
     ↓
Changed Order Status
     ↓
ORD202609110001
     ↓
STITCHING → TRIAL_READY
     ↓
Date/Time
     ↓
Audit Log
```

Audit should capture:

- User
- Action
- Module
- Record ID
- Old Value
- New Value
- Date/Time
- IP Address where appropriate

---

# 28. Database Structure – Recommended

MS SQL Server should contain separate tables.

### Core Tables

```text
Users
Customers
CustomerMeasurements
MeasurementDetails
BlouseDesigns
DesignImages
Gallery
Orders
OrderItems
OrderMeasurements
OrderStatusHistory
OrderImages
Payments
PaymentTransactions
EmailLogs
WebsiteSettings
AdminUsers
AuditLogs
```

### Suggested Relationship

```text
CUSTOMER
   │
   ├── MEASUREMENTS
   │
   ├── ORDERS
   │      │
   │      ├── DESIGN
   │      ├── MEASUREMENT SNAPSHOT
   │      ├── PAYMENTS
   │      ├── STATUS HISTORY
   │      ├── TRIAL IMAGES
   │      └── EMAIL LOGS
   │
   └── PROFILE
```

---

# 29. Important Database Design Principle

The system should **not depend only on the current customer measurement**.

When an order is created, the system should store a snapshot/version of the measurement used for that order.

Example:

```text
Customer Current Measurement
        ↓
Measurement Version 3
        ↓
Order Created
        ↓
Order stores Measurement Version 3
```

Later:

```text
Customer Measurement Version 4
```

The old order should still use Version 3.

This is critical for tailoring applications.

---

# 30. Application Architecture

Recommended architecture:

```text
                    INTERNET
                       │
                       ▼
                ┌─────────────┐
                │    IIS      │
                │ Web Server  │
                └──────┬──────┘
                       │
                       ▼
              ┌─────────────────┐
              │ Python Web App  │
              │                 │
              │ Authentication  │
              │ Customer Module │
              │ Admin Module    │
              │ Order Module    │
              │ Payment Module  │
              │ Email Module    │
              └───────┬─────────┘
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
 ┌─────────────────┐      ┌─────────────────┐
 │ MS SQL Server   │      │ File Storage    │
 │                 │      │                 │
 │ Customers       │      │ Images          │
 │ Orders          │      │ Logos           │
 │ Measurements    │      │ Gallery         │
 │ Payments        │      │ Trial Images    │
 │ Audit Logs      │      │ Design Images   │
 └─────────────────┘      └─────────────────┘
          │
          ▼
   External Services
          │
     ┌────┴─────┐
     ▼          ▼
 Gmail API    Payment
```

---

# 31. Application Module Structure

Recommended Python application structure:

```text
TailoringWebApp/
│
├── app/
│   ├── authentication/
│   ├── admin/
│   ├── customer/
│   ├── measurements/
│   ├── designs/
│   ├── gallery/
│   ├── orders/
│   ├── payments/
│   ├── trial/
│   ├── notifications/
│   ├── reports/
│   └── settings/
│
├── templates/
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── uploads/
│
├── config/
│
├── logs/
│
├── database/
│
├── tests/
│
├── requirements.txt
│
└── run.py
```

The application should be developed in a way that avoids hard-coded Windows paths.

For example, avoid:

```text
C:\MyApplication\Images\
```

Instead use configurable application settings.

This will make future migration to another server/cloud environment easier.

---

# 32. Overall Customer Flow

```text
                 HOME PAGE
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
       LOGIN       SIGN UP   TRACK ORDER
          │          │          │
          │          ▼          │
          │      Registration   │
          │          │          │
          │          ▼          │
          │   Check Customer    │
          │          │          │
          │     ┌────┴────┐     │
          │     ▼         ▼     │
          │ Measurement  Existing│
          │ Required?    Data    │
          │     │         │      │
          │     └────┬────┘      │
          │          ▼           │
          └──────► CUSTOMER DASHBOARD
                         │
                         ▼
                  SELECT DESIGN
                         │
                         ▼
                   CUSTOMISATION
                         │
                         ▼
                    VIEW PRICE
                         │
                         ▼
                    PLACE ORDER
                         │
                ┌────────┴────────┐
                ▼                 ▼
             ONLINE            OFFLINE
             PAYMENT           PAYMENT
                │                 │
                └────────┬────────┘
                         ▼
                  ORDER RECEIVED
                         │
                         ▼
                    CUTTING
                         │
                         ▼
                    STITCHING
                         │
                         ▼
                   TRIAL READY
                         │
                         ▼
                  TRIAL IMAGE
                         │
                         ▼
                   EMAIL CUSTOMER
                         │
                         ▼
                  CUSTOMER TRIAL
                         │
                ┌────────┴────────┐
                ▼                 ▼
            APPROVED           ALTERATION
                │                 │
                │                 ▼
                │          FINAL STITCHING
                │                 │
                └────────┬────────┘
                         ▼
                  READY FOR DELIVERY
                         │
                         ▼
                     DELIVERED
                         │
                         ▼
                    COMPLETED
```

---

# 33. Admin End-to-End Flow

```text
ADMIN LOGIN
    ↓
ADMIN DASHBOARD
    │
    ├── Customers
    │      ├── Add
    │      ├── Modify
    │      ├── Search
    │      └── Orders
    │
    ├── Measurements
    │      ├── Add
    │      ├── Modify
    │      └── History
    │
    ├── Designs
    │      ├── Add
    │      ├── Modify
    │      ├── Price
    │      └── Images
    │
    ├── Orders
    │      ├── View
    │      ├── Modify
    │      ├── Status
    │      ├── Payment
    │      └── Trial
    │
    ├── Gallery
    │
    ├── Reports
    │
    └── Settings
           ├── Logo
           ├── Brand Image
           ├── Website
           ├── Pricing
           └── Contact Details
```

---

# 34. Validation Requirements

Strong validation should be implemented throughout the application.

### Customer

- Mobile mandatory
- Mobile unique
- Valid email format
- Password validation

### Measurement

- Numeric validation where applicable
- Maximum/minimum reasonable values
- Required fields based on design
- No invalid negative values

### Order

- Design must be active
- Customer must be active
- Measurement must exist where required
- Delivery date validation
- Price must be calculated by system

### Payment

- Payment amount cannot exceed total order amount
- Pending amount cannot become negative
- Duplicate payment reference should be prevented
- Payment status must be controlled

### Image Upload

- Allowed extensions
- Maximum file size
- Unique file name
- Invalid/corrupted image rejection

---

# 35. Security Requirements

The application should include:

- Secure password hashing
- Session management
- HTTPS
- SQL injection protection
- Input validation
- CSRF protection
- Role-based authorization
- Secure file upload
- File extension validation
- Maximum upload size
- Protection against unauthorized image access
- Admin session timeout
- Login attempt protection
- Audit logging

Customer should never be able to access another customer's order by manipulating an Order ID.

---

# 36. Recommended Additional Features

The following features are recommended to make the application production-ready.

## 36.1 Customer Profile

Customer can maintain:

- Name
- Mobile
- Email
- Address
- Preferred communication method

## 36.2 WhatsApp Integration

Future enhancement:

```text
Order Status
      ↓
WhatsApp Notification
```

Useful for:

- Order received
- Trial ready
- Ready for delivery
- Delivery reminder

## 36.3 SMS Notification

Can be added later if required.

## 36.4 Email Notification

Automatic emails for:

- Order confirmation
- Payment confirmation
- Trial invitation
- Ready for delivery
- Order completion

## 36.5 Order Cancellation

Admin-controlled cancellation with:

- Cancellation reason
- Cancellation date
- Refund status

## 36.6 Alteration Management

If customer requests alteration during trial:

```text
TRIAL
 ↓
ALTERATION REQUIRED
 ↓
ALTERATION
 ↓
RE-TRIAL
 ↓
APPROVED
```

The system should maintain alteration history.

## 36.7 Customer Feedback

After completion:

```text
Order Completed
      ↓
Customer Feedback
      ↓
Rating + Comment
```

## 36.8 Reports

Admin reports:

- Daily Orders
- Monthly Orders
- Revenue
- Pending Payments
- Completed Orders
- Cancelled Orders
- Upcoming Deliveries
- Customer-wise Orders
- Design-wise Orders
- Payment Report

Reports should support:

- Search
- Date filter
- Export to Excel/CSV/PDF where required

> **Current implementation note**: `Admin > Reports` currently shows
> Orders by Status, Design-wise Orders & Revenue, Daily Revenue (last 14
> days) and Pending Payments. Monthly Orders, a dedicated Customer-wise
> Orders report, a standalone Payment Report and Excel/CSV/PDF export
> are not yet implemented (the underlying queries in
> `app/admin.py::reports` are straightforward to extend for these).

---

# 37. Backup & Recovery

MS SQL database must have a defined backup strategy.

Recommended:

```text
Database
   ↓
Daily Backup
   ↓
Backup Storage
   ↓
Retention Policy
```

Image files should also be backed up because order-related images are business data.

Database and image backups should be tested periodically for restoration.

---

# 38. Error Handling

User-friendly errors should be displayed.

Example:

Instead of:

```text
SQL Exception 500
```

Display:

```text
Unable to save customer details.
Please try again or contact the administrator.
```

Technical errors should be recorded in application logs.

---

# 39. Logging

Application logs should contain:

- Date/Time
- Module
- User
- Request
- Error
- Exception
- Order ID where applicable
- API response where applicable
- Processing time

Sensitive information such as passwords must never be logged.

---

# 40. Acceptance Criteria

The application will be considered functionally complete when:

### Customer

- Customer can register successfully.
- Duplicate mobile number is prevented.
- Customer can login.
- Customer can view designs.
- Customer can view pricing.
- Customer can enter/update measurements.
- Customer can place an order.
- Unique Order ID is generated.
- Customer can make/select payment option.
- Customer can track order.
- Customer can view order history.

### Admin

- Admin can login securely.
- Admin can add/modify customers.
- Admin can manage measurements.
- Admin can manage designs.
- Admin can manage prices.
- Admin can manage orders.
- Admin can update order status.
- Admin can select delivery date.
- Admin can upload trial image.
- Send Trial Message remains unavailable until trial image is uploaded.
- Admin can send customer email.
- Email activity is logged.
- Admin can manage website images.
- Dashboard displays correct order/payment statistics.

### Database

- Transactional data is stored in MS SQL.
- Unique customer mobile number is enforced.
- Unique Order ID is enforced.
- Historical order measurements are preserved.
- Payment calculations are accurate.
- Status history is maintained.
- Audit records are maintained.

---

# 41. Key Business Rules

| Rule ID | Business Rule |
|---|---|
| BR-001 | Mobile number is mandatory for customer registration. |
| BR-002 | Mobile number must be unique. |
| BR-003 | One customer can have multiple orders. |
| BR-004 | One customer can maintain multiple measurement versions. |
| BR-005 | Every order must have a unique Order ID. |
| BR-006 | Order must retain the measurement version used during order creation. |
| BR-007 | Total Amount is system calculated. |
| BR-008 | Pending Amount = Total Amount - Amount Received. |
| BR-009 | Payment amount cannot exceed the order amount. |
| BR-010 | Only authorized admin users can change order status. |
| BR-011 | Trial notification can only be sent when a valid trial image exists. |
| BR-012 | Customer can only view their own orders. |
| BR-013 | Historical order price should not change when design pricing is modified. |
| BR-014 | Historical order measurements should not change when customer updates current measurements. |
| BR-015 | Deleted customer/order records should preferably be soft-deleted where business history must be retained. |
| BR-016 | All important admin modifications must be audited. |
| BR-017 | All uploaded images must have unique server-generated names. |
| BR-018 | Images should not be stored only in the database; image metadata/path should be stored in SQL. |
| BR-019 | Delivery date cannot normally be earlier than the order date. |
| BR-020 | Order status must follow the configured workflow. |
| BR-021 | Order-status-triggered customer emails (beyond the trial invite) are sent automatically only for statuses the admin has explicitly enabled in Website Settings (opt-in per status, e.g. Order Received). |
| BR-022 | Admin may permanently ("hard") delete an order together with its images, payments, status history and email logs - a deliberate exception to BR-015's soft-delete preference, used for correcting mistaken/test orders. Every delete is written to the audit trail. |

---

# 42. Recommended Final Menu Structure

## Public Website

```text
Home
About Us
Designs
Gallery
Pricing
How It Works
Contact Us
Login
Sign Up
Track Order
```

## Customer Dashboard

```text
Dashboard
My Profile
My Measurements
Browse Designs
My Orders
Payments
Track Order
Notifications
Order History
Logout
```

## Admin Dashboard

```text
Dashboard
Customers
Measurements
Designs
Gallery
Orders
Payments
Trial Management
Deliveries
Reports
Website Management
Settings
Audit Logs
Logout
```

---

# 43. Recommended Development Phases

## Phase 1 – Foundation

- Python application
- IIS hosting
- MS SQL connection
- Login/registration
- Customer management
- Basic UI
- Security

## Phase 2 – Core Tailoring

- Measurement module
- Design module
- Gallery
- Pricing
- Customer dashboard

## Phase 3 – Order Management

- Order creation
- Order ID
- Order workflow
- Delivery calendar
- Payment management
- Admin dashboard

## Phase 4 – Trial & Communication

- Trial image upload
- Image management
- Gmail API
- Email templates
- Email logs

## Phase 5 – Reporting & Enhancement

- Reports
- Excel/PDF export
- Audit logs
- Alteration management
- Customer feedback
- Notifications

## Phase 6 – Production Hardening

- HTTPS
- Backup
- Error monitoring
- Security testing
- Performance testing
- UAT
- Production deployment

---

# 44. Final End-to-End Business Flow

```text
                    CUSTOMER
                       │
                       ▼
                 VISIT WEBSITE
                       │
              ┌────────┴────────┐
              ▼                 ▼
            LOGIN             SIGN UP
              │                 │
              └────────┬────────┘
                       ▼
                CUSTOMER PROFILE
                       │
                       ▼
             CHECK MEASUREMENT
                 /          \
              EXISTS       NOT EXISTS
                │              │
                │       ENTER MEASUREMENT
                │              │
                └──────┬───────┘
                       ▼
                 VIEW DESIGNS
                       │
                       ▼
              SELECT CUSTOMISATION
                       │
                       ▼
                  CALCULATE PRICE
                       │
                       ▼
                  PLACE ORDER
                       │
                       ▼
               GENERATE ORDER ID
                       │
              ┌────────┴────────┐
              ▼                 ▼
          ONLINE PAYMENT    OFFLINE PAYMENT
              │                 │
              └────────┬────────┘
                       ▼
                 ORDER RECEIVED
                       │
                       ▼
                    CUTTING
                       │
                       ▼
                   STITCHING
                       │
                       ▼
                  TRIAL READY
                       │
                       ▼
               ADMIN UPLOADS IMAGE
                       │
                       ▼
              SEND EMAIL TO CUSTOMER
                       │
                       ▼
                CUSTOMER ATTENDS
                    TRIAL
                       │
                ┌──────┴──────┐
                ▼             ▼
             APPROVED      ALTERATION
                │             │
                │             ▼
                │          RE-TRIAL
                │             │
                └──────┬──────┘
                       ▼
                 FINAL STITCHING
                       │
                       ▼
                READY FOR DELIVERY
                       │
                       ▼
                    DELIVERED
                       │
                       ▼
                   COMPLETED
                       │
                       ▼
               CUSTOMER FEEDBACK
```

---

# 45. Conclusion

The proposed system will provide a complete digital workflow for managing a tailoring business, eliminating the dependency on manual records and providing centralized management of customers, measurements, designs, orders, payments, trial images, delivery dates and customer communication.

The architecture will use:

**Python + IIS + MS SQL Server + Structured File Storage + Gmail API**

with a modular design that allows future migration to other hosting environments and integration with additional payment, WhatsApp, SMS or cloud services.

The most important design principles are:

1. **MS SQL as the source of truth for business data**
2. **Unique Customer and Order identification**
3. **Version-controlled customer measurements**
4. **Historical order data must never change unintentionally**
5. **Controlled order-status workflow**
6. **Unique and structured image storage**
7. **Secure customer/admin authentication**
8. **Complete payment tracking**
9. **Trial image → email notification dependency**
10. **Audit trail for important admin actions**
11. **Responsive modern customer website**
12. **Modular architecture for future hosting and feature expansion**

---

# 46. Implementation Status & Changes (v1.1)

This section reflects the state of the actual codebase (`app/*.py`, `templates/`,
`database/schema_*.sql`) as of this update, and should be read alongside
Sections 1-45 above (the original v1.0 specification), which remain the
baseline design intent. Where the two disagree, this section describes
what is actually built.

## 46.1 Fully implemented as specified

- Customer registration/login with mandatory unique mobile number, optional
  email/name (Section 6) and the first-time-measurement branching logic
  (Section 7, Scenarios A/B).
- Separate admin login with failed-login lockout and session timeout
  (Section 8).
- Admin dashboard KPIs, today's/upcoming deliveries (Section 9).
- Customer management: add/search/view/modify/activate-deactivate,
  view a customer's orders/measurements (Section 10).
- Versioned measurements - every order stores the measurement snapshot
  used at creation time; later edits never change historical orders
  (Sections 11 & 29, BR-006/BR-014).
- Blouse design catalogue with pricing, images and Active/Inactive status;
  historical order prices are unaffected by later price edits (Section 12,
  BR-013).
- Gallery module with category, description, display order and
  active/inactive flag (Section 13).
- Order creation with design → measurement → customisation → price →
  delivery date → payment option → confirm, unique never-reused order
  numbers in the `ORD<YYYYMMDD><seq>` format (Section 14, BR-005).
- Pricing/payment rules: pending = total - received, system-calculated,
  payment cannot exceed the order's pending amount, duplicate payment
  references are blocked (Sections 15/16, BR-007/008/009).
- Full order status workflow with history (previous/new status, remarks,
  updated by, timestamp) and admin-only status changes (Sections 17/18,
  BR-010).
- Trial flow gated on an uploaded trial image before the "Send Trial
  Message" action is available (Sections 19/20, BR-011).
- Order tracking (public, by order number) and customer order history
  (Sections 22/23).
- Delivery date management with same-day capacity limit
  (`MAX_ORDERS_PER_DAY`) (Section 24, BR-019).
- Admin order list/detail with all documented actions (view, status,
  payment, trial, email, cancel, history) (Section 25).
- Admin settings for brand/logo/contact/about-us content (Section 26).
- Audit log capturing admin user, action, module, record, old/new value,
  timestamp and IP address (Section 27, BR-016).
- Database structure matches the recommended entity list (Section 28) in
  both `schema_sqlite.sql` and `schema_mssql.sql`; both engines are driven
  through the same parameterised-query layer (`app/db.py`) with no
  engine-specific application code (Section 2/31).

## 46.2 Enhancements beyond the original v1.0 scope

- **Configurable automatic status emails (partial delivery of Section
  36.4).** Admin > Settings has an "Email Triggers" list of order
  statuses (e.g. `ORDER_RECEIVED`); when a status is checked there, every
  order that reaches it automatically emails the customer, in addition to
  the trial invite. This is data-driven (stored in
  `website_settings.email_trigger_statuses`), not hard-coded, so admin can
  enable/disable per status without a code change. See BR-021.
- **Trial email now attaches the trial image itself**, automatically
  downscaled/re-compressed to JPEG (via Pillow, optional dependency; the
  original file is sent unmodified if Pillow isn't installed) so a large
  phone photo doesn't stall the send.
- **Background/asynchronous email sending.** Both the trial invite and
  status-change emails are dispatched on a background thread so the
  admin's HTTP request returns immediately; the outcome is still recorded
  in `email_logs` once the send completes (or fails).
- **SMTP resilience.** The SMTP backend retries a failed send up to three
  times with backoff, and works around a common Windows DNS problem
  (broken IPv6-only resolution) by forcing IPv4 lookups for the SMTP
  connection.
- **Admin "walk-in" combined flow.** `Admin > Measurements > New` lets
  admin enter a mobile number plus measurement values in a single step -
  if no customer exists with that mobile it is created automatically,
  otherwise the measurement is added as a new version for the existing
  customer. Avoids a separate "create customer first" trip for in-person
  visits.
  - **Note**: `app/admin.py::quick_measurement` intentionally starts with
    the mobile/measurement fields and creates the customer inline; if a
    reviewer expects a strict two-step "create customer, then add
    measurement" flow, that remains available separately via
    `Admin > Customers > Add` followed by `Add Measurement`.
- **Customer-side reference image upload.** Customers can attach their
  own reference photo to an order (`CustomerReference` image type),
  visible to admin on the order detail screen - not only admin-uploaded
  trial/order images as implied by the original Section 3 folder diagram.
- **Hard delete of an order.** In addition to Cancel (which keeps the
  order record per BR-015's soft-delete guidance), admin can permanently
  delete an order and all related images (removed from disk too),
  payments, status history and email logs. This is an intentional,
  audited exception to BR-015 for removing mistaken/test/duplicate
  orders - see BR-022. There is no undo.
- **Individual trial image removal.** Admin can delete a specific trial
  image (file + soft-deleted DB row) without deleting the whole order,
  e.g. to remove an accidental upload before sending the trial email.
- **Installable web app (PWA).** The public site ships a dynamic
  `manifest.webmanifest` (reflecting the brand name from Settings) and a
  service worker (`static/js/sw.js`) so it can be installed to a phone's
  home screen or desktop like a native app. This requires HTTPS in
  production (see `docs/AZURE_IIS_DEPLOYMENT.md`).
- **MS SQL Server identity handling.** Inserts on SQL Server retrieve the
  new row's identity via `SCOPE_IDENTITY()` in the same batch as the
  `INSERT` (with `SET NOCOUNT ON`) to avoid an intermittent NULL result
  that a separate follow-up call can otherwise produce - this only
  affects the `mssql` engine internally and needs no application-level
  awareness.

## 46.3 Known deviations / things to double-check before production

- **`config.py`'s default `DB_ENGINE` is `mssql`**, with a specific local
  developer machine name (`MSSQL_SERVER`) as its default value, rather
  than defaulting to the zero-setup `sqlite` engine described in the
  Quick Start docs. Set `DB_ENGINE`/`MSSQL_*` explicitly via environment
  variables (or `.env`) for any environment other than that original
  developer's machine.
- **Real-looking SMTP credentials (`SMTP_USERNAME`, `SMTP_PASSWORD`,
  `EMAIL_FROM`) are hard-coded as defaults in `config.py`.** Per Section
  35 (Security Requirements), secrets must not live in source - move
  these to environment variables/`.env` (already `.gitignore`d) and
  rotate (regenerate) that Gmail app password, since it has been present
  in a plain source file.
- **BR-022 (hard order delete)** is a deliberate, audited exception to
  BR-015's general soft-delete preference; confirm this is acceptable for
  your business's record-retention requirements (e.g. tax/audit
  obligations) before relying on it in production, or restrict it to a
  more senior admin role if one is introduced later.
- **`config.py`'s `MAX_LOGIN_ATTEMPTS` setting is currently unused.**
  Admin lockout (Section 8) is implemented with its own hard-coded
  `MAX_ATTEMPTS = 5` / `LOCKOUT_MINUTES = 15` constants in
  `app/auth.py`, not wired to this config value - update `app/auth.py`
  directly (or wire it to the config setting) if you need this
  configurable.
- **Section 28's "recommended" table list is intentionally consolidated
  in the actual schema.** Both `schema_sqlite.sql` and `schema_mssql.sql`
  implement 12 tables (`admin_users`, `customers`, `measurements`,
  `designs`, `gallery`, `orders`, `order_status_history`, `payments`,
  `order_images`, `email_logs`, `website_settings`, `audit_logs`).
  There are no separate `MeasurementDetails`, `DesignImages`,
  `OrderItems`, `OrderMeasurements` or `PaymentTransactions` tables as
  named in Section 28 - those fields are folded directly into
  `measurements`, `designs`, `orders` and `payments` respectively, since
  this application only sells one line item (a blouse) per order.
- `database/MSSQL.sql` is an SSMS-generated snapshot of the schema and
  duplicates `database/schema_mssql.sql` (the maintained source); treat
  the latter as authoritative.
- **No live payment gateway or customer-side payment reference upload**
  (Section 16). Customers only choose a payment mode when ordering;
  admin records the actual payment (amount/mode/reference/status)
  afterwards via the order detail screen.
- **"Edit" / "Update Measurement" / "Update Design" on an existing order
  (Section 25) are intentionally not implemented** - allowing them would
  break BR-006/BR-013/BR-014's guarantee that an order keeps the exact
  design price and measurement snapshot used when it was placed.
  Status, payment, trial, delivery date, cancel and (hard) delete are
  the only supported per-order admin actions.
- **Reports (Section 36.8) are partially implemented.** Orders by
  Status, Design-wise Orders & Revenue, Daily Revenue (14 days) and
  Pending Payments exist; Monthly Orders, Customer-wise Orders, a
  standalone Payment Report and Excel/CSV/PDF export do not yet exist.
- **Customer detail screen (Section 10) does not show a consolidated
  payment/trial history** across all of a customer's orders - each is
  viewed per-order instead.
- **Home page (Section 5) omits a distinct "Services" section and a
  "Customer Reviews" section** (reviews aren't implemented at all - see
  Section 36.7 status below). It does include Hero/About Us, Featured
  Designs, Customisation Gallery and a "How It Works" summary.