# THE COMPLETE AFFORDMED BACKEND GUIDE
### For Absolute Beginners — Every Click, Every Step

---

## PHASE 0 — THE NIGHT BEFORE

---

### 0.1 — Check If Everything Is Installed

Click the **Windows key** (bottom left of keyboard) → type `cmd` → press **Enter**.

A black window opens. This is your Command Prompt. Type each line below and press Enter after each one:

```
node --version
```
✅ Good: shows something like `v20.11.0`
❌ Bad: says "not recognized" → go to nodejs.org → click the big green "LTS" download button → install it → restart CMD → try again

```
npm --version
```
✅ Good: shows a number like `10.2.4`
❌ Bad: says "not recognized" → npm comes with Node, so reinstall Node

```
git --version
```
✅ Good: shows `git version 2.x.x`
❌ Bad: says "not recognized" → go to git-scm.com → download → install with all default options → restart CMD → try again

```
git config --global user.name "Your Full Name"
git config --global user.email "your@college.edu"
```
No output = success. This tells git who you are.

---

### 0.2 — Set Up GitHub Personal Access Token

Without this, git push will fail tomorrow asking for a password that doesn't work.

1. Open your browser → go to **github.com** → log in
2. Click your **profile picture** (top right corner)
3. Click **Settings**
4. Scroll all the way down the left sidebar → click **Developer settings**
5. Click **Personal access tokens** → click **Tokens (classic)**
6. Click **Generate new token** → click **Generate new token (classic)**
7. In the "Note" field type: `exam`
8. Expiration: select **7 days**
9. Checkboxes: tick the box next to **repo** (this selects all repo permissions)
10. Scroll down → click **Generate token**
11. You see a long string starting with `ghp_...`

📸 **SCREENSHOT THIS PAGE RIGHT NOW** — you cannot see this token again after closing the page.

12. Open Notepad → paste the token there → save the file as `token.txt` on your Desktop

---

### 0.3 — Verify Postman Works

1. Open Postman
2. Click **+** to open a new tab
3. Make sure it says **GET** in the dropdown on the left
4. In the URL bar type: `https://jsonplaceholder.typicode.com/posts/1`
5. Click **Send**
6. You should see JSON appear in the bottom panel

✅ If you see JSON → Postman works → proceed
❌ If nothing happens or error → reinstall Postman from postman.com

---

### 0.4 — Pre-Install Your Packages Tonight

In CMD, type these one line at a time:

```
cd C:\Users\YourWindowsUsername
```
⚠️ Replace `YourWindowsUsername` with your actual Windows username. To find it, look at what comes before the `>` in CMD. Example: if you see `C:\Users\rahul>` then your username is `rahul`.

```
mkdir practice
cd practice
mkdir q1
cd q1
npm init -y
npm install express axios dotenv
```

You'll see a lot of text downloading. Wait until it finishes and you see your cursor again.

✅ Success looks like: `added 57 packages` or similar
❌ If you see `npm ERR!` → paste the error here

---

## PHASE 1 — EXAM MORNING (8:00 AM – 9:00 AM)

---

### 1.1 — What to Open Before 9 AM

Open all of these and keep them open:

1. **CMD** — Windows key → type `cmd` → Enter
2. **VSCode** — find it in Start menu or Desktop
3. **Postman** — find it in Start menu or Desktop
4. **Browser** → open **github.com** → make sure you're logged in
5. **Notepad** → open a blank one for saving credentials
6. Plug in your **charger**
7. **Check your email** — at exactly 9:00 AM you get an email with the test link and your Access Code

---

### 1.2 — When the Email Arrives at 9:00 AM

- Open the test document from the link
- **Read both questions fully before touching the keyboard** (10 minutes)
- Find your **Access Code** in the email — it looks like `IKOLJE` — copy it to Notepad immediately

---

## PHASE 2 — THE 3 HOURS (9:00 AM – 12:00 PM)

---

### STEP 1 — Create Your Folder (9:10 AM)

In CMD, type these one by one:

```
cd C:\Users\YourWindowsUsername
```
⚠️ Same as before — use your actual Windows username

```
mkdir 👈YOURROLLNUMBER👈
cd 👈YOURROLLNUMBER👈
mkdir q1
mkdir q2
cd q1
npm init -y
npm install express axios dotenv
```
⚠️ `👈YOURROLLNUMBER👈` = your actual college roll number e.g. `21BCE1234`

Wait for packages to install. When cursor returns → done.

Now open VSCode:
1. Open VSCode
2. Click **File** → **Open Folder**
3. Navigate to `C:\Users\YourWindowsUsername\👈YOURROLLNUMBER👈`
4. Click **Select Folder**

