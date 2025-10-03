import unittest
import tempfile
import shutil
import os
import time
from pathlib import Path
import yaml
import json
import subprocess
from unittest.mock import patch
import logging

from src.eless_pipeline import ElessPipeline
from src.core.state_manager import StateManager
from src.core.config_loader import ConfigLoader
from src.database.db_loader import DatabaseLoader

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TestEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Setup test environment with multiple file types and configurations."""
        # Create temporary test environment
        cls.temp_dir = tempfile.mkdtemp(prefix='eless_e2e_test_')
        cls.cache_dir = tempfile.mkdtemp(prefix='eless_e2e_cache_')
        cls.db_dir = tempfile.mkdtemp(prefix='eless_e2e_db_')
        
        # Load base configuration
        config_path = Path(__file__).parent / 'fixtures' / 'test_config.yaml'
        with open(config_path, 'r') as f:
            cls.base_config = yaml.safe_load(f)
        
        # Update paths
        cls.base_config['cache']['directory'] = cls.cache_dir
        cls.base_config['database']['path'] = str(Path(cls.db_dir) / 'test.db')
        
        # Create test files directory
        cls.test_files_dir = Path(cls.temp_dir) / 'test_files'
        cls.test_files_dir.mkdir(exist_ok=True)
        
        # Create various test files
        cls.create_test_files()

    @classmethod
    def create_test_files(cls):
        """Create various test files for processing."""
        # Text files
        text_dir = cls.test_files_dir / 'text'
        text_dir.mkdir(exist_ok=True)
        
        # Small text file
        with open(text_dir / 'small.txt', 'w') as f:
            f.write("This is a small test file.\nIt has multiple lines.\n")
        
        # Medium text file
        with open(text_dir / 'medium.txt', 'w') as f:
            f.write('x' * 1024 * 10)  # 10KB file
        
        # Large text file
        with open(text_dir / 'large.txt', 'w') as f:
            f.write('x' * 1024 * 1024)  # 1MB file
        
        # Create binary files
        binary_dir = cls.test_files_dir / 'binary'
        binary_dir.mkdir(exist_ok=True)
        with open(binary_dir / 'binary.bin', 'wb') as f:
            f.write(os.urandom(1024))

        # Create test PDF content
        pdf_dir = cls.test_files_dir / 'pdf'
        pdf_dir.mkdir(exist_ok=True)
        cls.create_test_pdf(pdf_dir / 'test.pdf')

        # Create test Word document
        doc_dir = cls.test_files_dir / 'doc'
        doc_dir.mkdir(exist_ok=True)
        cls.create_test_doc(doc_dir / 'test.docx')

    @classmethod
    def create_test_pdf(cls, path):
        """Create a test PDF file."""
        try:
            from reportlab.pdfgen import canvas
            c = canvas.Canvas(str(path))
            c.drawString(100, 750, "Test PDF Document")
            c.drawString(100, 700, "This is a test PDF file for ELESS testing.")
            c.save()
        except ImportError:
            logger.warning("Could not create PDF test file - reportlab not installed")
            # Create a dummy file
            path.touch()

    @classmethod
    def create_test_doc(cls, path):
        """Create a test Word document."""
        try:
            from docx import Document
            doc = Document()
            doc.add_heading('Test Document', 0)
            doc.add_paragraph('This is a test document for ELESS testing.')
            doc.save(str(path))
        except ImportError:
            logger.warning("Could not create DOCX test file - python-docx not installed")
            # Create a dummy file
            path.touch()

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        shutil.rmtree(cls.temp_dir, ignore_errors=True)
        shutil.rmtree(cls.cache_dir, ignore_errors=True)
        shutil.rmtree(cls.db_dir, ignore_errors=True)

    def setUp(self):
        """Setup for each test."""
        self.config = self.base_config.copy()
        self.pipeline = ElessPipeline(self.config)
        self.state_manager = StateManager(self.config)

    def test_full_pipeline_text_only(self):
        """Test full pipeline with text files only."""
        # Process text directory
        text_dir = self.test_files_dir / 'text'
        self.pipeline.run_process(str(text_dir))

        # Verify processing
        processed_files = self.state_manager.get_all_files()
        self.assertEqual(len(processed_files), 3)  # small, medium, large
        self.assertTrue(all(f['status'] == 'LOADED' for f in processed_files))

        # Check cache
        cache_files = list(Path(self.cache_dir).glob('*'))
        self.assertGreater(len(cache_files), 0)

        # Check database
        db_path = Path(self.config['database']['path'])
        self.assertTrue(db_path.exists())

    def test_full_pipeline_all_types(self):
        """Test full pipeline with all file types."""
        # Process entire test files directory
        self.pipeline.run_process(str(self.test_files_dir))

        # Verify processing
        processed_files = self.state_manager.get_all_files()
        txt_files = [f for f in processed_files if f['path'].endswith('.txt')]
        pdf_files = [f for f in processed_files if f['path'].endswith('.pdf')]
        doc_files = [f for f in processed_files if f['path'].endswith('.docx')]

        # Check text files
        self.assertEqual(len(txt_files), 3)
        self.assertTrue(all(f['status'] == 'LOADED' for f in txt_files))

        # Check PDF files (if supported)
        if len(pdf_files) > 0:
            self.assertTrue(all(f['status'] == 'LOADED' for f in pdf_files))

        # Check Doc files (if supported)
        if len(doc_files) > 0:
            self.assertTrue(all(f['status'] == 'LOADED' for f in doc_files))

    def test_interrupted_processing(self):
        """Test pipeline with interruption and resume."""
        # Start processing
        text_dir = self.test_files_dir / 'text'
        
        def interrupt_after_first_file():
            """Mock function to simulate interruption after first file."""
            processed_files = self.state_manager.get_all_files()
            if len(processed_files) >= 1:
                raise KeyboardInterrupt

        # Run with interruption
        try:
            with patch('src.core.state_manager.StateManager.get_all_files', 
                      side_effect=interrupt_after_first_file):
                self.pipeline.run_process(str(text_dir))
        except KeyboardInterrupt:
            pass

        # Check partial processing
        initial_files = self.state_manager.get_all_files()
        self.assertLess(len(initial_files), 3)  # Should not have processed all files

        # Resume processing
        self.pipeline.run_resume()

        # Verify completion
        final_files = self.state_manager.get_all_files()
        self.assertEqual(len(final_files), 3)
        self.assertTrue(all(f['status'] == 'LOADED' for f in final_files))

    def test_different_configurations(self):
        """Test pipeline with different configurations."""
        test_configs = [
            # Minimal parallel processing
            {
                'parallel_processing': {
                    'enable_parallel_files': False,
                    'enable_parallel_chunks': False
                }
            },
            # Aggressive parallel processing
            {
                'parallel_processing': {
                    'max_workers': 4,
                    'chunk_batch_size': 10,
                    'file_batch_size': 5
                }
            },
            # Conservative resource limits
            {
                'resource_limits': {
                    'memory_warning_percent': 60,
                    'max_file_size_mb': 5
                }
            }
        ]

        for mod_config in test_configs:
            # Update configuration
            test_config = self.base_config.copy()
            for section, settings in mod_config.items():
                if section not in test_config:
                    test_config[section] = {}
                test_config[section].update(settings)

            # Clear previous state and cache
            shutil.rmtree(self.cache_dir, ignore_errors=True)
            Path(self.cache_dir).mkdir(exist_ok=True)
            self.state_manager.clear_state()

            # Run pipeline with new config
            pipeline = ElessPipeline(test_config)
            pipeline.run_process(str(self.test_files_dir / 'text'))

            # Verify processing
            processed_files = self.state_manager.get_all_files()
            self.assertTrue(any(f['status'] == 'LOADED' for f in processed_files))

    def test_cli_end_to_end(self):
        """Test end-to-end processing using CLI."""
        # Save test config
        config_path = Path(self.temp_dir) / 'cli_config.yaml'
        with open(config_path, 'w') as f:
            yaml.dump(self.config, f)

        # Test CLI commands
        cli_tests = [
            # Process command
            ['process', '--config', str(config_path), 
             str(self.test_files_dir / 'text' / 'small.txt')],
            
            # Status command
            ['status', '--config', str(config_path)],
            
            # Process directory
            ['process', '--config', str(config_path), 
             str(self.test_files_dir / 'text')],
            
            # Resume command
            ['resume', '--config', str(config_path)],
        ]

        for args in cli_tests:
            # Run CLI command
            result = subprocess.run(
                ['python', '-m', 'eless'] + args,
                capture_output=True,
                text=True
            )
            self.assertEqual(result.returncode, 0,
                           f"CLI command failed: {' '.join(args)}\n{result.stderr}")

    def test_streaming_performance(self):
        """Test streaming performance with large files."""
        # Create a very large file
        large_file = self.test_files_dir / 'text' / 'very_large.txt'
        with open(large_file, 'w') as f:
            f.write('x' * (1024 * 1024 * 5))  # 5MB file

        # Process with streaming
        start_time = time.time()
        self.pipeline.run_process(str(large_file))
        processing_time = time.time() - start_time

        # Verify processing
        file_hash = self.state_manager.get_file_hash(str(large_file))
        status = self.state_manager.get_status(file_hash)
        self.assertEqual(status, 'LOADED')

        # Check memory usage
        memory_metrics = self.pipeline.resource_monitor.get_current_metrics()
        logger.info(f"Memory usage after processing: {memory_metrics.memory_percent}%")
        self.assertLess(memory_metrics.memory_percent, 90)  # Should not use excessive memory

        logger.info(f"Large file processing time: {processing_time:.2f} seconds")

    def test_database_operations(self):
        """Test database operations end-to-end."""
        # Process some files
        text_dir = self.test_files_dir / 'text'
        self.pipeline.run_process(str(text_dir))

        # Get database loader
        db_loader = DatabaseLoader(self.config, self.state_manager)

        # Test database queries
        test_queries = [
            "Test",  # Simple text query
            "file",  # Common word
            "nonexistent",  # Should return no results
        ]

        for query in test_queries:
            results = db_loader.search(query)
            if query != "nonexistent":
                self.assertGreater(len(results), 0)
            else:
                self.assertEqual(len(results), 0)

        # Test batch operations
        batch_data = [
            {'id': 'test1', 'text': 'test content 1', 'embedding': [0.1] * 384},
            {'id': 'test2', 'text': 'test content 2', 'embedding': [0.2] * 384}
        ]
        db_loader.batch_upsert(batch_data)

        # Verify batch insert
        results = db_loader.search("test content")
        self.assertGreater(len(results), 0)

if __name__ == '__main__':
    unittest.main()