# app/api.py

from flask import Flask, request, jsonify
from assisstant import get_product_info
from pydantic import ValidationError

# Initialize the Flask app
app = Flask(__name__)

# Define the POST endpoint
@app.route("/product-info", methods=["POST"])
def product_info():
    try:
        # Get JSON input from request
        data = request.get_json()
        if not data or "product" not in data:
            return jsonify({"error": "Missing 'product' in request body"}), 400

        # Extract product name
        product_name = data["product"]

        # Call your assistant to get product info
        product_info = get_product_info(product_name)

        # Return the response as JSON
        return jsonify(product_info.model_dump()), 200

    except ValidationError as ve:
        return jsonify({"error": "Validation failed", "details": ve.errors()}), 422
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run only if this file is executed directly
if __name__ == "__main__":
    app.run(debug=True)
