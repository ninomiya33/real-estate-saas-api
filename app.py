# app.py
from flask import Flask, request, jsonify, render_template_string, make_response
from flask_cors import CORS
import joblib
import os
# import weasyprint
from datetime import datetime

# Flask アプリ作成
app = Flask(__name__)
CORS(app, resources={r"/predict": {"origins": "http://localhost:3000"}, r"/generate_pdf": {"origins": "http://localhost:3000"}})

# モデルが保存されているディレクトリ
MODEL_DIR = './models'

@app.route('/')
def index():
    return "🏡 Real Estate Prediction API is running!"

# /predict API
@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()

        city_code = data.get('city_code')
        features = data.get('features')

        print("---- AI査定リクエスト受信 ✅ ----")
        print("city_code:", city_code)
        print("features:", features)

        if not city_code or not features:
            return jsonify({"error": "Missing city_code or features"}), 400

        model_path = os.path.join(MODEL_DIR, f"real_estate_model_{city_code}.pkl")
        print("モデルパス:", model_path)

        if not os.path.exists(model_path):
            return jsonify({"error": f"Model for city_code {city_code} not found"}), 404

        model = joblib.load(model_path)

        prediction = model.predict([features])[0]

        return jsonify({
            "city_code": city_code,
            "predicted_price": round(prediction, 2)
        }), 200

    except Exception as e:
        print("予測エラー:", str(e))
        return jsonify({"error": str(e)}), 500

# /generate_pdf API
@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    try:
        data = request.get_json()

        print("---- PDF生成リクエスト受信 ✅ ----")
        print(data)

        html_template = """
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                h1 { color: #2c3e50; }
                .section { margin-bottom: 20px; }
                .label { font-weight: bold; }
            </style>
        </head>
        <body>
            <h1>ご売却支援査定提案書</h1>
            <p>日付: {{ date }}</p>

            <div class="section">
                <h2>物件情報</h2>
                <p><span class="label">所在地:</span> {{ property_info.address }}</p>
                <p><span class="label">土地面積:</span> {{ property_info.land_area_sqm }} m²</p>
                <p><span class="label">建物面積:</span> {{ property_info.building_area_sqm }} m²</p>
                <p><span class="label">築年:</span> {{ property_info.building_year }}</p>
                <p><span class="label">構造:</span> {{ property_info.structure }}</p>
            </div>

            <div class="section">
                <h2>査定結果</h2>
                <p><span class="label">AI査定価格:</span> {{ predicted_price }} 円</p>
                <p><span class="label">売出ご提案価格:</span> {{ proposed_price_range.min_price }} 円 〜 {{ proposed_price_range.max_price }} 円</p>
            </div>

            <div class="section">
                <h2>AI市場流通性判定</h2>
                <p>{{ ai_market_liquidity }}</p>
            </div>

            <div class="section">
                <h2>ご提案・媒介契約・費用</h2>
                <p>（ここにテンプレート文面が入ります）</p>
            </div>

        </body>
        </html>
        """

        rendered_html = render_template_string(
            html_template,
            date=datetime.now().strftime("%Y-%m-%d"),
            property_info=data.get('property_info', {}),
            predicted_price=data.get('predicted_price', 0),
            proposed_price_range=data.get('proposed_price_range', {}),
            ai_market_liquidity=data.get('ai_market_liquidity', '未判定')
        )

        # ★ 今は weasyprint コメントアウトしているので仮PDFデータを返す
        pdf = "PDF生成は現在コメントアウト中（weasyprint有効化してね）".encode('utf-8')

        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename="real_estate_estimate.pdf"'

        return response

    except Exception as e:
        print("PDF生成エラー:", str(e))
        return jsonify({"error": str(e)}), 500

# アプリ起動設定（Railway / Heroku / Vercel でもOK対応版）
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
