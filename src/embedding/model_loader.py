import logging
from typing import Dict, Any, List, Union, Optional
from pathlib import Path

import numpy as np

# Import logging performance decorator
from ..core.logging_config import log_performance

# Try to import sentence transformers with fallback
try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None

logger = logging.getLogger("ELESS.ModelLoader")


class ModelLoader:
    """
    A wrapper class for loading and managing the low-resource embedding model
    (e.g., a Sentence Transformer model).
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the model wrapper, loading the specified model from the
        configuration.
        """
        self.config = config
        self.model_name = config["embedding"]["model_name"]
        self.device = config["embedding"]["device"]
        self.model = self._load_model()

        if self.model:
            # Get the dimension of the embeddings produced by this model
            self.embedding_dimension = self.model.get_sentence_embedding_dimension()
            logger.info(
                f"Embedding model loaded: {self.model_name} (Dim: {self.embedding_dimension}) on {self.device}."
            )
        else:
            # Set default dimension from config or use a reasonable default
            self.embedding_dimension = config["embedding"].get("dimensions", 384)
            logger.error(f"Failed to load embedding model: {self.model_name}")

    @log_performance("ELESS.ModelLoader")
    def _load_model(self) -> Optional["SentenceTransformer"]:
        """
        Loads the SentenceTransformer model onto the configured device (CPU/GPU).
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.error(
                "SentenceTransformers library not available. Install with: pip install sentence-transformers"
            )
            return None

        logger.info(
            f"Loading embedding model: {self.model_name} on device: {self.device}"
        )
        try:
            # Setting trust_remote_code=True may be required for some custom models
            model = SentenceTransformer(
                model_name_or_path=self.model_name,
                device=self.device,
                trust_remote_code=self.config["embedding"].get(
                    "trust_remote_code", False
                ),
            )
            logger.info(f"Successfully loaded model {self.model_name}")
            return model
        except Exception as e:
            logger.critical(
                f"Failed to load embedding model '{self.model_name}' on device '{self.device}'. Error: {e}"
            )
            logger.critical(
                "Ensure the model name is correct and necessary dependencies (like PyTorch/TensorFlow) are installed."
            )
            # Return None instead of raising to allow graceful handling
            return None

    @log_performance("ELESS.ModelLoader")
    def embed_chunks(self, texts: List[str]) -> np.ndarray:
        """
        Generates vector embeddings for a list of text strings.

        Args:
            texts: A list of text chunks (strings) to be encoded.

        Returns:
            A NumPy array of shape (N, D), where N is the number of texts
            and D is the embedding dimension.
        """
        if not texts:
            logger.debug("Empty text list provided, returning empty array")
            return np.array([])

        if not self.model:
            logger.error("Model not loaded, cannot embed texts")
            raise RuntimeError("Embedding model not loaded")

        logger.info(f"Encoding {len(texts)} chunks...")

        try:
            # Use the model's encode method
            embeddings = self.model.encode(
                sentences=texts,
                batch_size=self.config["embedding"]["batch_size"],
                show_progress_bar=False,
                convert_to_numpy=True,
            )

            logger.debug(
                f"Successfully generated embeddings with shape: {embeddings.shape}"
            )
            # The output 'embeddings' is a NumPy array
            return embeddings

        except Exception as e:
            logger.error(f"Error during batch embedding: {e}", exc_info=True)
            # Return an empty array or raise a specific error
            raise RuntimeError(f"Embedding failure: {e}")

    def get_dimension(self) -> int:
        """Returns the output dimension of the embeddings."""
        return self.embedding_dimension
