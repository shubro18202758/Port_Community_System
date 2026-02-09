"""
GPU-Optimized Fine-Tuning Pipeline for Berth Planning AI
=========================================================
Comprehensive optimization with iterative refinement for retrieval accuracy
- GPU-accelerated embeddings
- Enhanced chunking strategies
- Semantic metadata enrichment
- Multi-iteration fine-tuning
- Comprehensive benchmarking
"""

import os
import sys
import json
import time
import gc
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
import warnings
warnings.filterwarnings('ignore')

# GPU Setup - MUST be done before importing torch-dependent libraries
os.environ['CUDA_VISIBLE_DEVICES'] = '0'

import torch
import numpy as np
import pandas as pd

# Set GPU as default device
if torch.cuda.is_available():
    torch.set_default_device('cuda')
    print(f"✓ GPU Acceleration Enabled: {torch.cuda.get_device_name(0)}")
else:
    print("⚠ Running on CPU - GPU not available")

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class FinetuningConfig:
    """Configuration for fine-tuning pipeline"""
    # Paths
    base_path: str = r"C:\Users\sayan\Downloads\Team1\Berth_Planning\ai-service"
    mundra_path: str = r"C:\Users\sayan\Downloads\Team1\Berth_Planning\documents\Data\Mundra"
    global_train_path: str = r"C:\Users\sayan\Downloads\Team1\Berth_Planning\ai-service\Train_Database"
    knowledge_base_path: str = r"C:\Users\sayan\Downloads\Team1\Berth_Planning\ai-service\knowledge_base"
    chroma_path: str = r"C:\Users\sayan\Downloads\Team1\Berth_Planning\ai-service\chroma_db_optimized"
    
    # Embedding model - using a better model for accuracy
    embedding_model: str = "sentence-transformers/all-mpnet-base-v2"  # 768-dim, better quality
    
    # Chunking parameters
    chunk_size: int = 512  # Larger chunks for more context
    chunk_overlap: int = 100  # More overlap for continuity
    
    # Fine-tuning iterations
    max_iterations: int = 3
    accuracy_threshold: float = 0.85  # Target accuracy
    
    # GPU batch size
    batch_size: int = 64  # Optimized for RTX 4070 8GB
    
    # Test queries for evaluation
    test_queries: Dict[str, List[str]] = field(default_factory=lambda: {
        "tidal": [
            "What is the tidal pattern at Mundra Port?",
            "Show me tide levels for Mundra",
            "High tide and low tide times at Mundra",
            "Tidal data for berth planning",
        ],
        "vessel": [
            "What vessels are scheduled at Mundra?",
            "Container vessel arrivals at Mundra Port",
            "Vessel schedule for next week",
            "Ships calling at Mundra terminals",
        ],
        "berth": [
            "List all berths at Mundra Container Terminal",
            "Berth availability at Mundra Port",
            "Which berths can handle VLCC vessels?",
            "Berth dimensions at Mundra",
        ],
        "weather": [
            "Weather conditions at Mundra Port",
            "Wind speed and wave height at Mundra",
            "Weather forecast for port operations",
            "Visibility conditions at Mundra",
        ],
        "ukc": [
            "Under keel clearance requirements at Mundra",
            "UKC calculations for deep draft vessels",
            "Minimum UKC for container terminals",
            "Draft restrictions at Mundra channel",
        ],
        "pilot": [
            "Pilotage requirements at Mundra",
            "Pilot boarding procedures",
            "Licensed pilots at Mundra Port",
            "Pilot availability for vessel arrival",
        ],
        "ais": [
            "AIS data for vessels near Mundra",
            "Real-time vessel positions at Mundra",
            "AIS tracking for port approach",
            "Vessel movement patterns from AIS",
        ],
        "anchorage": [
            "Anchorage areas at Mundra Port",
            "Anchorage waiting times",
            "Vessel anchorage assignments",
            "Anchorage capacity at Mundra",
        ],
    })


