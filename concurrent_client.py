import requests
import threading
import random
import time
server_url = "http://127.0.0.1:8080/sum"
num_concurrent_client = 10
def send_request(client_id):
    print(f"[client {client_id}]-> Sending requests")
    numbers = {}
    num_entities = random.randint(2,4)
    for i in range(num_entities):
        key=f"num_{i}"
        value=round(random.uniform(-100,100),2)
        numbers[key] = value
        # حالا هر کلاینت دیتای منحصربه‌فرد خود را پرینت و ارسال می‌کند
        print(f"[Client {client_id}]-> Sending payload:{numbers}")
    try: 
        response = requests.post(server_url,json=numbers,timeout=10)
        response_data = response.json()
        if response.status_code == 200:
            # اگر موفق بود، خودِ "sum" را نمایش بده
            print(f"[Client {client_id}]<- Recieved SUM: {response_data['sum']} (Status: 200)")
        else:
            # اگر سرور خطا داد (مثلا خطای 400)، "error" را نمایش بده
            print(f"[Client {client_id}]<- Recieved ERROR: {response_data['error']} (Status: {response.status_code})")
    
    except requests.exceptions.JSONDecodeError:
        # این اتفاق زمانی می‌افتد که سرور خطای 405 یا 500 بدهد و HTML برگرداند
        print(f"[Client {client_id}]!!! Error: Could not decode JSON. Server response: {response.text}")
    except requests.exceptions.RequestException as e:
        # خطاهای اتصال (مثل Connection refused)
        print(f"[Client {client_id}]!!!error {e} ]")
if __name__== "__main__":
    print(f"--- Simulating {num_concurrent_client} concurrent clients ---")
    threads=[]
    for i in range(num_concurrent_client):
        thread = threading.Thread(target=send_request,args=(i,))
        threads.append(thread)
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    print("--- All concurrent requests completed. ---")          