You'll see your folder open in the left panel of VSCode.

---

### STEP 2 — Create .gitignore File (9:15 AM)

In VSCode left panel:
1. Click on the `q1` folder to expand it
2. Click the **New File** icon (looks like a page with a + sign, appears when you hover over the folder name)
3. Type exactly: `.gitignore` → press Enter

The file opens. Type this inside it:

```
node_modules/
.env
.DS_Store
*.log
```

Press `Ctrl+S` to save.

---

### STEP 3 — Create .env File (9:16 AM)

Same as above — right click `q1` folder → New File → name it `.env`

Type this inside:

```
PORT=3000
TEST_SERVER=http://20.244.56.144/test
COMPANY_NAME=
CLIENT_ID=
CLIENT_SECRET=
OWNER_EMAIL=
```

Leave the values after `=` blank for now. Press `Ctrl+S` to save.

---

### STEP 4 — Register on Their Server (9:20 AM)

Open Postman.

1. Click the **+** button to open a new request tab
2. Click the dropdown that says **GET** → change it to **POST**
3. In the URL bar type: `http://20.244.56.144/test/register`
4. Click the **Body** tab (below the URL bar)
5. Click the **raw** radio button
6. On the right side of that row, click the dropdown that says **Text** → change it to **JSON**
7. In the big text area below, type this:

```json
{
  "companyName": "anyname",
  "ownerName": "👈YourFullName👈",
  "rollNo": "👈YOURROLLNUMBER👈",
  "ownerEmail": "👈your@college.edu👈",
  "accessCode": "👈CODEFROMYOUREMAIL👈"
}
```

⚠️ Replace every 👈...👈 with your actual values:
- `companyName` = make up any simple name like `mystore`
- `ownerName` = your actual full name
- `rollNo` = your college roll number
- `ownerEmail` = your college email address
- `accessCode` = the code from the exam email you received at 9 AM

8. Click **Send**

Response will appear in the bottom panel. It looks like:

```json
{
  "companyName": "anyname",
  "clientID": "37664332-7343-4749-8675-2146696735",
  "clientSecret": "HVIE",
  "ownerName": "Your Name",
  "ownerEmail": "your@college.edu"
}
```

📸 **SCREENSHOT THIS POSTMAN WINDOW RIGHT NOW** — full screen, showing the response clearly.

9. Open your Notepad → copy `clientID` value → paste it → new line → copy `clientSecret` value → paste it → save

---

### STEP 5 — Fill In Your .env File (9:22 AM)

Go back to VSCode → open `.env` file → fill in the values:

```
PORT=3000
TEST_SERVER=http://20.244.56.144/test
COMPANY_NAME=👈samecompanynameyouused👈
CLIENT_ID=👈pasteclientIDhere👈
CLIENT_SECRET=👈pasteclientSecrethere👈
OWNER_EMAIL=👈your@college.edu👈
```

Press `Ctrl+S` to save.

---

### STEP 6 — Verify Auth Works (9:24 AM)

In Postman → click **+** for new tab → method: **POST**

URL: `http://20.244.56.144/test/auth`

Body → raw → JSON:

```json
{
  "companyName": "👈samenameasregister👈",
  "clientID": "👈yourclientID👈",
  "clientSecret": "👈yourclientSecret👈",
  "ownerEmail": "👈your@college.edu👈"
}
```

Click **Send**. Response:

```json
{
  "token_type": "Bearer",
  "access_token": "a-very-long-string",
  "expires_in": 1718835258
}
```

📸 **SCREENSHOT THIS** — shows auth working.

✅ You see access_token → proceed
❌ You see 401 error → your clientID or clientSecret is wrong → re-check your .env

---

### STEP 7 — Verify Their Product API Works (9:27 AM)

In Postman → new tab → method: **GET**

URL:
```
http://20.244.56.144/test/companies/AMZ/categories/Laptop/products/top-5/minPrice-1/maxPrice-10000
```

Click **Headers** tab → click the empty row at the bottom of the table → type:
- Key: `Authorization`
- Value: `Bearer ` (then paste your access_token after the space)

Click **Send**. You should see a JSON array of laptops.

📸 **SCREENSHOT THIS** — shows their server is working.

✅ You see products → start writing your server
❌ You see 401 → your token expired → go back to Step 6 and get a new one

---

### STEP 8 — Create Your Server File (9:30 AM)

In VSCode:
1. Right click the `q1` folder in left panel
2. Click **New File**
3. Name it `index.js` → Enter

