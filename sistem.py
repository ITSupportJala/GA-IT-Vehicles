import requests, time, os
from datetime import datetime, timedelta

# Kredensial login
username = os.environ.get("GPS_USERNAME")
password = os.environ.get("GPS_PASSWORD")

# Cache token dan waktu kedaluwarsa (dalam detik)
_token_cache = {
    "token": None,
    "expires_at": 0  # epoch time
}

# Fungsi ambil token autentikasi
def get_token():
    now = time.time()
    if _token_cache["token"] and now < _token_cache["expires_at"]:
        return _token_cache["token"]

    url = "https://portal.gps.id/backend/seen/public/login"
    payload = {"username": username, "password": password}
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        result = response.json()
        token = result.get("message", {}).get("data", {}).get("token")

        if token:
            # Simpan token dan set masa berlaku 55 menit (buffer dari 60 menit)
            _token_cache["token"] = token
            _token_cache["expires_at"] = now + (55 * 60)
            return token
        else:
            print("❌ Token tidak ditemukan dalam respons.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Gagal mendapatkan token: {e}")
        return None

# Fungsi ambil daftar semua kendaraan
def get_vehicle_data(token):
    url = "https://portal.gps.id/backend/seen/public/vehicle"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        return response.json().get("message", {}).get("data", [])

    except requests.exceptions.RequestException as e:
        print(f"❌ Error mengambil data kendaraan: {e}")
        return []

# Fungsi ambil detail kendaraan berdasarkan IMEI
def get_vehicle_detail(token, imei):
    url = f"https://portal.gps.id/backend/seen/public/vehicle/detail/{imei}"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        detail = response.json().get("message", {}).get("data", {})
        return detail if isinstance(detail, dict) else None

    except requests.exceptions.RequestException as e:
        print(f"❌ Error mengambil detail kendaraan untuk IMEI {imei}: {e}")
        return None

# Fungsi ambil data mileage untuk rentang waktu tertentu (maksimal 7 hari)
def get_mileage_data(token, imei, start_date, end_date):
    url = "https://portal.gps.id/backend/seen/public/data/mileage"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "imei": imei,
        "start_date": start_date,
        "end_date": end_date
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        data = response.json().get("message", {}).get("data", [])
        if not data:
            print(f"⚠️ Data mileage kosong dari {start_date} sampai {end_date}")
        return data

    except requests.exceptions.RequestException as e:
        print(f"❌ Gagal mengambil data mileage: {e}")
        return []

# Fungsi ambil mileage penuh dengan pagination mingguan
def get_full_mileage_data(token, imei, start_date, end_date):
    all_data = []
    try:
        current_start = datetime.strptime(start_date, "%Y-%m-%d")
        final_end = datetime.strptime(end_date, "%Y-%m-%d")

        while current_start <= final_end:
            current_end = min(current_start + timedelta(days=6), final_end)

            mileage_chunk = get_mileage_data(
                token,
                imei,
                current_start.strftime("%Y-%m-%d"),
                current_end.strftime("%Y-%m-%d")
            )

            if mileage_chunk:
                if isinstance(mileage_chunk, list):
                    all_data.extend(mileage_chunk)
                else:
                    all_data.append(mileage_chunk)

            current_start = current_end + timedelta(days=1)

        return all_data 

    except ValueError as ve:
        print(f"❌ Format tanggal tidak valid: {ve}")
        return []   
    