import os
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
import numpy as np
from typing import List, Dict, Tuple
import re
from datetime import datetime
import hashlib
import ssl
import urllib3
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import PyPDF2
import io
import json

import sys
import io
import unicodedata

# 1. Console encoding (Windows)
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context
os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'

load_dotenv()

class EmbeddingGenerator:
    """Generate embeddings using sentence transformers"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.embedding_dim = 384  # Dimension for all-MiniLM-L6-v2
        self._load_model()
    
    def _load_model(self):
        """Load the sentence transformer model with SSL bypass"""
        try:
            print(f"Loading embedding model: {self.model_name}")
            
            # Try offline mode first if model is cached
            try:
                self.model = SentenceTransformer(self.model_name, local_files_only=True)
                print(f"Model loaded from cache successfully")
                return
            except Exception:
                print(f"Model not found in cache, downloading...")
            
            # Download with SSL bypass
            self.model = SentenceTransformer(self.model_name, trust_remote_code=True)
            print(f"Model loaded successfully")
            
        except Exception as e:
            print(f"Failed to load model: {e}")
            print("\nTo fix SSL issues:")
            print("1. Use a different network (personal instead of corporate)")
            print("2. Download model manually from https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2")
            raise
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for single text"""
        try:
            if not self.model:
                self._load_model()
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.astype(np.float32)
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return np.zeros(self.embedding_dim, dtype=np.float32)
    
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """Generate embeddings for multiple texts in batches"""
        try:
            if not self.model:
                self._load_model()
            
            embeddings = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                batch_embeddings = self.model.encode(batch, convert_to_numpy=True, show_progress_bar=False)
                embeddings.extend([emb.astype(np.float32) for emb in batch_embeddings])
                print(f"Processed {min(i + batch_size, len(texts))}/{len(texts)} embeddings")
            
            return embeddings
        except Exception as e:
            print(f"Error generating batch embeddings: {e}")
            return [np.zeros(self.embedding_dim, dtype=np.float32) for _ in texts]


