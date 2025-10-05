# 🧩 QR Code Render System

A complete QR code rendering and caching system powered by **Node.js** and **Django**.

---

## 🚀 Overview

This project contains two coordinated services:

### 🟢 1. Node Render Service (`qr-node-service/`)

* Built with **Express** and **qr-code-styling-node**
* Handles **QR code generation** with advanced styling features:

  * Custom colors
  * Rounded corners
  * Embedded logos (image or base64)
  * PNG and SVG output
* Returns either a **base64 string** or a **binary file**

### 🟣 2. Django API Service (`django-backend/`)

* Exposes a single REST API endpoint:

  ```
  POST /api/qr/
  ```
* Accepts either:

  * A direct URL (`"data": "https://example.com"`)
  * A full `options.json` (same as qr-code-styling format)
* Performs intelligent caching:

  * If the same QR was previously rendered → returns cached base64 from DB
  * Otherwise → requests the Node service → stores result in DB
* Stores images as **base64** inside the database
* Supports optional file download

---

## ⚙️ Tech Stack

| Component             | Technology                               |
| --------------------- | ---------------------------------------- |
| **Frontend/Renderer** | Node.js (Express + qr-code-styling-node) |
| **Backend API**       | Django 5.x (REST + ORM + cache)          |
| **Database**          | SQLite / PostgreSQL                      |
| **Format Support**    | PNG, SVG (base64 or binary)              |
| **Language**          | Python 3.12+, Node 18+                   |

---

## 🧩 Repository Structure

```
qr-code-render-system/
│
├── qr-node-service/         # Node QR rendering microservice
│   ├── server.js
│   ├── package.json  
│
├── django-backend/          # Django caching + API gateway
│   ├── core/
│   │   ├── models.py
│   │   ├── utils.py
│   │   ├── views.py
│   │   └── urls.py
│   ├── manage.py
│   ├── requirements.txt
│
└── README.md
```

---

## 🧰 Requirements

| Dependency | Version                       |
| ---------- | ----------------------------- |
| Python     | ≥ 3.10                        |
| Node.js    | ≥ 18                          |
| npm        | ≥ 8                           |
| Database   | SQLite (default) / PostgreSQL |

---

## 🛠️ Setup & Run

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/hosseinMsh/qr-code-render-system.git
cd qr-code-render-system
```

---

### 2️⃣ Start Node QR Render Service

```bash
cd qr-node-service
npm install
node server.js
```

✅ Output:

```
QR render service listening on :3001
```

Default port: **3001**

To change it:

```bash
PORT=8080 node server.js
```

---

### 3️⃣ Start Django API Service

```bash
cd ../django-backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8000
```

✅ Output:

```
Starting development server at http://127.0.0.1:8000/
```

---

## 🔌 Inter-Service Configuration

In `django-backend/settings.py`, configure the Node service URL:

```python
QR_NODE_URL = "http://localhost:3001/render"
```

If Node runs on another port or host, just update this URL.

---

## 🧪 API Usage Examples

### ✅ Example 1 — Simple URL Input

Django will auto-generate defaults.

```bash
curl -X POST http://localhost:8000/api/qr/ \
  -H "Content-Type: application/json" \
  -d '{
    "data": "https://masihii.ir",
    "asBase64": true,
    "download": false
  }'
```

Response:

```json
{
  "format": "png",
  "base64": "data:image/png;base64,iVBORw0K..."
}
```

---

### ✅ Example 2 — Full Options Object (like `options.json`)

```bash
curl -X POST http://localhost:8000/api/qr/ \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "data": "https://sharif.ir",
      "type": "png",
      "width": 768,
      "height": 768,
      "qrOptions": {"errorCorrectionLevel": "H"},
      "dotsOptions": {"type": "rounded", "color": "#1966ab"},
      "backgroundOptions": {"color": "#ffffff"},
      "cornersSquareOptions": {"type": "dot", "color": "#1966ab"},
      "cornersDotOptions": {"type": "dot", "color": "#1966ab"},
      "image": "data:image/png;base64,....",
      "imageOptions": {"margin": 14, "imageSize": 0.22}
    },
    "asBase64": false,
    "download": true
  }'
```

→ Django forwards request to Node
→ Node renders & returns image
→ Django stores it in DB and returns file for download.

---

## 🧠 Database Model

| Field          | Description                                       | Type            |
| -------------- | ------------------------------------------------- | --------------- |
| `options_hash` | SHA256 signature of QR options                    | `CharField`     |
| `options_json` | Full normalized QR options (merged with defaults) | `JSONField`     |
| `fmt`          | Image format (`png` or `svg`)                     | `CharField`     |
| `image_base64` | Image as base64 (data URL)                        | `TextField`     |
| `created_at`   | Timestamp                                         | `DateTimeField` |

> Each unique combination of QR options is rendered only once.

---

## 🐳 Docker Build & Run

### 🟢 Node Service Dockerfile

```Dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3001
CMD ["node", "server.js"]
```

### 🟣 Django Service Dockerfile

```Dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

### 🧩 docker-compose.yml

```yaml
version: "3"
services:
  qrnode:
    build:
      context: ./qr-node-service
    ports:
      - "3001:3001"

  django:
    build:
      context: ./django-backend
    ports:
      - "8000:8000"
    environment:
      - QR_NODE_URL=http://qrnode:3001/render
    depends_on:
      - qrnode
```

Run both together:

```bash
docker-compose up --build
```

---

## ⚙️ Services Summary

| Service             | Port   | Description                                                                         |
| ------------------- | ------ | ----------------------------------------------------------------------------------- |
| **qr-node-service** | `3001` | Renders QR codes using `qr-code-styling-node` and returns base64 / image files.     |
| **django-backend**  | `8000` | Provides the `/api/qr/` endpoint, caching results and storing them in the database. |

---

## 🧾 Example Output

| Example                                                                         | Description                                          |
| ------------------------------------------------------------------------------- | ---------------------------------------------------- |
| ![QR Example](https://qr-code-styling.com/assets/images/examples/example-2.png) | Rounded style with center logo and Sharif blue color |

---

## 🔍 Notes

* Cached QR images are reused based on the SHA256 hash of normalized options.
* Changing any style parameter automatically triggers a new render.
* If Node service is offline, Django returns a 502 error.
* You can switch to PostgreSQL for better performance.
* Each image is stored as a **data URL (base64)** inside the database.

---

## ✨ Author

**Hossein Masihi**
💻 Software Engineer — Sharif University of Technology
🌐 [masihii.ir](https://masihii.ir)
📧 [Hossein.Masihi@gmail.com](mailto:Hossein.Masihi@gmail.com)

---

Would you like me to add a **“/api/docs” Swagger-UI page** (OpenAPI spec) so you can test QR generation visually inside Django Admin / API Docs?