The file opens. Now type this entire code — **type it, don't copy paste, you need to know it**:

```javascript
const express = require('express');
const axios = require('axios');
require('dotenv').config();

const app = express();
app.use(express.json());

// LOGGING MIDDLEWARE — mandatory, must come before routes
app.use((req, res, next) => {
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.url}`);
  next();
});

// CONFIG
const TEST_SERVER = process.env.TEST_SERVER;

// 👈 THESE ARE THE EXACT COMPANY CODES FROM THE PDF 👈
const COMPANIES = ['AMZ', 'A', 'F', 'HYN', 'WAL'];

const CACHE_TTL = 60 * 1000; // cache for 60 seconds

// TOKEN CACHE — so we dont call auth every single request
let cachedToken = null;
let tokenExpiry = 0;

async function getToken() {
  // reuse token if still valid with 30 second safety buffer
  if (cachedToken && Date.now() < tokenExpiry - 30000) {
    return cachedToken;
  }
  const res = await axios.post(`${TEST_SERVER}/auth`, {
    companyName: process.env.COMPANY_NAME,
    clientID: process.env.CLIENT_ID,
    clientSecret: process.env.CLIENT_SECRET,
    ownerEmail: process.env.OWNER_EMAIL
  });
  cachedToken = res.data.access_token;
  // expires_in is a unix timestamp in seconds, convert to milliseconds
  tokenExpiry = res.data.expires_in * 1000;
  return cachedToken;
}

// FETCH PRODUCTS FROM ONE COMPANY
async function fetchFromCompany(company, category, n, minPrice, maxPrice) {
  try {
    const token = await getToken();
    // NOTE: path params not query params — /top-5/minPrice-1/maxPrice-10000
    const url = `${TEST_SERVER}/companies/${company}/categories/${category}/products/top-${n}/minPrice-${minPrice}/maxPrice-${maxPrice}`;
    const res = await axios.get(url, {
      headers: { Authorization: `Bearer ${token}` },
      timeout: 5000
    });
    // add company name to each product
    return res.data.map(p => ({ ...p, company }));
  } catch (err) {
    // if one company fails, dont crash — return empty array
    console.error(`[${company}] failed: ${err.message}`);
    return [];
  }
}

// PRODUCT CACHE — reduces calls to their server
const productCache = new Map();

// PRODUCT STORE — for get by ID to work
const productStore = new Map();

async function getCachedProducts(category, n, minPrice, maxPrice) {
  const key = `${category}-${n}-${minPrice}-${maxPrice}`;
  const hit = productCache.get(key);
  // return cached data if still fresh
  if (hit && Date.now() - hit.timestamp < CACHE_TTL) {
    return hit.data;
  }
  // call all 5 companies at the same time (parallel)
  const results = await Promise.all(
    COMPANIES.map(c => fetchFromCompany(c, category, n, minPrice, maxPrice))
  );
  const data = results.flat(); // merge all arrays into one
  productCache.set(key, { data, timestamp: Date.now() });
  return data;
}

// GENERATE STABLE UNIQUE ID — no external library needed
function generateId(productName, company, price) {
  const raw = `${company}|${productName}|${price}`;
  let hash = 0;
  for (let i = 0; i < raw.length; i++) {
    hash = ((hash << 5) - hash) + raw.charCodeAt(i);
    hash |= 0; // convert to 32 bit integer
  }
  return Math.abs(hash).toString(36);
}

// SORT WITHOUT EXTERNAL LIBRARY — rules say no external algo libraries
function sortProducts(products, sortBy, order) {
  const valid = ['rating', 'price', 'discount', 'company'];
  const key = valid.includes(sortBy) ? sortBy : 'rating';
  const arr = [...products];
  // insertion sort
  for (let i = 1; i < arr.length; i++) {
    const cur = arr[i];
    let j = i - 1;
    while (j >= 0) {
      const a = arr[j][key];
      const b = cur[key];
      let shouldSwap;
      if (typeof a === 'string') {
        shouldSwap = order === 'asc'
          ? a.localeCompare(b) > 0
          : a.localeCompare(b) < 0;
      } else {
        shouldSwap = order === 'asc' ? a > b : a < b;
      }
      if (shouldSwap) { arr[j + 1] = arr[j]; j--; }
      else break;
    }
    arr[j + 1] = cur;
  }
  return arr;
}

