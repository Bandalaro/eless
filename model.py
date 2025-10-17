import os
from sentence_transformers import SentenceTransformer

# 1. Define the model name and the local folder path
# The model name for MiniLM embedding model v2 is 'all-MiniLM-L6-v2'
MODEL_NAME = 'all-MiniLM-L6-v2'
LOCAL_PATH = './models/minilm_v2_local' # The folder where the model will be saved

# 2. Download and load the model from Hugging Face Hub (this is the download step)
# This step automatically handles downloading all necessary files.
print(f"Downloading and loading model: {MODEL_NAME}...")
try:
    model = SentenceTransformer(MODEL_NAME)
    print("Model loaded successfully.")
except Exception as e:
    print(f"Error loading model: {e}")
    exit()

# 3. Save the model locally to the specified folder
print(f"Saving model to local directory: {LOCAL_PATH}...")
os.makedirs(LOCAL_PATH, exist_ok=True) # Ensure the directory exists
model.save(LOCAL_PATH)
print("Model saved successfully.")

# You can now load the model locally without an internet connection using:
# local_model = SentenceTransformer(LOCAL_PATH)
# print(f"Model loaded locally from: {LOCAL_PATH}")