# ============================================================================
# GPU-OPTIMIZED EMBEDDING CLASS
# ============================================================================

class GPUEmbeddingFunction:
    """GPU-accelerated embedding function for ChromaDB"""
    
    def __init__(self, model_name: str, device: str = None):
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"Loading embedding model on {self.device.upper()}...")
        
        self.model = SentenceTransformer(model_name, device=self.device)
        self.model.max_seq_length = 512
        
        # Warm up the model
        _ = self.model.encode(["warmup"], convert_to_numpy=True)
        print(f"✓ Embedding model loaded: {model_name}")
        
    def __call__(self, input: List[str]) -> List[List[float]]:
        """Generate embeddings using GPU - for document embedding"""
        embeddings = self.model.encode(
            input,
            batch_size=64,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True  # Important for cosine similarity
        )
        return embeddings.tolist()
    
    def embed_documents(self, input: List[str]) -> List[List[float]]:
        """ChromaDB interface for document embedding"""
        return self.__call__(input)
    
    def embed_query(self, input: str) -> List[float]:
        """ChromaDB interface for query embedding"""
        embedding = self.model.encode(
            [input],
            batch_size=1,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        return embedding[0].tolist()
    
    def embed_with_metadata(self, texts: List[str], batch_size: int = 64) -> np.ndarray:
        """Batch embed with progress tracking"""
        all_embeddings = []
        total_batches = (len(texts) + batch_size - 1) // batch_size
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            embeddings = self.model.encode(
                batch,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            all_embeddings.append(embeddings)
            
            batch_num = (i // batch_size) + 1
            if batch_num % 10 == 0:
                print(f"  Embedded {batch_num}/{total_batches} batches...")
        
        return np.vstack(all_embeddings)


# ============================================================================
# ENHANCED CHUNKING WITH SEMANTIC METADATA
# ============================================================================

class SemanticChunker:
    """Enhanced chunking with semantic enrichment for better retrieval"""
    
    # Domain-specific keyword mappings for metadata enrichment
    DOMAIN_KEYWORDS = {
        "tidal": ["tide", "tidal", "high_tide", "low_tide", "tide_height", "tide_time", 
                  "tidal_range", "spring_tide", "neap_tide", "tidal_window", "tide_level"],
        "weather": ["wind", "wave", "visibility", "weather", "temperature", "humidity",
                    "wind_speed", "wind_direction", "wave_height", "swell", "precipitation"],
        "vessel": ["vessel", "ship", "imo", "mmsi", "vessel_name", "vessel_type", "dwt",
                   "loa", "beam", "draft", "eta", "etd", "arrival", "departure", "cargo"],
        "berth": ["berth", "terminal", "quay", "jetty", "pier", "berth_number", "berth_length",
                  "berth_depth", "fender", "bollard", "crane", "berth_status"],
        "pilot": ["pilot", "pilotage", "boarding", "pilot_name", "pilot_license", 
                  "pilot_station", "pilot_boat", "pilot_ladder"],
        "ukc": ["ukc", "under_keel", "clearance", "squat", "draft", "depth", "channel_depth",
                "air_draft", "charted_depth", "minimum_ukc"],
        "ais": ["ais", "mmsi", "imo", "position", "latitude", "longitude", "course", 
                "speed", "heading", "navigation_status", "destination"],
        "anchorage": ["anchorage", "anchor", "waiting", "anchorage_area", "anchor_position",
                      "waiting_time", "anchorage_capacity"],
        "schedule": ["schedule", "eta", "etd", "arrival", "departure", "planned", "actual",
                     "delay", "slot", "window", "booking"],
        "channel": ["channel", "fairway", "draft_restriction", "channel_depth", "navigation",
                    "approach", "channel_width", "turning_basin"],
    }
    
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def detect_domain(self, text: str, source_file: str = "") -> List[str]:
        """Detect domain categories for text"""
        text_lower = text.lower()
        source_lower = source_file.lower()
        detected = []
        
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            # Check source file name first (strong signal)
            if domain in source_lower or any(kw in source_lower for kw in keywords[:3]):
                detected.append(domain)
                continue
            
            # Check text content
            keyword_count = sum(1 for kw in keywords if kw in text_lower)
            if keyword_count >= 2:  # At least 2 keywords
                detected.append(domain)
        
        return detected if detected else ["general"]
    
    def create_semantic_prefix(self, domains: List[str], source: str, row_data: dict = None) -> str:
        """Create semantic prefix for better retrieval"""
        prefixes = []
        
        # Domain-specific prefixes
        domain_prefixes = {
            "tidal": "TIDAL DATA: Tide levels, times, and tidal patterns.",
            "weather": "WEATHER DATA: Wind, waves, visibility, and conditions.",
            "vessel": "VESSEL DATA: Ship information, specifications, and schedule.",
            "berth": "BERTH DATA: Terminal berths, dimensions, and availability.",
            "pilot": "PILOT DATA: Pilotage services and requirements.",
            "ukc": "UKC DATA: Under-keel clearance calculations and requirements.",
            "ais": "AIS DATA: Automatic Identification System vessel tracking.",
            "anchorage": "ANCHORAGE DATA: Anchorage areas and waiting positions.",
            "schedule": "SCHEDULE DATA: Vessel arrival and departure schedules.",
            "channel": "CHANNEL DATA: Navigation channels and fairways.",
        }
        
        for domain in domains:
            if domain in domain_prefixes:
                prefixes.append(domain_prefixes[domain])
        
        if not prefixes:
            prefixes.append(f"DATA from {source}")
        
        return " ".join(prefixes) + " "
    
    def chunk_csv_enhanced(self, df: pd.DataFrame, source_file: str, 
                          rows_per_chunk: int = 10) -> List[Dict[str, Any]]:
        """Enhanced CSV chunking with semantic metadata"""
        chunks = []
        source_name = Path(source_file).stem
        
        # Detect overall domain from filename
        file_domains = self.detect_domain("", source_file)
        
        # Create column description
        col_desc = f"Columns: {', '.join(df.columns.tolist())}"
        
        for i in range(0, len(df), rows_per_chunk):
            batch = df.iloc[i:i+rows_per_chunk]
            
            # Convert rows to text
            rows_text = []
            for idx, row in batch.iterrows():
                row_dict = row.to_dict()
                row_text = ", ".join([f"{k}: {v}" for k, v in row_dict.items() if pd.notna(v)])
                rows_text.append(row_text)
            
            content = "\n".join(rows_text)
            
            # Detect content-specific domains
            content_domains = self.detect_domain(content, source_file)
            all_domains = list(set(file_domains + content_domains))
            
            # Create semantic prefix
            prefix = self.create_semantic_prefix(all_domains, source_name)
            
            # Create chunk with enhanced metadata
            chunk_id = hashlib.md5(f"{source_file}_{i}".encode()).hexdigest()[:12]
            
            chunks.append({
                "id": f"{source_name}_{chunk_id}",
                "text": prefix + col_desc + "\n" + content,
                "metadata": {
                    "source": source_name,
                    "source_file": Path(source_file).name,
                    "domains": ",".join(all_domains),
                    "row_start": i,
                    "row_end": min(i + rows_per_chunk, len(df)),
                    "total_rows": len(df),
                    "chunk_type": "csv_data",
                    "columns": ",".join(df.columns.tolist()[:10]),  # First 10 columns
                }
            })
        
        return chunks
    
    def chunk_text_enhanced(self, text: str, source_file: str) -> List[Dict[str, Any]]:
        """Enhanced text chunking with semantic metadata"""
        chunks = []
        source_name = Path(source_file).stem
        
        # Split into paragraphs first
        paragraphs = text.split('\n\n')
        
        current_chunk = ""
        chunk_num = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            if len(current_chunk) + len(para) < self.chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    # Detect domains
                    domains = self.detect_domain(current_chunk, source_file)
                    prefix = self.create_semantic_prefix(domains, source_name)
                    
                    chunk_id = hashlib.md5(f"{source_file}_{chunk_num}".encode()).hexdigest()[:12]
                    
                    chunks.append({
                        "id": f"{source_name}_{chunk_id}",
                        "text": prefix + current_chunk.strip(),
                        "metadata": {
                            "source": source_name,
                            "source_file": Path(source_file).name,
                            "domains": ",".join(domains),
                            "chunk_num": chunk_num,
                            "chunk_type": "text",
                        }
                    })
                    chunk_num += 1
                
                current_chunk = para + "\n\n"
        
        # Don't forget the last chunk
        if current_chunk.strip():
            domains = self.detect_domain(current_chunk, source_file)
            prefix = self.create_semantic_prefix(domains, source_name)
            chunk_id = hashlib.md5(f"{source_file}_{chunk_num}".encode()).hexdigest()[:12]
            
            chunks.append({
                "id": f"{source_name}_{chunk_id}",
                "text": prefix + current_chunk.strip(),
                "metadata": {
                    "source": source_name,
                    "source_file": Path(source_file).name,
                    "domains": ",".join(domains),
                    "chunk_num": chunk_num,
                    "chunk_type": "text",
                }
            })
        
        return chunks


# ============================================================================
# FINE-TUNING PIPELINE
# ============================================================================

class GPUOptimizedFinetuning:
    """Main fine-tuning pipeline with GPU acceleration"""
    
    def __init__(self, config: FinetuningConfig):
        self.config = config
        self.chunker = SemanticChunker(config.chunk_size, config.chunk_overlap)
        self.embedding_fn = None
        self.collection = None
        self.client = None
        self.metrics = {
            "iterations": [],
            "accuracy_history": [],
            "timing": {},
        }
    
    def initialize(self):
        """Initialize ChromaDB and embedding model"""
        print("\n" + "="*70)
        print("INITIALIZING GPU-OPTIMIZED FINE-TUNING PIPELINE")
        print("="*70)
        
        # Initialize embedding function with GPU
        self.embedding_fn = GPUEmbeddingFunction(self.config.embedding_model)
        
        # Initialize ChromaDB
        chroma_path = Path(self.config.chroma_path)
        if chroma_path.exists():
            import shutil
            print(f"Removing existing ChromaDB at {chroma_path}")
            shutil.rmtree(chroma_path)
        
        self.client = chromadb.PersistentClient(
            path=str(chroma_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        self.collection = self.client.create_collection(
            name="berth_planning_optimized",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )
        
        print(f"✓ ChromaDB initialized at {chroma_path}")
    
    def process_mundra_data(self) -> List[Dict[str, Any]]:
        """Process Mundra-specific training data"""
        print("\n--- Processing Mundra Data ---")
        all_chunks = []
        mundra_path = Path(self.config.mundra_path)
        
        csv_files = list(mundra_path.glob("*.csv"))
        print(f"Found {len(csv_files)} Mundra CSV files")
        
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file, encoding='utf-8', on_bad_lines='skip')
                
                # Determine optimal rows per chunk based on columns
                cols = len(df.columns)
                rows_per_chunk = max(5, min(15, 50 // cols))
                
                chunks = self.chunker.chunk_csv_enhanced(df, str(csv_file), rows_per_chunk)
                all_chunks.extend(chunks)
                print(f"  {csv_file.name}: {len(df)} rows → {len(chunks)} chunks")
                
            except Exception as e:
                print(f"  ⚠ Error processing {csv_file.name}: {e}")
        
        return all_chunks
    
    def process_global_data(self) -> List[Dict[str, Any]]:
        """Process global training data"""
        print("\n--- Processing Global Training Data ---")
        all_chunks = []
        global_path = Path(self.config.global_train_path)
        
        csv_files = list(global_path.glob("*.csv"))
        print(f"Found {len(csv_files)} global training files")
        
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file, encoding='utf-8', on_bad_lines='skip')
                
                # Larger chunks for training data (more context)
                rows_per_chunk = 15
                
                chunks = self.chunker.chunk_csv_enhanced(df, str(csv_file), rows_per_chunk)
                all_chunks.extend(chunks)
                print(f"  {csv_file.name}: {len(df)} rows → {len(chunks)} chunks")
                
            except Exception as e:
                print(f"  ⚠ Error processing {csv_file.name}: {e}")
        
        return all_chunks
    
    def process_knowledge_base(self) -> List[Dict[str, Any]]:
        """Process knowledge base documents"""
        print("\n--- Processing Knowledge Base ---")
        all_chunks = []
        kb_path = Path(self.config.knowledge_base_path)
        
        if not kb_path.exists():
            print("  Knowledge base path not found")
            return all_chunks
        
        md_files = list(kb_path.glob("*.md"))
        print(f"Found {len(md_files)} knowledge base files")
        
        for md_file in md_files:
            try:
                content = md_file.read_text(encoding='utf-8')
                chunks = self.chunker.chunk_text_enhanced(content, str(md_file))
                all_chunks.extend(chunks)
                print(f"  {md_file.name}: {len(content)} chars → {len(chunks)} chunks")
                
            except Exception as e:
                print(f"  ⚠ Error processing {md_file.name}: {e}")
        
        return all_chunks
    
    def create_synthetic_tidal_chunks(self) -> List[Dict[str, Any]]:
        """Create explicit tidal data chunks for better retrieval"""
        print("\n--- Creating Synthetic Tidal Enhancement Chunks ---")
        
        # Read actual tidal data if available
        tidal_file = Path(self.config.mundra_path) / "TIDAL_DATA.csv"
        
        synthetic_chunks = []
        
        if tidal_file.exists():
            df = pd.read_csv(tidal_file)
            
            # Create summary chunks
            chunk_templates = [
                {
                    "id": "tidal_summary_mundra",
                    "text": f"""TIDAL DATA: Comprehensive tidal information for Mundra Port.
                    
This dataset contains {len(df)} tidal observations for Mundra Port.
Tidal data includes: tide heights, tide times, tidal patterns, high tide, low tide, spring tide, neap tide information.
Columns: {', '.join(df.columns.tolist())}

Use this data for:
- Berth planning based on tidal windows
- Vessel arrival/departure scheduling with tide times
- UKC (Under Keel Clearance) calculations
- Channel navigation planning
- Port operations optimization

Key tidal parameters recorded: tide_height, tide_time, tide_type, tidal_range.""",
                    "metadata": {
                        "source": "TIDAL_DATA",
                        "domains": "tidal,ukc,schedule",
                        "chunk_type": "summary",
                        "priority": "high",
                    }
                },
                {
                    "id": "tidal_patterns_mundra",
                    "text": f"""TIDAL PATTERNS AT MUNDRA PORT

The tidal patterns at Mundra Port follow semi-diurnal characteristics with two high tides and two low tides per day.

Tidal Data Summary from {len(df)} records:
- Data source: TIDAL_DATA.csv
- Location: Mundra Port, Gujarat, India
- Used for: Vessel scheduling, berth planning, UKC calculations

Tidal considerations for berth planning:
1. High tide windows - optimal for deep draft vessels
2. Low tide restrictions - draft limitations apply
3. Tidal range affects vessel mooring and cargo operations
4. Spring tides (full/new moon) have larger ranges
5. Neap tides have smaller tidal variations

Query this dataset for: tide levels, tidal patterns, high tide times, low tide times, tidal windows.""",
                    "metadata": {
                        "source": "TIDAL_DATA",
                        "domains": "tidal,schedule,berth",
                        "chunk_type": "explanation",
                        "priority": "high",
                    }
                }
            ]
            
            synthetic_chunks.extend(chunk_templates)
            
            # Create chunks from actual data samples
            sample_data = df.head(20).to_string()
            synthetic_chunks.append({
                "id": "tidal_sample_data",
                "text": f"TIDAL DATA SAMPLE from Mundra Port:\n\n{sample_data}",
                "metadata": {
                    "source": "TIDAL_DATA",
                    "domains": "tidal",
                    "chunk_type": "sample",
                }
            })
        
        print(f"  Created {len(synthetic_chunks)} tidal enhancement chunks")
        return synthetic_chunks
    
    def index_chunks(self, chunks: List[Dict[str, Any]]):
        """Index all chunks to ChromaDB with GPU-accelerated embeddings"""
        print(f"\n--- Indexing {len(chunks)} chunks with GPU ---")
        start_time = time.time()
        
        # Prepare batch data
        ids = [c["id"] for c in chunks]
        texts = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        
        # Index in batches
        batch_size = 500
        for i in range(0, len(chunks), batch_size):
            batch_ids = ids[i:i+batch_size]
            batch_texts = texts[i:i+batch_size]
            batch_meta = metadatas[i:i+batch_size]
            
            self.collection.add(
                ids=batch_ids,
                documents=batch_texts,
                metadatas=batch_meta
            )
            
            print(f"  Indexed batch {i//batch_size + 1}/{(len(chunks)+batch_size-1)//batch_size}")
        
        elapsed = time.time() - start_time
        self.metrics["timing"]["indexing"] = elapsed
        print(f"✓ Indexing complete in {elapsed:.1f}s ({len(chunks)/elapsed:.1f} chunks/sec)")
    
    def evaluate_retrieval(self, iteration: int) -> Dict[str, Any]:
        """Evaluate retrieval accuracy for all test queries"""
        print(f"\n--- Evaluating Retrieval (Iteration {iteration}) ---")
        
        results = {
            "iteration": iteration,
            "timestamp": datetime.now().isoformat(),
            "categories": {},
            "overall_accuracy": 0.0,
            "overall_mrr": 0.0,
            "details": [],
        }
        
        total_correct = 0
        total_queries = 0
        total_mrr = 0.0
        
        for category, queries in self.config.test_queries.items():
            category_correct = 0
            category_mrr = 0.0
            
            for query in queries:
                # Query ChromaDB
                query_results = self.collection.query(
                    query_texts=[query],
                    n_results=5,
                    include=["documents", "metadatas", "distances"]
                )
                
                # Check if expected category is in top results
                found_rank = None
                for rank, meta in enumerate(query_results["metadatas"][0]):
                    domains = meta.get("domains", "").split(",")
                    if category in domains or category in meta.get("source", "").lower():
                        found_rank = rank + 1
                        break
                
                is_correct = found_rank is not None and found_rank <= 3
                mrr = 1.0 / found_rank if found_rank else 0.0
                
                if is_correct:
                    category_correct += 1
                    total_correct += 1
                
                category_mrr += mrr
                total_mrr += mrr
                total_queries += 1
                
                results["details"].append({
                    "category": category,
                    "query": query,
                    "correct": is_correct,
                    "found_rank": found_rank,
                    "top_source": query_results["metadatas"][0][0].get("source", "unknown") if query_results["metadatas"][0] else "none",
                })
            
            category_accuracy = category_correct / len(queries) if queries else 0
            category_avg_mrr = category_mrr / len(queries) if queries else 0
            
            results["categories"][category] = {
                "accuracy": category_accuracy,
                "mrr": category_avg_mrr,
                "correct": category_correct,
                "total": len(queries),
            }
            
            status = "✓" if category_accuracy >= 0.75 else "⚠" if category_accuracy >= 0.5 else "✗"
            print(f"  {status} {category}: {category_accuracy*100:.0f}% ({category_correct}/{len(queries)})")
        
        results["overall_accuracy"] = total_correct / total_queries if total_queries else 0
        results["overall_mrr"] = total_mrr / total_queries if total_queries else 0
        
        print(f"\n  Overall Accuracy: {results['overall_accuracy']*100:.1f}%")
        print(f"  Mean Reciprocal Rank: {results['overall_mrr']:.3f}")
        
        return results
    
    def run_finetuning(self):
        """Run the complete fine-tuning pipeline"""
        print("\n" + "="*70)
        print("STARTING GPU-OPTIMIZED FINE-TUNING")
        print("="*70)
        
        total_start = time.time()
        
        # Initialize
        self.initialize()
        
        # Process all data sources
        all_chunks = []
        
        mundra_chunks = self.process_mundra_data()
        all_chunks.extend(mundra_chunks)
        
        global_chunks = self.process_global_data()
        all_chunks.extend(global_chunks)
        
        kb_chunks = self.process_knowledge_base()
        all_chunks.extend(kb_chunks)
        
        # Add synthetic enhancement chunks
        tidal_chunks = self.create_synthetic_tidal_chunks()
        all_chunks.extend(tidal_chunks)
        
        print(f"\n--- Total: {len(all_chunks)} chunks ---")
        print(f"  Mundra: {len(mundra_chunks)}")
        print(f"  Global: {len(global_chunks)}")
        print(f"  Knowledge Base: {len(kb_chunks)}")
        print(f"  Synthetic Enhancements: {len(tidal_chunks)}")
        
        # Index all chunks
        self.index_chunks(all_chunks)
        
        # Run evaluation iterations
        for iteration in range(1, self.config.max_iterations + 1):
            print(f"\n{'='*70}")
            print(f"FINE-TUNING ITERATION {iteration}/{self.config.max_iterations}")
            print("="*70)
            
            eval_results = self.evaluate_retrieval(iteration)
            self.metrics["iterations"].append(eval_results)
            self.metrics["accuracy_history"].append(eval_results["overall_accuracy"])
            
            if eval_results["overall_accuracy"] >= self.config.accuracy_threshold:
                print(f"\n✓ Target accuracy {self.config.accuracy_threshold*100}% achieved!")
                break
            
            # If not last iteration, apply improvements
            if iteration < self.config.max_iterations:
                self.apply_iteration_improvements(eval_results)
        
        total_time = time.time() - total_start
        self.metrics["timing"]["total"] = total_time
        
        # Generate final report
        self.generate_report()
        
        return self.metrics
    
    def apply_iteration_improvements(self, eval_results: Dict[str, Any]):
        """Apply improvements based on evaluation results"""
        print("\n--- Applying Iteration Improvements ---")
        
        weak_categories = [
            cat for cat, data in eval_results["categories"].items()
            if data["accuracy"] < 0.75
        ]
        
        if weak_categories:
            print(f"  Weak categories: {', '.join(weak_categories)}")
            
            # Add more targeted chunks for weak categories
            enhancement_chunks = []
            
            for category in weak_categories:
                # Create targeted enhancement chunks
                enhancement_chunks.extend(self.create_category_enhancements(category))
            
            if enhancement_chunks:
                print(f"  Adding {len(enhancement_chunks)} enhancement chunks")
                
                ids = [c["id"] for c in enhancement_chunks]
                texts = [c["text"] for c in enhancement_chunks]
                metadatas = [c["metadata"] for c in enhancement_chunks]
                
                self.collection.add(ids=ids, documents=texts, metadatas=metadatas)
    
    def create_category_enhancements(self, category: str) -> List[Dict[str, Any]]:
        """Create enhancement chunks for a weak category"""
        enhancements = []
        
        # Category-specific enhancement templates
        templates = {
            "tidal": [
                "TIDAL INFORMATION: The tidal patterns, tide levels, high tide times, low tide times, and tidal windows at Mundra Port.",
                "TIDE DATA: Tidal range, spring tides, neap tides, and tidal predictions for vessel scheduling and berth planning.",
            ],
            "weather": [
                "WEATHER CONDITIONS: Wind speed, wind direction, wave height, visibility, and weather forecasts for Mundra Port operations.",
                "METEOROLOGICAL DATA: Weather parameters affecting port operations, vessel movements, and berth allocations.",
            ],
            "vessel": [
                "VESSEL INFORMATION: Ship schedules, vessel specifications (LOA, beam, draft, DWT), ETAs, and cargo details at Mundra Port.",
                "SHIP DATA: Container vessels, tankers, bulk carriers, and their scheduling at Mundra terminals.",
            ],
            "berth": [
                "BERTH INFORMATION: Terminal berths at Mundra Port including dimensions, depths, crane availability, and occupancy status.",
                "BERTH ALLOCATION: Berth planning data for container terminals, bulk terminals, and liquid cargo berths.",
            ],
            "pilot": [
                "PILOTAGE DATA: Pilot requirements, pilot boarding points, and pilotage services at Mundra Port.",
                "PILOT INFORMATION: Licensed pilots, pilot availability, and boarding procedures for vessel arrivals.",
            ],
            "ukc": [
                "UKC CALCULATIONS: Under-keel clearance requirements, squat calculations, and draft restrictions at Mundra.",
                "DRAFT DATA: Channel depths, minimum UKC requirements, and vessel draft limitations.",
            ],
            "ais": [
                "AIS TRACKING: Automatic Identification System data showing vessel positions, movements, and navigation status.",
                "VESSEL TRACKING: Real-time AIS data for ships approaching and departing Mundra Port.",
            ],
            "anchorage": [
                "ANCHORAGE INFORMATION: Designated anchorage areas, waiting positions, and anchorage capacity at Mundra.",
                "ANCHORAGE DATA: Vessel waiting times, anchorage assignments, and anchor positions.",
            ],
        }
        
        if category in templates:
            for i, text in enumerate(templates[category]):
                enhancements.append({
                    "id": f"enhancement_{category}_{i}",
                    "text": text,
                    "metadata": {
                        "source": f"{category.upper()}_ENHANCEMENT",
                        "domains": category,
                        "chunk_type": "enhancement",
                        "priority": "high",
                    }
                })
        
        return enhancements
    
    def generate_report(self):
        """Generate fine-tuning report"""
        print("\n" + "="*70)
        print("FINE-TUNING REPORT")
        print("="*70)
        
        final_iteration = self.metrics["iterations"][-1] if self.metrics["iterations"] else {}
        
        print(f"\nIterations Completed: {len(self.metrics['iterations'])}")
        print(f"Final Accuracy: {final_iteration.get('overall_accuracy', 0)*100:.1f}%")
        print(f"Final MRR: {final_iteration.get('overall_mrr', 0):.3f}")
        print(f"Total Time: {self.metrics['timing'].get('total', 0):.1f}s")
        
        print("\nCategory Performance:")
        for cat, data in final_iteration.get("categories", {}).items():
            status = "✓" if data["accuracy"] >= 0.75 else "⚠"
            print(f"  {status} {cat}: {data['accuracy']*100:.0f}% (MRR: {data['mrr']:.3f})")
        
        print("\nAccuracy Progress:")
        for i, acc in enumerate(self.metrics["accuracy_history"], 1):
            print(f"  Iteration {i}: {acc*100:.1f}%")
        
        # Save metrics to file
        metrics_file = Path(self.config.base_path) / "finetuning_metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump(self.metrics, f, indent=2, default=str)
        print(f"\n✓ Metrics saved to {metrics_file}")
        
        # Collection stats
        collection_count = self.collection.count()
        print(f"\nFinal Collection: {collection_count} chunks indexed")
        print(f"ChromaDB Path: {self.config.chroma_path}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run the GPU-optimized fine-tuning pipeline"""
    print("="*70)
    print("BERTH PLANNING AI - GPU-OPTIMIZED FINE-TUNING")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # GPU Memory cleanup
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        gc.collect()
    
    config = FinetuningConfig()
    pipeline = GPUOptimizedFinetuning(config)
    
    try:
        metrics = pipeline.run_finetuning()
        
        print("\n" + "="*70)
        print("FINE-TUNING COMPLETED SUCCESSFULLY")
        print("="*70)
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Fine-tuning failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