// ROUTE 1 — GET /categories/:categoryname/products
app.get('/categories/:categoryname/products', async (req, res) => {
  try {
    const { categoryname } = req.params;
    const n        = parseInt(req.query.n)        || 10;
    const page     = parseInt(req.query.page)     || 1;
    const sortBy   = req.query.sortBy             || 'rating';
    const order    = req.query.order              || 'desc';
    const minPrice = parseInt(req.query.minPrice) || 1;
    const maxPrice = parseInt(req.query.maxPrice) || 100000;

    // get products from cache or fresh fetch
    let products = await getCachedProducts(categoryname, n, minPrice, maxPrice);

    // add unique id to each product and save for lookup
    products = products.map(p => {
      const id = generateId(p.productName, p.company, p.price);
      const full = { ...p, id };
      productStore.set(id, full);
      return full;
    });

    // sort
    products = sortProducts(products, sortBy, order);

    // pagination only kicks in when n > 10
    if (n > 10) {
      const start = (page - 1) * n;
      return res.json({
        page,
        total: products.length,
        totalPages: Math.ceil(products.length / n),
        products: products.slice(start, start + n)
      });
    }

    return res.json({ products: products.slice(0, n) });

  } catch (err) {
    console.error('Error in route 1:', err.message);
    res.status(500).json({ error: err.message });
  }
});

// ROUTE 2 — GET /categories/:categoryname/products/:productid
app.get('/categories/:categoryname/products/:productid', (req, res) => {
  const product = productStore.get(req.params.productid);
  if (!product) {
    return res.status(404).json({
      error: 'Product not found. Call /categories/:name/products first.'
    });
  }
  res.json(product);
});

// HEALTH CHECK — quickly verify server is alive
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    productsStored: productStore.size,
    tokenActive: !!cachedToken
  });
});

// START SERVER
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
```

Press `Ctrl+S` to save.

---

### STEP 9 — Start Your Server (10:00 AM)

Go to CMD. Make sure you're in the q1 folder. Type:

```
node index.js
```

✅ You see: `Server running on http://localhost:3000`
❌ You see an error → read the line number it mentions → go fix that line in VSCode → save → try again

**Leave this CMD window open and running. Do not close it.**

Open a second CMD window for testing (Windows key → cmd → Enter).

---

### STEP 10 — Test All Routes in Postman (10:00 AM onward)

**Test 1 — Health check**

Postman → new tab → GET

URL: `http://localhost:3000/health`

Click Send.

📸 **SCREENSHOT** when you see `{"status":"ok",...}`

---

**Test 2 — Basic product fetch**

GET `http://localhost:3000/categories/Laptop/products?n=5&minPrice=1&maxPrice=10000`

Click Send. You should see products array with `id` field on each product.

📸 **SCREENSHOT** — make sure response time shows at bottom right of Postman (it shows something like `832 ms`)

---

**Test 3 — Sort by price ascending**

GET `http://localhost:3000/categories/Phone/products?n=10&sortBy=price&order=asc`

Click Send. Check that prices go from lowest to highest.

📸 **SCREENSHOT**

---

**Test 4 — Pagination (n must be more than 10)**

GET `http://localhost:3000/categories/TV/products?n=15&page=1`

Click Send. Response should have `page`, `total`, `totalPages`, `products`.

📸 **SCREENSHOT**

GET `http://localhost:3000/categories/TV/products?n=15&page=2`

Click Send. Different products, same structure.

📸 **SCREENSHOT**

---

**Test 5 — Get product by ID**

From the Test 2 response, find any product and copy its `id` value. It looks like `a3f9b2`.

GET `http://localhost:3000/categories/Laptop/products/PASTEIDHERE`

Click Send. You should see that single product's details.

📸 **SCREENSHOT**

---

**Test 6 — 404 for fake ID**

GET `http://localhost:3000/categories/Laptop/products/fakeid999`

Click Send. You should see `{"error":"Product not found..."}`

📸 **SCREENSHOT**

---

### STEP 11 — Save Screenshots (11:15 AM)

In VSCode:
1. Right click `q1` folder → New Folder → name it `screenshots`
2. Move all your screenshots into this folder

Name them clearly:
```
test1-health.png
test2-basic-fetch.png
test3-sort-price.png
test4-pagination-page1.png
test4-pagination-page2.png
test5-get-by-id.png
test6-404-error.png
```

---

### STEP 12 — Create GitHub Repo (11:30 AM)

1. Open browser → github.com → logged in
2. Click the **+** icon top right → **New repository**
3. Repository name: type your **exact roll number** e.g. `21BCE1234`
4. Click **Public** (not Private)
5. Do NOT tick "Add a README file"
6. Click **Create repository**
7. You see a page with setup instructions — copy the URL that looks like `https://github.com/yourusername/21BCE1234.git`

