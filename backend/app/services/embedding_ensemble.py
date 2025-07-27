"""Multi-model embedding ensemble for enhanced search accuracy."""

import logging
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import numpy as np
from openai import AsyncOpenAI
import httpx

from app.core.config import settings
from app.core.redis import cache_manager, RedisKeys

logger = logging.getLogger(__name__)


class EmbeddingModel(Enum):
    """Available embedding models."""
    OPENAI_SMALL = "text-embedding-3-small"  # 1536 dims, general purpose
    OPENAI_LARGE = "text-embedding-3-large"  # 3072 dims, higher quality
    COHERE_ENGLISH = "embed-english-v3.0"   # 1024 dims, optimized for technical


class EmbeddingEnsemble:
    """
    Multi-model embedding service that combines:
    1. OpenAI text-embedding-3-small for general semantic understanding
    2. Cohere embed-english-v3.0 for technical skill precision
    
    This ensemble approach provides:
    - Better handling of technical jargon
    - Improved semantic understanding
    - Reduced false negatives for skill searches
    """
    
    def __init__(self):
        # OpenAI client
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        
        # Cohere client setup (would need API key in settings)
        self.cohere_api_key = getattr(settings, 'COHERE_API_KEY', None)
        self.cohere_client = httpx.AsyncClient() if self.cohere_api_key else None
        
        # Model dimensions
        self.model_dims = {
            EmbeddingModel.OPENAI_SMALL: 1536,
            EmbeddingModel.OPENAI_LARGE: 3072,
            EmbeddingModel.COHERE_ENGLISH: 1024
        }
        
        # Default models to use
        self.default_models = [EmbeddingModel.OPENAI_SMALL]
        if self.cohere_api_key:
            self.default_models.append(EmbeddingModel.COHERE_ENGLISH)
    
    async def get_embedding(
        self,
        text: str,
        model: EmbeddingModel = EmbeddingModel.OPENAI_SMALL,
        use_cache: bool = True
    ) -> List[float]:
        """
        Get embedding for text using specified model.
        
        Args:
            text: Text to embed
            model: Which embedding model to use
            use_cache: Whether to use cached embeddings
            
        Returns:
            Embedding vector
        """
        # Generate cache key
        text_hash = RedisKeys.hash_text(text)
        cache_key = f"{RedisKeys.EMBEDDING_CACHE}:{model.value}:{text_hash}"
        
        # Try cache first
        if use_cache:
            cached = await cache_manager.get_or_set(
                key=cache_key,
                fetch_func=lambda: self._compute_embedding(text, model),
                ttl=cache_manager.embedding_ttl,
                serialize=True
            )
            return cached
        
        # Compute directly
        return await self._compute_embedding(text, model)
    
    async def _compute_embedding(
        self,
        text: str,
        model: EmbeddingModel
    ) -> List[float]:
        """Compute embedding using specified model."""
        try:
            if model in [EmbeddingModel.OPENAI_SMALL, EmbeddingModel.OPENAI_LARGE]:
                return await self._compute_openai_embedding(text, model)
            elif model == EmbeddingModel.COHERE_ENGLISH:
                return await self._compute_cohere_embedding(text)
            else:
                raise ValueError(f"Unknown embedding model: {model}")
                
        except Exception as e:
            logger.error(f"Error computing {model.value} embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * self.model_dims[model]
    
    async def _compute_openai_embedding(
        self,
        text: str,
        model: EmbeddingModel
    ) -> List[float]:
        """Compute OpenAI embedding."""
        if not self.openai_client:
            logger.warning("OpenAI client not configured")
            return [0.0] * self.model_dims[model]
        
        try:
            response = await self.openai_client.embeddings.create(
                model=model.value,
                input=text,
                encoding_format="float"
            )
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            return [0.0] * self.model_dims[model]
    
    async def _compute_cohere_embedding(
        self,
        text: str
    ) -> List[float]:
        """Compute Cohere embedding."""
        if not self.cohere_client or not self.cohere_api_key:
            logger.warning("Cohere client not configured")
            return [0.0] * self.model_dims[EmbeddingModel.COHERE_ENGLISH]
        
        try:
            response = await self.cohere_client.post(
                "https://api.cohere.ai/v1/embed",
                headers={
                    "Authorization": f"Bearer {self.cohere_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "texts": [text],
                    "model": EmbeddingModel.COHERE_ENGLISH.value,
                    "input_type": "search_document"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["embeddings"][0]
            else:
                logger.error(f"Cohere API error: {response.status_code}")
                return [0.0] * self.model_dims[EmbeddingModel.COHERE_ENGLISH]
                
        except Exception as e:
            logger.error(f"Cohere embedding error: {e}")
            return [0.0] * self.model_dims[EmbeddingModel.COHERE_ENGLISH]
    
    async def get_ensemble_embedding(
        self,
        text: str,
        models: Optional[List[EmbeddingModel]] = None,
        weights: Optional[Dict[EmbeddingModel, float]] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get ensemble embedding combining multiple models.
        
        Args:
            text: Text to embed
            models: Models to use (defaults to all available)
            weights: Model weights for combination
            use_cache: Whether to use cached embeddings
            
        Returns:
            Dictionary with individual and combined embeddings
        """
        models = models or self.default_models
        
        # Default weights
        if not weights:
            weights = {
                EmbeddingModel.OPENAI_SMALL: 0.7,
                EmbeddingModel.COHERE_ENGLISH: 0.3
            }
        
        # Get embeddings from each model
        embeddings = {}
        for model in models:
            embedding = await self.get_embedding(text, model, use_cache)
            embeddings[model] = embedding
        
        # Combine embeddings (concatenation for now, could use other strategies)
        combined = []
        for model in models:
            if model in embeddings:
                combined.extend(embeddings[model])
        
        return {
            "text": text,
            "models": [m.value for m in models],
            "embeddings": {m.value: emb for m, emb in embeddings.items()},
            "combined": combined,
            "dimensions": len(combined)
        }
    
    async def get_query_embedding(
        self,
        query: str,
        query_type: Optional[str] = None
    ) -> List[float]:
        """
        Get optimized embedding for search queries.
        
        Args:
            query: Search query
            query_type: Type of query (skill_focused, role_focused, etc)
            
        Returns:
            Embedding optimized for search
        """
        # For skill-focused queries, emphasize technical precision
        if query_type == "skill_focused" and self.cohere_api_key:
            # Use Cohere for technical queries
            return await self.get_embedding(
                query,
                EmbeddingModel.COHERE_ENGLISH,
                use_cache=True
            )
        
        # For general queries, use OpenAI
        return await self.get_embedding(
            query,
            EmbeddingModel.OPENAI_SMALL,
            use_cache=True
        )
    
    async def batch_embed_texts(
        self,
        texts: List[str],
        model: EmbeddingModel = EmbeddingModel.OPENAI_SMALL,
        batch_size: int = 100
    ) -> List[List[float]]:
        """
        Embed multiple texts efficiently in batches.
        
        Args:
            texts: List of texts to embed
            model: Embedding model to use
            batch_size: Number of texts per batch
            
        Returns:
            List of embeddings
        """
        embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            if model in [EmbeddingModel.OPENAI_SMALL, EmbeddingModel.OPENAI_LARGE]:
                # OpenAI supports batch embedding
                if self.openai_client:
                    try:
                        response = await self.openai_client.embeddings.create(
                            model=model.value,
                            input=batch
                        )
                        batch_embeddings = [e.embedding for e in response.data]
                        embeddings.extend(batch_embeddings)
                    except Exception as e:
                        logger.error(f"Batch embedding error: {e}")
                        # Fallback to individual
                        for text in batch:
                            emb = await self.get_embedding(text, model)
                            embeddings.append(emb)
            else:
                # Process individually for other models
                for text in batch:
                    emb = await self.get_embedding(text, model)
                    embeddings.append(emb)
        
        return embeddings
    
    def compute_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float],
        metric: str = "cosine"
    ) -> float:
        """
        Compute similarity between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            metric: Similarity metric (cosine, euclidean, dot)
            
        Returns:
            Similarity score
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        if metric == "cosine":
            # Cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
                
            return float(dot_product / (norm1 * norm2))
            
        elif metric == "euclidean":
            # Euclidean distance (inverted to similarity)
            distance = np.linalg.norm(vec1 - vec2)
            return float(1 / (1 + distance))
            
        elif metric == "dot":
            # Dot product
            return float(np.dot(vec1, vec2))
            
        else:
            raise ValueError(f"Unknown similarity metric: {metric}")
    
    async def find_optimal_model(
        self,
        sample_queries: List[str],
        sample_documents: List[str],
        ground_truth_matches: List[Tuple[int, int]]
    ) -> Dict[str, Any]:
        """
        Find optimal embedding model for a specific use case.
        
        Args:
            sample_queries: Sample search queries
            sample_documents: Sample documents
            ground_truth_matches: List of (query_idx, doc_idx) pairs
            
        Returns:
            Analysis of model performance
        """
        results = {}
        
        for model in self.default_models:
            # Embed queries and documents
            query_embeddings = await self.batch_embed_texts(sample_queries, model)
            doc_embeddings = await self.batch_embed_texts(sample_documents, model)
            
            # Compute all similarities
            correct_matches = 0
            avg_rank = 0
            
            for query_idx, true_doc_idx in ground_truth_matches:
                query_emb = query_embeddings[query_idx]
                
                # Compute similarities to all documents
                similarities = []
                for doc_idx, doc_emb in enumerate(doc_embeddings):
                    sim = self.compute_similarity(query_emb, doc_emb)
                    similarities.append((doc_idx, sim))
                
                # Sort by similarity
                similarities.sort(key=lambda x: x[1], reverse=True)
                
                # Find rank of true match
                rank = next(
                    i for i, (doc_idx, _) in enumerate(similarities)
                    if doc_idx == true_doc_idx
                ) + 1
                
                avg_rank += rank
                if rank == 1:
                    correct_matches += 1
            
            results[model.value] = {
                "accuracy": correct_matches / len(ground_truth_matches),
                "avg_rank": avg_rank / len(ground_truth_matches),
                "model": model.value,
                "dimensions": self.model_dims[model]
            }
        
        return results


# Singleton instance
embedding_ensemble = EmbeddingEnsemble()