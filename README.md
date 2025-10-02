# location-image-tracker
⚠️ For educational purposes only. Do not use to track anyone without their informed consent
profile
Qwen3-Max
7:31 pm
Here's a professional and clear README.md for your GitHub repository with strong ethical warnings:

Location Image Tracker
A FastAPI-based web application that requests the user's geolocation with explicit consent before displaying an image. If the user allows location access, their coordinates (latitude, longitude, accuracy, and timestamp) are logged server-side.

✅ This project is strictly for educational and ethical demonstration purposes only. 

⚠️ WARNING: ETHICAL & LEGAL USE ONLY
This tool must NEVER be used to track, spy on, or collect location data from anyone without their full knowledge and explicit consent.
Using this script to deceive users (e.g., sending fake image links to secretly obtain location) is:
🚫 Illegal under privacy laws (including India’s IT Act, GDPR, and DPDP Act 2023),
🚫 A violation of human rights and digital ethics,
🚫 Potentially punishable by fines or imprisonment.
You are fully responsible for how you use this code.
The author (GitHub: @python-hacked) is NOT liable for any misuse, illegal activity, or harm caused by third parties.
🔍 Important: Modern browsers only share location if the user clicks "Allow". This script cannot bypass browser security. Any attempt to trick users into granting access may leave digital traces (IP logs, server records, browser fingerprints), making misuse easily traceable. 

📌 How It Works
You place an image in static/images/.
Share a link like: https://location-image-tracker.onrender.com/view/download.jpg
The recipient sees a page asking them to click "Allow & View".
Only if they manually allow location, their coordinates are sent to your server and logged.
The image is shown regardless of their choice.
🛠️ Setup
bash


1
2
pip install fastapi uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000
Place images in: static/images/
Location logs: locations_log.jsonl

📜 License
This project is open-source for learning and ethical research only.
Do not deploy this in production or use it against real users without informed consent.

🔐 Remember: With great power comes great responsibility.
Respect privacy. Always ask. Never deceive. 

✅ Author: Not affiliated with any malicious activity.
✅ GitHub: @python-hacked — Educational projects only.