---

### STEP 13 — Push to GitHub (11:32 AM)

In CMD, navigate to your roll number folder (one level up from q1):

```
cd C:\Users\YourWindowsUsername\👈YOURROLLNUMBER👈
```

Then run these one by one:

```
git init
```
✅ Shows: `Initialized empty Git repository`

```
git add .
```
No output = good

```
git status
```
📸 **SCREENSHOT THIS** — read it carefully. You must NOT see `node_modules` in the list. If you do → your .gitignore has a problem → fix it before continuing.

```
git commit -m "backend microservice submission"
```
✅ Shows files being committed

```
git branch -M main
```
No output = good

```
git remote add origin https://github.com/yourusername/👈YOURROLLNUMBER👈.git
```
⚠️ Use your actual GitHub username and roll number

```
git push -u origin main
```
When it asks for username → type your GitHub username → Enter

When it asks for password → paste your Personal Access Token from Notepad → Enter

(Note: when pasting the token you won't see it appear — that's normal, just paste and press Enter)

✅ Shows: `Branch 'main' set up to track remote branch 'main'`

---

### STEP 14 — Verify on GitHub (11:40 AM)

Open your repo in browser: `https://github.com/yourusername/YOURROLLNUMBER`

Check every single one of these:

- [ ] Repo name = your roll number exactly ✅
- [ ] Set to Public ✅
- [ ] `q1/` folder visible ✅
- [ ] `q1/index.js` visible ✅
- [ ] `q1/screenshots/` folder with all images ✅
- [ ] `q1/.gitignore` visible ✅
- [ ] `node_modules/` folder is NOT there ✅
- [ ] `.env` file is NOT there ✅
- [ ] Everything on `main` branch (check the dropdown top left of file list) ✅
- [ ] No mention of "Affordmed" anywhere ✅

📸 **SCREENSHOT YOUR GITHUB REPO PAGE** — proof of submission

---

### STEP 15 — Fill Google Form (11:45 AM)

The Google Form link is in your exam email. Open it. Fill everything. Submit before 12:00.

📸 **SCREENSHOT the form confirmation page** after submitting.

---

## PHASE 3 — IF YOU PASS: INTERVIEW ANSWERS

**"Why Promise.all?"**
Sequential awaits = wait for company 1, then 2, then 3... total time = sum of all 5. Promise.all = all 5 fire at the same time, total time = slowest one. 5x faster.

**"Why cache the token?"**
Every auth call costs time and an API call. Token stays valid for several minutes. I cache it and reuse it — only refresh when it's about to expire.

**"One company goes down?"**
Each company call has its own try/catch. If it fails I return empty array for that company. Other 4 still work. User gets a response.

**"How is the ID stable?"**
Hash of company + product name + price. Deterministic — same inputs always produce same output. Same product always gets same ID.

**"Why insertion sort?"**
Rules say no external algorithm libraries. I wrote this myself. Shows I understand sorting, not just that I can call a library.

**"What's your caching strategy?"**
60 second TTL. After 60 seconds next request fetches fresh data from all companies. Balances cost reduction vs data freshness — companies can update data and within 60 seconds users see the new data.

---

## INSTANT DISQUALIFICATION LIST

- `node_modules` pushed to GitHub
- `.env` pushed to GitHub
- Wrong branch (must be `main`)
- Repo name is anything other than exact roll number
- "Affordmed" mentioned in repo name, README, or commits
- Used someone else's clientID or clientSecret
- No screenshots
- Google Form not submitted
- Incomplete code

---

## EXACT VALUES (memorize — from the PDF)

**Their server:** `http://20.244.56.144`

**Companies:** 👈`AMZ`, `A`, `F`, `HYN`, `WAL`👈 *(changes every exam)*

**Categories:** 👈`Phone`, `Computer`, `TV`, `Earphone`, `Tablet`, `Charger`, `House`, `Keypad`, `Bluetooth`, `Pendrive`, `Remote`, `Speaker`, `Headset`, `Laptop`👈 *(verify in your actual question paper)*

**Their product API format:**
```
GET http://20.244.56.144/test/companies/👈COMPANY👈/categories/👈CATEGORY👈/products/top-👈N👈/minPrice-👈MIN👈/maxPrice-👈MAX👈
```
⚠️ These are path parameters not query parameters — the `/top-5/minPrice-1/maxPrice-10000` part is IN the URL path, not after a `?`

**Register:** `POST http://20.244.56.144/test/register`

**Auth:** `POST http://20.244.56.144/test/auth`

---
