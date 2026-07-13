# ☁️ NutriCloud - Serverless Multi-User Nutrition & Stock Planner with Google Drive Sync

NutriCloud is a modern, single-page serverless web application designed to help users calculate custom nutritional goals, manage kitchen inventory, plan daily meals based on actual stock, and log their progress over time.

Built on a 100% decentralized, privacy-first architecture, NutriCloud has no backend database. Instead, it utilizes Google Identity Services (OAuth2) and the Google Drive API to securely save and load the user's profile and inventory as a single private file (`nutricloud_data.json`) inside their personal Google Drive.

Anyone can clone this single-file HTML application, host it for free (e.g., on GitHub Pages), input their own Google Client ID, and run a private, multi-device SaaS instantly.

## ✨ Features

* **🩺 Dynamic Biomarker & Macro Calculator**: Computes Basal Metabolic Rate (BMR) and Total Daily Energy Expenditure (TDEE) using the Mifflin-St Jeor equation. Calculates personalized macronutrient targets based on customizable caloric deficits or surpluses.
* **⚡ Stock-Based Meal Planner**: Analyzes real-time inventory and designs a daily meal schedule based on available ingredients. Upon user confirmation, it automatically deducts the matching ingredient weights from the pantry and registers the consumption history.
* **📦 Real-Time Kitchen Inventory**: Fully editable inventory table tracking item categories, unit types, and available stock, with custom "low-stock" alert thresholds.
* **📊 Visual Logs & Intake History**: Track daily calorie and macro consistency over time with dynamic, responsive SVG-based charts.
* **🔒 Privacy-Focused Cloud Sync**: Reads and writes directly to the user's private Google Drive (using the highly restricted `drive.file` scope). The application cannot see any other files in your Google Drive.
* **💾 Universal Manual Backups**: Single-button manual JSON export and import for local backups, data migrations, or offline use.

## 🛠️ Technology Stack

* **Frontend**: HTML5, CSS3, Tailwind CSS (Responsive, utility-first design).
* **Typography**: Plus Jakarta Sans.
* **Cloud & Auth Integration**:
  * Google Identity Services (GIS) (Secure OAuth2 authorization flows).
  * Google Drive API v3 (Reads/writes `nutricloud_data.json` directly from/to the client browser).
* **Architecture**: Static Single-Page Application (SPA) - zero server backend required.

## 🚀 Deployment (GitHub Pages)

Since NutriCloud is compiled entirely inside a single self-contained HTML file, hosting it online takes under a minute:

Rename the main application file (e.g., `nutricloud.html`) to `index.html`.
Push `index.html` and `README.md` to your public or private GitHub repository:

```bash
git init
git add index.html README.md
git commit -m "Initial commit - NutriCloud"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

On GitHub, navigate to your repository's **Settings** -> **Pages**.
Under Build and deployment, select **Deploy from a branch**, choose `main` and the `/ (root)` folder, then click Save.
(Optional) Add your custom domain under the Custom domain section on the same settings page and configure your DNS records with your registrar.

## 🔑 How to Generate your Google Client ID

To activate automatic cloud synchronization on your hosted instance of NutriCloud, you must generate a free Client ID from Google. This guarantees that your users' data goes straight from their browser to their Google Drive with no middleman.

### Step 1: Create a Project in Google Cloud
1. Go to the Google Cloud Console.
2. Log in with any Google Account and create a new project (e.g., "NutriCloud").

### Step 2: Configure the OAuth Consent Screen
1. In the left sidebar, navigate to **APIs & Services** -> **OAuth consent screen**.
2. Select **External** as the User Type and click Create.
3. Fill in the app registration details (App name, support emails) and click Save and Continue.
4. In the Scopes section, click Add or Remove Scopes and add this specific scope:
   `https://www.googleapis.com/auth/drive.file`
   *(This highly restricted scope ensures that NutriCloud can ONLY read and write files it created itself. Your general Drive contents remain completely invisible to the app).*
5. Under Test Users, add your own Google email address (this is required if you keep the app in "Testing" mode).

### Step 3: Create OAuth Client Credentials
1. Go to **Credentials** in the left sidebar.
2. Click **+ Create Credentials** -> **OAuth client ID**.
3. Under Application type, select **Web application**.
4. Under Authorized JavaScript origins, click **+ Add URI** and add:
   * Your local test environment (e.g., `http://localhost`, `http://127.0.0.1` or `file://`).
   * Your live production domain (e.g., `https://yourdomain.com` or `https://username.github.io`).
5. Click **Create**.

### Step 4: Link to NutriCloud
1. Copy the generated Client ID (a long string ending in `.apps.googleusercontent.com`).
2. Open your deployed NutriCloud page in your browser.
3. Go to the Cloud Settings & Backup tab, paste the Client ID into the configuration field, and click Save Client ID.
4. You can now securely click Connect Google Drive on the top header to begin automatic cloud synchronization!

## 📂 Generic Data Schema (JSON)

The structure of the sync file written to Google Drive is formatted as follows:

```json
{
  "profile": {
    "gender": "Male",
    "weight": 80.0,
    "height": 180,
    "age": 30,
    "activity": "light",
    "leanMass": 65.0,
    "bmr": 1800,
    "tdee": 2400,
    "targetCalories": 2000,
    "targetProtein": 130,
    "targetCarbs": 220,
    "targetFat": 65
  },
  "inventory": [
    { "id": 1, "name": "Brown Rice", "category": "Carbohydrates", "quantity": 1000, "unit": "g", "minQuantity": 250 }
  ],
  "logs": [
    { "date": "13 Jul 2026", "calories": 2000, "protein": 130, "carbs": 220, "fat": 65, "items": "Sample log details" }
  ]
}
```

## 🤝 Contributing
Contributions are welcome! Feel free to open issues or pull requests to improve the BMR/TDEE algorithms, propose UI components, or add localized translations.

## 📄 License
This project is licensed under the MIT License. Feel free to modify, host, or integrate it into other workflows.