class PDFProcessor:
    """Process PDF documents and extract text"""
    
    def __init__(self, chunk_size: int = 1500, chunk_overlap: int = 300):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def extract_text_from_pdf(self, pdf_bytes: bytes) -> List[Tuple[str, int]]:
        """Extract text from PDF bytes and return list of (text, page_number)"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            pages_text = []
            
            for page_num, page in enumerate(pdf_reader.pages):
                text = page.extract_text()
                if text.strip():
                    cleaned_text = self._clean_text(text)
                    pages_text.append((cleaned_text, page_num + 1))
            
            print(f"Extracted text from {len(pages_text)} pages")
            return pages_text
            
        except Exception as e:
            print(f"Error extracting PDF text: {e}")
            return []
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # ADD Unicode normalization HERE
        text = unicodedata.normalize('NFKD', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s.,!?;:()\-\'"]+', '', text)
        return text.strip()
    
    def chunk_text(self, text: str, page_number: int = 1) -> List[Dict]:
        """Split text into overlapping chunks"""
        text = re.sub(r'\s+', ' ', text).strip()
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                sentence_end = max(
                    text.rfind('.', start, end),
                    text.rfind('!', start, end),
                    text.rfind('?', start, end)
                )
                if sentence_end > start:
                    end = sentence_end + 1
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunks.append({
                    'text': chunk_text,
                    'page_number': page_number,
                    'chunk_index': chunk_index,
                    'start_char': start,
                    'end_char': end
                })
                chunk_index += 1
            
            start = end - self.chunk_overlap
        
        return chunks
    
    def process_pdf_bytes(self, pdf_bytes: bytes) -> List[Dict]:
        """Complete PDF processing pipeline"""
        pages_text = self.extract_text_from_pdf(pdf_bytes)
        if not pages_text:
            return []
        
        all_chunks = []
        for text, page_num in pages_text:
            chunks = self.chunk_text(text, page_num)
            all_chunks.extend(chunks)
        
        print(f"Created {len(all_chunks)} chunks from PDF")
        return all_chunks


class PolicyWordingRAG:
    """RAG system without pgvector - uses Python-based similarity search"""
    
    def __init__(self, db_config: Dict[str, str] = None):
        """Initialize RAG system with database and embedding model"""
        
        # Database configuration
        if db_config is None:
            db_config = {
                'host': os.getenv('POSTGRES_HOST', 'localhost'),
                'database': os.getenv('POSTGRES_DB', 'insurance_rag'),
                'user': os.getenv('POSTGRES_USER', 'postgres'),
                'password': os.getenv('POSTGRES_PASSWORD', 'postgres'),
                'port': os.getenv('POSTGRES_PORT', '5432')
            }
        
        self.db_config = db_config
        self.conn = None
        
        # Initialize components
        self.embedding_generator = EmbeddingGenerator()
        self.pdf_processor = PDFProcessor()
        
        # Initialize database
        self._initialize_database()
    
    def _get_connection(self):
        """Create and return database connection"""
        try:
            conn = psycopg2.connect(**self.db_config)
            conn.set_client_encoding('UTF8')  # ADD THIS LINE
            return conn
        except Exception as e:
            print(f"Database connection failed: {e}")
            raise
    
    def _initialize_database(self):
        """Initialize database tables (no pgvector required)"""
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            # Create policy_documents table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS policy_documents (
                    id SERIAL PRIMARY KEY,
                    document_name VARCHAR(255) NOT NULL,
                    document_hash VARCHAR(64) UNIQUE NOT NULL,
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_chunks INTEGER,
                    metadata JSONB
                );
            """)
            
            # Create policy_chunks table with binary embedding storage
            cur.execute("""
                CREATE TABLE IF NOT EXISTS policy_chunks (
                    id SERIAL PRIMARY KEY,
                    document_id INTEGER REFERENCES policy_documents(id) ON DELETE CASCADE,
                    chunk_index INTEGER NOT NULL,
                    chunk_text TEXT NOT NULL,
                    page_number INTEGER,
                    chunk_metadata JSONB,
                    embedding BYTEA,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(document_id, chunk_index)
                );
            """)
            
            # Create indices
            cur.execute("""
                CREATE INDEX IF NOT EXISTS policy_chunks_document_id_idx 
                ON policy_chunks(document_id);
            """)
            
            cur.execute("""
                CREATE INDEX IF NOT EXISTS policy_chunks_page_number_idx 
                ON policy_chunks(page_number);
            """)
            
            conn.commit()
            print("Database initialized successfully (using binary embedding storage)")
            
        except Exception as e:
            conn.rollback()
            print(f"Database initialization error: {e}")
            raise
        finally:
            cur.close()
            conn.close()
    
    def _compute_document_hash(self, text: str) -> str:
        """Compute SHA-256 hash of document text"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def add_policy_document(self, document_text: str = None, document_name: str = None, 
                       pdf_bytes: bytes = None, metadata: Dict = None) -> Tuple[int, int]:
        """
        Add a policy wording document to the knowledge base
        
        Args:
            document_text: Full text of policy (if already extracted)
            document_name: Name/identifier for document
            pdf_bytes: PDF file as bytes (if text not provided)
            metadata: Optional metadata dictionary
            
        Returns:
            Tuple of (document_id, number_of_chunks)
        """
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            # Process PDF if provided
            if pdf_bytes and not document_text:
                print("Processing PDF document...")
                chunks_data = self.pdf_processor.process_pdf_bytes(pdf_bytes)
                if not chunks_data:
                    raise Exception("Failed to extract text from PDF")
                document_text = " ".join([c['text'] for c in chunks_data])
            elif document_text:
                # Chunk the text
                chunks_data = self.pdf_processor.chunk_text(document_text)
            else:
                raise Exception("Either document_text or pdf_bytes must be provided")
            
            # Compute document hash
            doc_hash = self._compute_document_hash(document_text)
            
            # Check if document already exists
            cur.execute(
                "SELECT id, total_chunks FROM policy_documents WHERE document_hash = %s",
                (doc_hash,)
            )
            existing = cur.fetchone()
            
            if existing:
                document_id, num_chunks = existing
                print(f"Document already exists (ID: {document_id}) with {num_chunks} chunks - reusing it")
                return document_id, num_chunks
        
            print(f"Chunking document: {document_name}")
            print(f"Created {len(chunks_data)} chunks")
            
            # Generate embeddings for all chunks
            print("Generating embeddings...")
            chunk_texts = [chunk['text'] for chunk in chunks_data]
            embeddings = self.embedding_generator.generate_embeddings_batch(chunk_texts)
            
            # Insert document record
            cur.execute("""
                INSERT INTO policy_documents (document_name, document_hash, total_chunks, metadata)
                VALUES (%s, %s, %s, %s)
                RETURNING id;
            """, (document_name, doc_hash, len(chunks_data), 
                psycopg2.extras.Json(metadata or {})))
            
            document_id = cur.fetchone()[0]
            
            # Prepare chunk data for batch insert
            chunk_records = []
            for chunk, embedding in zip(chunks_data, embeddings):
                # Convert numpy array to binary
                embedding_binary = embedding.tobytes()
                
                chunk_records.append((
                    document_id,
                    chunk['chunk_index'],
                    chunk['text'],
                    chunk.get('page_number', 0),
                    psycopg2.extras.Json({
                        'start_char': chunk.get('start_char', 0),
                        'end_char': chunk.get('end_char', 0)
                    }),
                    embedding_binary
                ))
            
            # Batch insert chunks
            print("Inserting chunks into database...")
            execute_values(
                cur,
                """
                INSERT INTO policy_chunks 
                (document_id, chunk_index, chunk_text, page_number, chunk_metadata, embedding)
                VALUES %s
                """,
                chunk_records
            )
            
            conn.commit()
            print(f"Successfully added document (ID: {document_id}) with {len(chunks_data)} chunks")
            
            return document_id, len(chunks_data)
            
        except Exception as e:
            conn.rollback()
            print(f"Error adding document: {e}")
            import traceback
            print(traceback.format_exc())
            raise
        finally:
            cur.close()
            conn.close()
    
    def search_similar_chunks(self, query: str, top_k: int = 5, 
                            document_id: int = None, 
                            min_page: int = 0) -> List[Dict]:
        """Search for similar chunks using cosine similarity"""
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_generator.generate_embedding(query)
            query_norm = np.linalg.norm(query_embedding)
            
            # Build SQL query - try with page filter first only if min_page > 0
            sql = """
                SELECT 
                    pc.id,
                    pc.document_id,
                    pd.document_name,
                    pc.chunk_index,
                    pc.chunk_text,
                    pc.page_number,
                    pc.chunk_metadata,
                    pc.embedding
                FROM policy_chunks pc
                JOIN policy_documents pd ON pc.document_id = pd.id
                WHERE 1=1
            """
            
            params = []
            
            # Only filter by page if min_page is explicitly set
            if min_page > 0:
                sql += " AND pc.page_number > %s"
                params.append(min_page)
            
            if document_id:
                sql += " AND pc.document_id = %s"
                params.append(document_id)
            
            cur.execute(sql, params)
            results = cur.fetchall()
            
            if not results:
                print(f"No chunks found for query: '{query}'")
                return []
            
            # Calculate similarities
            similarities = []
            for row in results:
                # Convert binary embedding back to numpy array
                stored_embedding = np.frombuffer(row['embedding'], dtype=np.float32)
                stored_norm = np.linalg.norm(stored_embedding)
                
                # Cosine similarity
                if stored_norm > 0 and query_norm > 0:
                    similarity = np.dot(query_embedding, stored_embedding) / (query_norm * stored_norm)
                else:
                    similarity = 0.0
                
                similarities.append({
                    'chunk_id': row['id'],
                    'document_id': row['document_id'],
                    'document_name': row['document_name'],
                    'chunk_index': row['chunk_index'],
                    'chunk_text': row['chunk_text'],
                    'page_number': row['page_number'],
                    'chunk_metadata': row['chunk_metadata'],
                    'similarity_score': float(similarity)
                })
            
            # Sort by similarity and return top_k
            similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            print(f"Found {len(similarities)} chunks, returning top {min(top_k, len(similarities))}")
            return similarities[:top_k]
            
        except Exception as e:
            print(f"Search error: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            cur.close()
            conn.close()

    def get_context_for_query(self, query: str, top_k: int = 5,document_id: int = None) -> str:
        try:
            # Use the existing search_similar_chunks method
            results = self.search_similar_chunks(
                query=query, 
                top_k=top_k, 
                document_id=document_id
            )
            
            if not results:
                return ""
            
            # Format the results into a context string
            context_parts = []
            for i, result in enumerate(results, 1):
                context_parts.append(
                    f"[Chunk {i} - Page {result['page_number']}, "
                    f"Similarity: {result['similarity_score']:.3f}]\n"
                    f"{result['chunk_text']}"
                )
            
            return "\n\n".join(context_parts)
            
        except Exception as e:
            print(f"Error getting context: {e}")
            return ""
    
    def delete_document(self, document_id: int) -> bool:
        """Delete a document and all its chunks"""
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("DELETE FROM policy_documents WHERE id = %s", (document_id,))
            conn.commit()
            deleted = cur.rowcount > 0
            
            if deleted:
                print(f"Deleted document ID: {document_id}")
            
            return deleted
            
        except Exception as e:
            conn.rollback()
            print(f"Delete error: {e}")
            raise
        finally:
            cur.close()
            conn.close()
    
    def get_document_stats(self) -> Dict:
        """Get statistics about the knowledge base"""
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                SELECT 
                    COUNT(DISTINCT pd.id) as total_documents,
                    COALESCE(SUM(pd.total_chunks), 0) as total_chunks,
                    COALESCE(AVG(pd.total_chunks), 0) as avg_chunks_per_doc
                FROM policy_documents pd;
            """)
            
            row = cur.fetchone()
            
            return {
                'total_documents': row[0] or 0,
                'total_chunks': row[1] or 0,
                'avg_chunks_per_document': float(row[2]) if row[2] else 0
            }
            
        finally:
            cur.close()
            conn.close()

    def list_documents(self) -> List[Dict]:
        """List all documents in the knowledge base"""
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                SELECT 
                    id,
                    document_name,
                    upload_date,
                    total_chunks,
                    metadata
                FROM policy_documents
                ORDER BY upload_date DESC
            """)
            
            rows = cur.fetchall()
            documents = []
            
            for row in rows:
                documents.append({
                    'id': row[0],
                    'document_name': row[1],
                    'upload_date': row[2].strftime('%Y-%m-%d %H:%M:%S') if row[2] else 'N/A',
                    'total_chunks': row[3],
                    'metadata': row[4]
                })
            
            return documents
            
        except Exception as e:
            print(f"Error listing documents: {e}")
            return []
        finally:
            cur.close()
            conn.close()
    
    def clear_all_documents(self) -> bool:
        """Clear all documents from the database"""
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("DELETE FROM policy_documents")
            conn.commit()
            print("All documents cleared from database")
            return True
        except Exception as e:
            conn.rollback()
            print(f"Failed to clear documents: {e}")
            return False
        finally:
            cur.close()
            conn.close()


# Utility functions for Streamlit integration

def analyze_claim_with_rag(claim_json: Dict, policy_wording_text: str, 
                           rag_system: PolicyWordingRAG, 
                           gemini_api_function) -> Tuple[Dict, str]:
    """Analyze if incident description is covered in policy wording using RAG"""
    import streamlit as st

    try:
        # Validate inputs
        if not policy_wording_text:
            return None, "Policy wording text is empty"
        
        if len(policy_wording_text.strip()) < 50:
            return None, "Policy wording text is too short"
        
        # CHANGED: Use st.write instead of print
        st.write(f"Policy wording length: {len(policy_wording_text)} characters")
        
        # Add policy wording to RAG
        st.write("Adding policy wording to knowledge base...")
        doc_id, chunks = rag_system.add_policy_document(
            document_text=policy_wording_text,
            document_name="Current Policy Wording",
            metadata={'claim_id': str(claim_json.get('claim_number', 'unknown'))}
        )
        st.write(f"Document added: ID={doc_id}, Chunks={chunks}")
        
        # Get incident description from claim
        incident_desc = claim_json.get('incident_description', '')
        if not incident_desc:
            return None, "No incident description found in claim"
        
        # Search for relevant policy sections
        st.write(f"Searching for: '{incident_desc}'")
        context = rag_system.get_context_for_query(incident_desc, top_k=5, document_id=doc_id)
        
        if not context:
            return None, "Could not find relevant policy sections"
        
        st.write(f"Found relevant sections")
        
        # Build simple prompt for Gemini
        prompt = f"""You are an insurance policy analyst. Determine if the following incident is covered by the policy.
