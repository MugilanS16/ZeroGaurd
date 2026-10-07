# ZeroGuard AI — Cybercrime Reporting & Threat Intelligence Platform

ZeroGuard AI is a full-stack cybercrime reporting and evidence preservation platform with real-time AI assistance, dynamic legal question generation, official complaint PDF drafting, two-step SMS/WhatsApp OTP verification, emergency guardian alerts, and tamper-evident SHA-256 audit ledger logging.

---

## 📱 Setting up SMS & WhatsApp OTP Verification

ZeroGuard AI features a provider-agnostic messaging architecture supporting **Twilio**, **MSG91** (India-optimized), and **Console (Dev)** modes.

### 1. Provider Configuration

Choose your messaging provider in `.env` using `MESSAGING_PROVIDER`:

```bash
# Option A: Zero-cost Local Dev (Prints OTP directly to server terminal)
MESSAGING_PROVIDER=console

# Option B: Twilio (Global SMS & WhatsApp)
MESSAGING_PROVIDER=twilio
TWILIO_ACCOUNT_SID=ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# Option C: MSG91 (DLT-compliant SMS & WhatsApp for India)
MESSAGING_PROVIDER=msg91
MSG91_AUTH_KEY=your_msg91_auth_key
MSG91_SENDER_ID=ZEROGD
MSG91_INTEGRATED_NUMBER=919876543210
```

---

### 🇮🇳 India-Specific Telecom (DLT) & Meta WhatsApp Requirements

1. **SMS Distributed Ledger Technology (DLT)**:
   - In accordance with Telecom Regulatory Authority of India (TRAI) guidelines, all commercial SMS traffic requires pre-registered Entity IDs, Header/Sender IDs, and approved Content Templates.
   - Set the following variables in `.env`:
     - `DLT_ENTITY_ID`: Your registered Principal Entity ID (e.g., `1101452367890123456`).
     - `DLT_SENDER_ID`: Your approved 6-character Alpha Header (e.g., `ZEROGD`).
     - `DLT_TEMPLATE_ID_OTP`: Approved OTP Template ID with variable `{#var#}`.
     - `DLT_TEMPLATE_ID_GUARDIAN`: Approved Guardian Alert Template ID.
2. **WhatsApp Meta-Approved HSM Templates**:
   - Outbound WhatsApp notifications initiated by the platform must utilize Meta-approved message templates.
   - **Authentication Template** (`zeroguard_otp_verification`): One-time password verification with copy-code button.
   - **Utility Template** (`zeroguard_guardian_alert`): Sanitized emergency case notifications.
3. **Automatic Channel Fallback**:
   - When a user selects WhatsApp, if delivery fails or is rejected, ZeroGuard AI automatically retries delivery over SMS with zero latency penalty.
   - Email OTP is preserved as an optional last-resort fallback behind `OTP_EMAIL_FALLBACK=false` (default disabled).
4. **Data Privacy by Design**:
   - Phone numbers are normalized to E.164 (default Region: `+91`).
   - Logging strictly masks phone numbers (`+91******3210`) and omits raw OTP codes.
   - Guardian notifications **never** contain victim narratives, monetary figures, or evidence files.
   - Every message includes a `STOP` opt-out path that revokes guardian consent immediately upon receipt.

---

## 🏛️ Architecture & Tech Stack
- **Frontend**: React 19 + TypeScript + Tailwind CSS, Vite, React Router, and Axios (`/frontend`).
- **Backend**: Python Flask REST API with SQLite (`zeroguard.db`), Flask-SQLAlchemy 2.0 (`Mapped` / `mapped_column`), Flask-Limiter, Flask-JWT-Extended, Flask-Migrate, and Flask-CORS (`app.py`).
- **Messaging Layer**: Provider-agnostic abstraction under `backend/services/messaging/` (`TwilioProvider`, `MSG91Provider`, `ConsoleProvider`).
- **Security Engine**: 6-digit numeric OTP generated via `secrets`, HMAC-SHA256 hashing, 5-minute expiry, 5-attempt locking, 30s resend cooldown, 5/hr rate limits, and constant-time comparison.
- **Audit System**: Real-time user action tracking (`activity_logs`) with SHA-256 hash chaining ledger and authentication security monitoring (`login_history`).

---

## 🚀 Running the Project

### 1. Start the Flask Backend (Port 5000)
```powershell
python app.py
```

### 2. Start the Vite React Frontend (Port 5173)
```powershell
cd frontend
npm run dev
```

### 3. Run Automated Pytest Suite
```powershell
pytest tests/ -v
```

---

## 🔑 REST API 2FA & Guardian Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/auth/otp/send` | Send 6-digit OTP via SMS or WhatsApp with rate limits |
| `POST` | `/api/auth/otp/verify` | Constant-time HMAC OTP verification & JWT issuance |
| `POST` | `/api/auth/otp/resend` | 30-second cooldown resend challenge |
| `GET` | `/api/guardian` | List enrolled emergency guardians |
| `POST` | `/api/guardian` | Add/update guardian (requires consent flag) & trigger verification |
| `POST` | `/api/guardian/verify` | Verify guardian phone number via OTP |
| `DELETE` | `/api/guardian/:id` | Remove guardian |
| `POST` | `/api/webhooks/messaging` | Delivery status callbacks & inbound STOP opt-out handling |

---

## 🛡️ Demo Credentials
- **Citizen Account**: `citizen@cybercrime.gov.in` / `CitizenPass123!` (Mobile: `+919876543210`)
- **Admin Account**: `admin@cybercrime.gov.in` / `AdminPass123!` (Mobile: `+919876500000`)
- **Dev Mode**: When `MESSAGING_PROVIDER=console`, OTPs are printed directly in the backend terminal.
