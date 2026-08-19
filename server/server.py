from flask import Flask, request, jsonify
import json
import datetime
import os

app = Flask(__name__)

LICENSE_FILE = "licenses.json"

# -------------------------
# ライセンス生成
# -------------------------
@app.route("/api/generate_license", methods=["POST"])
def generate_license():
    data = request.get_json()
    user_id = data.get("UserId")
    purchase_type = data.get("PurchaseType")

    # ライセンスキー生成
    prefix = "SUB" if purchase_type == "subscription" else "PERM"
    license_key = f"{prefix}-{datetime.datetime.now().strftime('%H%M%S')}"

    # 有効期限設定
    expires = (datetime.datetime.now() + datetime.timedelta(days=365)).isoformat() \
        if purchase_type == "subscription" else None

    new_license = {
        "UserId": user_id,
        "LicenseKey": license_key,
        "Type": purchase_type,
        "Expires": expires,
        "IsValid": True
    }

    # 既存ライセンスを読み込み
    if os.path.exists(LICENSE_FILE):
        with open(LICENSE_FILE, "r", encoding="utf-8") as f:
            licenses = json.load(f)
    else:
        licenses = {"licenses": []}

    # 新しいライセンスを追加
    licenses["licenses"].append(new_license)

    # 保存
    with open(LICENSE_FILE, "w", encoding="utf-8") as f:
        json.dump(licenses, f, indent=4)

    # アプリに返す
    return jsonify({
        "LicenseKey": license_key,
        "Type": purchase_type,
        "Expires": expires,
        "IsValid": True
    })


# -------------------------
# サブスク延長
# -------------------------
@app.route("/api/extend_subscription", methods=["POST"])
def extend_subscription():
    data = request.get_json()
    license_key = data.get("LicenseKey")
    extend_years = data.get("ExtendYears", 1)

    with open(LICENSE_FILE, "r", encoding="utf-8") as f:
        licenses = json.load(f)

    for lic in licenses["licenses"]:
        if lic["LicenseKey"] == license_key and lic["Type"] == "subscription":
            current_exp = datetime.datetime.fromisoformat(lic["Expires"])
            new_exp = current_exp + datetime.timedelta(days=365 * extend_years)
            lic["Expires"] = new_exp.isoformat()
            break

    with open(LICENSE_FILE, "w", encoding="utf-8") as f:
        json.dump(licenses, f, indent=4)

    return jsonify({
        "LicenseKey": license_key,
        "Expires": lic["Expires"],
        "IsValid": True
    })


# -------------------------
# サブスク確認
# -------------------------
@app.route("/api/check_subscription", methods=["GET"])
def check_subscription():
    license_key = request.args.get("licenseKey")

    with open(LICENSE_FILE, "r", encoding="utf-8") as f:
        licenses = json.load(f)

    for lic in licenses["licenses"]:
        if lic["LicenseKey"] == license_key:
            return jsonify({
                "LicenseKey": license_key,
                "Expires": lic.get("Expires"),
                "IsValid": lic.get("IsValid", False)
            })

    return jsonify({"error": "License not found"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
