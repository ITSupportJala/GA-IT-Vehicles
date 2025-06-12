from flask import Flask, render_template, request, send_file
from sistem import get_token, get_vehicle_data, get_vehicle_detail, get_full_mileage_data
import pandas as pd
import io

app = Flask(__name__)

@app.route("/")
def index():
    token = get_token()
    plates = []
    if token:
        vehicles = get_vehicle_data(token)
        if vehicles:
            plates = [v['plate'] for v in vehicles if v.get('plate')]
    return render_template("index.html", plate_list=plates)

@app.route("/detail", methods=["POST"])
def detail():
    token = get_token()
    error = None
    detail = None
    plate_list = []
    plate_input = request.form.get("plate", "").upper()

    if token:
        vehicles = get_vehicle_data(token)
        if vehicles:
            plate_list = [v['plate'] for v in vehicles if v.get('plate')]
            found = next((v for v in vehicles if v.get('plate','').upper() == plate_input), None)
            if found:
                detail = get_vehicle_detail(token, found['imei'])
                if detail:
                    detail["plate"] = plate_input
                else:
                    error = "Detail kendaraan tidak ditemukan."
            else:
                error = f"Plat '{plate_input}' tidak ditemukan."
        else:
            error = "Data kendaraan tidak tersedia."
    else:
        error = "Gagal mendapatkan token."

    return render_template("index.html", plate_list=plate_list, detail=detail, error=error)

@app.route("/mileage", methods=["GET", "POST"])
def mileage():
    token = get_token()
    error = None
    imei_list = []
    mileage_data = []
    selected_imei = None
    start_date = None
    end_date = None

    if token:
        vehicles = get_vehicle_data(token)
        if vehicles:
            imei_list = [{"imei": v["imei"], "plate": v.get("plate", "")} for v in vehicles]

        if request.method == "POST":
            selected_imei = request.form.get("imei")
            start_date = request.form.get("start_date")
            end_date = request.form.get("end_date")

            if not selected_imei:
                error = "Silakan pilih IMEI."
            elif not start_date or not end_date:
                error = "Silakan masukkan tanggal mulai dan tanggal akhir."
            else:
                mileage_data = get_full_mileage_data(token, selected_imei, start_date, end_date)
                if not mileage_data:
                    error = "Data mileage tidak ditemukan untuk rentang tanggal tersebut."
    else:
        error = "Gagal mendapatkan token."

    return render_template("mileage.html",
                           imei_list=imei_list,
                           detail=mileage_data,
                           error=error,
                           selected_imei=selected_imei,
                           start_date=start_date,
                           end_date=end_date)

@app.route("/all-data")
def all_data():
    token = get_token()
    data = []
    error = None

    if token:
        vehicles = get_vehicle_data(token)
        if vehicles:
            data = vehicles
        else:
            error = "Data kendaraan tidak tersedia."
    else:
        error = "Gagal mendapatkan token."

    return render_template("all_data.html", data=data, error=error)

@app.route("/export-all-data")
def export_all_data():
    token = get_token()
    if not token:
        return "Gagal mendapatkan token.", 500

    vehicles = get_vehicle_data(token)
    if not vehicles:
        return "Data kendaraan kosong.", 404

    df = pd.DataFrame(vehicles)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Kendaraan")
    output.seek(0)

    return send_file(output,
                     as_attachment=True,
                     download_name="data_kendaraan.xlsx",
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if __name__ == "__main__":
    app.run(debug=True)