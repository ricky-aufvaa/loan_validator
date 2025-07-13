#predefined path constants

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_PATH = os.path.join(BASE_DIR,"..", "data", "DSCR-Quick-Reference.pdf")
DB_PATH ="vectorstore/faiss_index"
COLLECTION_NAME="pdf_collection"
