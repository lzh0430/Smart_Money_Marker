# 🚀 Smart Money Follower

---

## 📖 Overview

**Smart Money Follower** is a powerful Python tool designed to track and analyze top-performing cryptocurrency wallets using the [GMGN.ai](https://gmgn.ai/) API wrapper. The project now includes a MongoDB data pipeline and REST API for comprehensive wallet analysis and data access.

---

## ✨ Key Features

- 🔍 **Discover Top Wallets**: Fetch high-performing wallets based on customizable filters like timeframe and wallet tags.
- 📈 **Analyze Trading Activity**: Monitor and evaluate wallet transactions over user-defined periods.
- 💰 **Token Insights**: Retrieve detailed token information, including USD prices for traded assets.
- 🗄️ **MongoDB Storage**: Store wallet data with timestamps for historical analysis.
- 🌐 **REST API**: HTTPS API for programmatic access to wallet data.
- 📊 **Daily Scraping**: Automated daily collection of trending SOL wallets.
- 🖥️ **Clear Data Visualization**: Present insights in a structured, easy-to-read tabulated format.

---

## 🛠️ Getting Started

### Prerequisites

- Python 3.8+
- MongoDB (local installation or MongoDB Atlas)
- SSL certificates (optional, for HTTPS server)

### 1. Clone the Repository
```bash
git clone https://github.com/yllvar/Smart_Money_Follower.git
cd Smart_Money_Follower
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure MongoDB

#### Local MongoDB Setup
```bash
# Install MongoDB (Ubuntu/Debian)
sudo apt-get install mongodb

# Start MongoDB service
sudo systemctl start mongodb

# Or start manually
mongod --dbpath /path/to/data/directory
```

#### Configuration
Edit `config.yaml` to match your MongoDB setup:
```yaml
mongodb:
  host: localhost
  port: 27017
  database: smart_money_follower
  collection: sol_wallets
  username: your_mongodb_username  # Optional: for authenticated MongoDB
  password: your_mongodb_password  # Optional: for authenticated MongoDB

scraper:
  timeframe: "7d"
  wallet_tag: "smart_degen"
  min_winrate: 0.6  # Configurable winrate threshold

server:
  host: "0.0.0.0"
  port: 8443
  ssl_certfile: null  # Path to SSL cert
  ssl_keyfile: null   # Path to SSL key
```

#### MongoDB Authentication Setup (Optional)
If you have MongoDB authentication enabled:

1. **Create a MongoDB user with read/write permissions:**
```bash
# Connect to MongoDB as admin
mongosh

# Switch to admin database
use admin

# Create user with read/write permissions
db.createUser({
  user: "<username>",
  pwd: "<password>",
  roles: [
    { role: "readWrite", db: "smart_money_follower" }
  ]
})
```

2. **Update config.yaml with your credentials:**
```yaml
mongodb:
  username: <username>
  password: <password>
  # ... other settings
```

### 4. Run the System

#### Option A: Original Scripts (Direct API Usage)
```bash
python wallet.py
# or
python smartMoney.py
```

#### Option B: New MongoDB Pipeline

1. **Run the Scraper** (collect wallet data):
```bash
python sol_wallets_scraper.py
```

2. **Start the API Server**:
```bash
python server.py
```

3. **Access the API**:
```bash
# Get all wallets
curl "http://localhost:8443/wallets"

# Get wallets with minimum winrate
curl "http://localhost:8443/wallets?min_winrate=0.7"

# Get specific wallet
curl "http://localhost:8443/wallets/ADDRESS_HERE"

# Get statistics
curl "http://localhost:8443/wallets/stats"

# Health check
curl "http://localhost:8443/health"
```

### 5. Schedule Daily Scraping

#### Using Cron (Linux/macOS)
```bash
# Edit crontab
crontab -e

# Add daily scraping at midnight
0 0 * * * /path/to/python /path/to/Smart_Money_Follower/sol_wallets_scraper.py
```

#### Using Task Scheduler (Windows)
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger to "Daily"
4. Set action to start program: `python.exe`
5. Add arguments: `C:\path\to\Smart_Money_Follower\sol_wallets_scraper.py`

---

## 📋 API Documentation

### Endpoints

#### `GET /wallets`
Retrieve wallets with optional filtering.

**Query Parameters:**
- `min_winrate` (float): Minimum winrate filter
- `limit` (int): Maximum number of results (1-1000)
- `start_date` (string): Start date filter (ISO format)
- `end_date` (string): End date filter (ISO format)

**Example:**
```bash
curl "http://localhost:8443/wallets?min_winrate=0.7&limit=50"
```

#### `GET /wallets/{address}`
Get specific wallet by address.

**Example:**
```bash
curl "http://localhost:8443/wallets/ADDRESS_HERE"
```

#### `GET /wallets/stats`
Get collection statistics.

**Example:**
```bash
curl "http://localhost:8443/wallets/stats"
```

#### `GET /health`
Health check endpoint.

---

## 📊 Example Output

See the tool in action with this sample output (Realized Profit displayed in SOL):
<p align="center">
  <img width="800" alt="Sample Output" src="https://github.com/user-attachments/assets/8f741e91-263c-45c0-888b-81ce6351d2c2" />
</p>

---

## 🔧 Configuration

### Scraper Configuration
- `timeframe`: Time period for trending wallets ("1d", "7d", "30d")
- `wallet_tag`: Wallet category filter ("smart_degen", "pump_smart", etc.)
- `min_winrate`: Minimum winrate threshold for filtering wallets

### Server Configuration
- `host`: Server host address
- `port`: Server port
- `ssl_certfile`: Path to SSL certificate (for HTTPS)
- `ssl_keyfile`: Path to SSL private key (for HTTPS)

---

## 📁 Project Structure

```
Smart_Money_Follower/
├── gmgn/                    # GMGN API client
│   ├── __init__.py
│   └── client.py
├── database/                # MongoDB integration
│   ├── __init__.py
│   ├── mongo_client.py     # MongoDB operations
│   └── models.py           # Data models
├── config.yaml             # Configuration file
├── sol_wallets_scraper.py  # Daily scraper script
├── server.py              # FastAPI HTTPS server
├── smartMoney.py          # Original analysis script
├── wallet.py              # Original wallet analyzer
└── requirements.txt       # Dependencies
```

---

## 🤝 Contributing
Interested in contributing? Fork the repository, make improvements, and submit a pull request. We welcome all contributions!

📜 License
This project is open-source and licensed under the MIT License (LICENSE). Feel free to use, modify, and distribute as you see fit!

🌟 Show Your Support
Love Smart Money Follower? Give it a ⭐ on GitHub to show your support and help others discover this tool!
<p align="center">
  Built with 💻 and ☕ by <a href="https://github.com/yllvar">yllvar</a>
</p>