INCIDENT DESCRIPTION:
{incident_desc}

RELEVANT POLICY SECTIONS:
{context}

Provide your analysis in the following JSON format:
{{
    "is_covered": "YES/NO/UNCLEAR",
    "confidence": "HIGH/MEDIUM/LOW",
    "reasoning": "brief explanation of why it is or isn't covered",
    "relevant_policy_text": "specific text from policy that supports your decision"
}}

Return ONLY the JSON object, no markdown or extra text."""

        # Call Gemini API
        st.write("Calling Gemini API for analysis...")
        response_text, error = gemini_api_function(prompt, os.getenv("GOOGLE_API_KEY"))
        
        if error:
            return None, f"Gemini API error: {error}"
        
        # Parse response
        response_text = re.sub(r'```json\s*', '', response_text)
        response_text = re.sub(r'```\s*', '', response_text)
        
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            analysis_result = json.loads(json_match.group(0))
            print("Analysis completed successfully")
            return analysis_result, None
        else:
            return None, f"Could not parse JSON from response: {response_text[:200]}..."
            
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        st.error(f"Analysis error: {e}")
        st.code(error_trace)
        return None, f"Analysis error: {str(e)}"

def display_rag_analysis(analysis_result: Dict):
    """Display RAG-based analysis results in Streamlit"""
    import streamlit as st
    import json
    
    # Coverage Decision
    is_covered = analysis_result.get('is_covered', 'UNKNOWN')
    confidence = analysis_result.get('confidence', 'UNKNOWN')
    
    if is_covered == 'YES':
        st.success(f"✅ Coverage Decision: **COVERED** (Confidence: {confidence})")
    elif is_covered == 'NO':
        st.error(f"❌ Coverage Decision: **NOT COVERED** (Confidence: {confidence})")
    else:
        st.warning(f"⚠️ Coverage Decision: **UNCLEAR** (Confidence: {confidence})")
    
    # Reasoning
    st.subheader("Analysis Reasoning")
    st.write(analysis_result.get('reasoning', 'N/A'))
    
    # Relevant Policy Text
    if analysis_result.get('relevant_policy_text'):
        st.subheader("Supporting Policy Text")
        st.info(analysis_result.get('relevant_policy_text'))
    
    # Download Report
    report_json = json.dumps(analysis_result, indent=4)
    st.download_button(
        label="Download Analysis Report",
        data=report_json,
        file_name="rag_analysis_report.json",
        mime="application/json"
    )

# Add these functions to the END of your rag.py file

# ADD THESE FUNCTIONS TO THE END OF YOUR rag.py FILE (after display_rag_analysis function)

def policy_assistant_chatbot(rag_system: PolicyWordingRAG, 
                             gemini_api_function,
                             document_id: int = None):
    """Interactive chatbot for querying policy wording"""
    import streamlit as st
    
    st.markdown("---")
    st.header("💬 Policy Assistant Chatbot")
    st.info("💡 Ask questions about the policy wording. The chatbot will search relevant sections and provide answers.")
    
    # Initialize chat history in session state
    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []
    
    # Display chat history with better formatting
    if st.session_state['chat_history']:
        st.subheader("📝 Conversation History")
        
        for i, message in enumerate(st.session_state['chat_history']):
            if message['role'] == 'user':
                with st.container():
                    st.markdown(f"**🧑 You:** {message['content']}")
            else:
                with st.container():
                    st.markdown(f"**🤖 Assistant:** {message['content']}")
                    if 'sources' in message and message['sources']:
                        with st.expander(f"📚 View {len(message['sources'])} Source(s)"):
                            for j, source in enumerate(message['sources'], 1):
                                st.markdown(f"**Source {j}** • Page {source['page_number']} • Relevance: {source['similarity_score']:.2%}")
                                st.text(source['chunk_text'][:400] + ("..." if len(source['chunk_text']) > 400 else ""))
                                st.markdown("---")
    
    # Chat input section
    st.markdown("---")
    st.subheader("✍️ Ask a Question")
    
    # Example questions
    with st.expander("💡 Example Questions"):
        st.markdown("""
        - What are the exclusions for fire damage?
        - What is the claim settlement process?
        - Is theft covered under this policy?
        - What documents are required to file a claim?
        - What is the deductible amount?
        - Are natural disasters covered?
        """)
    
    user_question = st.text_input(
        "Your question:",
        key="chat_input",
        placeholder="Type your question here...",
        label_visibility="collapsed"
    )
    
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        send_button = st.button("📤 Send", type="primary", use_container_width=True)
    with col2:
        clear_button = st.button("🗑️ Clear Chat", use_container_width=True)
    
    # Clear chat functionality
    if clear_button:
        st.session_state['chat_history'] = []
        st.rerun()
    
    # Send message functionality
    if send_button and user_question:
        # Add user message to history
        st.session_state['chat_history'].append({
            'role': 'user',
            'content': user_question
        })
        
        # Search for relevant context
        with st.spinner("🔍 Searching policy document..."):
            relevant_chunks = rag_system.search_similar_chunks(
                query=user_question,
                top_k=5,
                document_id=document_id
            )
        
        if not relevant_chunks:
            assistant_response = "❌ I couldn't find relevant information in the policy document for your question. Please try rephrasing or ask about a different topic."
            sources = []
        else:
            # Build context from relevant chunks
            context = "\n\n".join([
                f"[Section {i+1} - Page {chunk['page_number']}]\n{chunk['chunk_text']}"
                for i, chunk in enumerate(relevant_chunks)
            ])
            
            # Create prompt for Gemini
            prompt = f"""You are a helpful insurance policy assistant. Answer the user's question based ONLY on the provided policy sections.

