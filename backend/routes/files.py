import os
import logging
from flask import request, jsonify
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
import docx
import pandas as pd
from PIL import Image
import pytesseract
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()  
# Initialize logging
logger = logging.getLogger(__name__)

# Supported file extensions
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'csv', 'jpg', 'jpeg', 'png', 'txt'}

# File path to save the FAISS index
FAISS_INDEX_PATH = 'faiss_index'

openai_api = os.getenv('OPENAI_API_KEY')
# Initialize the vector store (FAISS) with the OpenAI embeddings
embedding = OpenAIEmbeddings(openai_api_key=openai_api)

# Load the FAISS index if it exists, otherwise create a placeholder
if os.path.exists(FAISS_INDEX_PATH):
    logger.info("Loading existing FAISS index.")
    vectorstore = FAISS.load_local(FAISS_INDEX_PATH, embedding, allow_dangerous_deserialization=True)

else:
    logger.info("Creating new FAISS index placeholder.")
    vectorstore = None  # Initialize as None and create when data is available

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_pdf(file_path):
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def parse_docx(file_path):
    doc = docx.Document(file_path)
    text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
    return text

def parse_csv(file_path):
    df = pd.read_csv(file_path)
    return df.to_string()

def parse_image(file_path):
    img = Image.open(file_path)
    text = pytesseract.image_to_string(img)
    return text

def parse_text(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def handle_file_upload():
    global vectorstore  # Declare vectorstore as global to modify it within the function

    try:
        # Check if the request contains the file part
        if 'file' not in request.files:
            return jsonify({"error": "No file part in the request"}), 400

        file = request.files['file']

        # If the user does not select a file, the browser may submit an empty file without a filename
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join('/tmp', filename)
            file.save(file_path)

            # Parse the file based on its extension
            if filename.endswith('.pdf'):
                content = parse_pdf(file_path)
            elif filename.endswith('.docx'):
                content = parse_docx(file_path)
            elif filename.endswith('.csv'):
                content = parse_csv(file_path)
            elif filename.endswith(('.jpg', '.jpeg', '.png')):
                content = parse_image(file_path)
            elif filename.endswith('.txt'):
                content = parse_text(file_path)
            else:
                return jsonify({"error": "Unsupported file type"}), 400

            # Initialize FAISS vectorstore if it's not already created
            if vectorstore is None:
                vectorstore = FAISS.from_texts([content], embedding)
            else:
                # Add the new content to the existing FAISS index
                vectorstore.add_texts([content], metadatas=[{'filename': filename}])

            # Save the updated FAISS index
            vectorstore.save_local(FAISS_INDEX_PATH)

            logger.info(f"File {filename} uploaded and processed successfully.")
            return jsonify({"message": f"File {filename} uploaded and processed successfully"}), 200

        else:
            return jsonify({"error": "Unsupported file type"}), 400

    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return jsonify({"error": "An error occurred while uploading the file"}), 500
