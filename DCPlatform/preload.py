import nltk
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('paraphrase-xlm-r-multilingual-v1')
nltk.download('stopwords')