USER QUESTION:
{user_question}

RELEVANT POLICY SECTIONS:
{context}

Instructions:
1. Answer the question directly and concisely
2. Quote specific policy text when relevant (use quotes)
3. If the information isn't in the provided sections, clearly state "This information is not covered in the available policy sections"
4. Use clear, simple language that's easy to understand
5. Be helpful and professional
6. Keep your answer focused and avoid unnecessary elaboration

Answer:"""
            
            # Get response from Gemini
            with st.spinner("💭 Generating answer..."):
                response_text, error = gemini_api_function(prompt, os.getenv("GOOGLE_API_KEY"))
            
            if error:
                assistant_response = f"❌ Error getting response: {error}"
                sources = []
            else:
                assistant_response = response_text.strip()
                sources = [
                    {
                        'chunk_text': chunk['chunk_text'],
                        'page_number': chunk['page_number'],
                        'similarity_score': chunk['similarity_score']
                    }
                    for chunk in relevant_chunks[:3]  # Top 3 sources
                ]
        
        # Add assistant response to history
        st.session_state['chat_history'].append({
            'role': 'assistant',
            'content': assistant_response,
            'sources': sources
        })
        
        # Rerun to display updated chat
        st.rerun()
    
    # Footer info
    st.markdown("---")
    st.caption("💡 Tip: Ask specific questions for better results. The assistant can only answer based on the uploaded policy document.")


# Also add this method to the PolicyWordingRAG class if not already present
# (Insert this inside the PolicyWordingRAG class definition)

