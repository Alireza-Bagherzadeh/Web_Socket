import sys
import uuid
import time
import logging
from datetime import datetime
from flask import Flask, request, jsonify, g

# --- راه‌اندازی اپلیکیشن Flask ---
app = Flask(__name__)

# --- تنظیمات لاگینگ ---
# تنظیم می‌کنیم که لاگ‌ها به جای فایل، در ترمینال (stdout) چاپ شوند
# تا Gunicorn بتواند آن‌ها را مدیریت کند.
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Middleware برای لاگ کردن ---

@app.before_request
def log_request_info():
    """قبل از هر درخواست، اطلاعات آن را لاگ می‌کند."""
    g.request_id = str(uuid.uuid4())[:8]  # یک ID کوتاه و یکتا برای درخواست
    g.start_time = time.monotonic()       # زمان شروع پردازش
    
    # دریافت IP - در زمان اجرا با Gunicorn، پراکسی را در نظر می‌گیرد
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    # دریافت بدنه (body) درخواست
    # از 'get_data' استفاده می‌کنیم تا بتوانیم بدنه خام را بخوانیم
    request_body = request.get_data(as_text=True)
    if len(request_body) > 500: # جلوگیری از لاگ کردن بدنه‌های خیلی بزرگ
        request_body = "[Body too large to log]"
    
    # فرمت لاگ مطابق با PDF [cite: 31]
    log_message = (
        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
        f"REQUEST id={g.request_id} "
        f"$ip={ip_address}$ "
        f"method={request.method} "
        f"path={request.path} "
        f"body={request_body}"
    )
    logger.info(log_message)

@app.after_request
def log_response_info(response):
    """بعد از هر درخواست، اطلاعات پاسخ را لاگ می‌کند."""
    
    # محاسبه زمان پردازش (latency)
    latency_ms = (time.monotonic() - g.start_time) * 1000
    
    # دریافت بدنه (body) پاسخ
    response_body = response.get_data(as_text=True)
    if len(response_body) > 500:
        response_body = "[Body too large to log]"

    # فرمت لاگ مطابق با PDF [cite: 32]
    log_message = (
        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
        f"RESPONSE id={g.request_id} "
        f"status={response.status_code} "
        f"body={response_body} "
        f"latency={latency_ms:.2f}ms"
    )
    logger.info(log_message)
    
    return response

# --- Endpoint اصلی برنامه ---

@app.route('/sum', methods=['POST'])
def calculate_sum():
    """
    اعداد float را از یک JSON دریافت کرده، جمع می‌زند و نتیجه را برمی‌گرداند.
    همچنین مدیریت خطای کامل برای ورودی نامعتبر را انجام می‌دهد. [cite: 15, 17, 27]
    """
    
    # ۱. بررسی کنید که آیا JSON ارسال شده یا نه
    if not request.is_json:
        return jsonify({"error": "Invalid input: Request must be JSON"}), 400

    data = request.get_json()

    # ۲. بررسی کنید که آیا JSON یک دیکشنری است
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid input: JSON data must be a dictionary"}), 400

    total_sum = 0.0
    
    # ۳. مقادیر را پردازش کنید
    if not data:
        return jsonify({"error": "Invalid input: Empty dictionary received"}), 400

    try:
        for key, value in data.items():
            # ۴. بررسی کنید که آیا مقادیر عددی هستند (float یا int)
            if not isinstance(value, (int, float)):
                raise ValueError(f"Value for key '{key}' is not a number: '{value}'")
            total_sum += float(value)
    
    except ValueError as e:
        # مدیریت خطای ورودی غیر عددی 
        return jsonify({"error": f"Invalid input: {str(e)}"}), 400
    except Exception as e:
        # خطای کلی
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

    # ارسال پاسخ موفق [cite: 18]
    return jsonify({"sum": total_sum}), 200

@app.route('/')
def health_check():
    """یک روت ساده برای بررسی سلامت سرور."""
    return "Server is running."

# --- اجرای سرور ---
if __name__ == '__main__':
    # توجه: این بخش فقط برای تست مستقیم فایل پایتون است.
    # برای اجرای نهایی و مدیریت همزمانی، از Gunicorn استفاده کنید.
    print("--- Running in DEBUG mode. Use Gunicorn for production. ---")
    app.run(debug=True, port=8000)