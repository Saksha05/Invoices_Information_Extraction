from flask import Flask,request,jsonify,render_template
from PIL import Image
import numpy as np
from langchain_google_genai import ChatGoogleGenerativeAI
import json
import io
import pytesseract
from dotenv import load_dotenv
import os

load_dotenv()

google_api_key = os.getenv("GOOGL_API_KEY")




app = Flask(__name__)

def extract_text_from_file(file):
    """Extract text from uploaded file"""
    try:

        file_bytes = file.read()
        image = Image.open(io.BytesIO(file_bytes))


        gray_image = image.convert("L")


        extracted_text = pytesseract.image_to_string(gray_image).strip()

        print("Extracted Text:")
        print(extracted_text)

        return extracted_text
    except Exception as e:
        print(f"Error extracting text: {str(e)}")
        raise e

@app.route('/details', methods=['POST'])
def details():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    try:
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400


        extracted_text = extract_text_from_file(file)
        
        if not extracted_text:
            return jsonify({"error": "No text could be extracted from the image"}), 400

        message = f"""
        system: You are an invoice information extractor who extracts information from text and converts it into a JSON format with proper structure and key-value pairs.
        user: {extracted_text}
        """

        llm = ChatGoogleGenerativeAI(
            google_api_key=google_api_key,
            temperature=0.3,
            model="gemini-1.5-flash-latest"
        )

        response = llm.invoke(message)
        print("Extracted text for processing:")
        print(extracted_text)
        

        result = str(response.content)
        

        result = result.replace("```json", "").replace("```", "").strip()
        

        file_name = 'data.json'
        with open(file_name,'w') as op:
            op.write(result)

        json_data = json.loads(result)
        return jsonify(json_data)
        
    except json.JSONDecodeError as e:
        return jsonify({"error": f"Invalid JSON response from AI: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Error processing invoice: {str(e)}"}), 500
if __name__ == "__main__":
    app.run(debug=True)