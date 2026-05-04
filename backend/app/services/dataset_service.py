"""Dataset service for fine-tuning data management."""
import json
import uuid
import hashlib
from pathlib import Path
from typing import Optional, AsyncIterator
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
import pandas as pd

from app.models.finetune import Dataset
from app.core.config import settings


class DatasetService:
    """Service for managing fine-tuning datasets."""
    
    SUPPORTED_FORMATS = ["jsonl", "parquet", "csv"]
    SUPPORTED_TYPES = ["conversation", "sharegpt", "alpaca"]
    
    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        self.upload_dir = Path(settings.DATA_DIR) / "datasets"
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_dataset(
        self,
        name: str,
        file_path: str,
        file_name: str,
        file_size: int,
        file_format: str,
        format_type: str = "conversation",
        description: Optional[str] = None,
    ) -> Dataset:
        """Create a new dataset record."""
        dataset_id = str(uuid.uuid4())
        
        # Calculate storage path
        storage_name = f"{dataset_id}_{file_name}"
        storage_path = str(self.upload_dir / storage_name)
        
        dataset = Dataset(
            id=dataset_id,
            user_id=self.user_id,
            name=name,
            description=description,
            file_name=file_name,
            file_path=storage_path,
            file_size=file_size,
            file_format=file_format,
            format_type=format_type,
        )
        
        self.db.add(dataset)
        await self.db.commit()
        await self.db.refresh(dataset)
        
        return dataset
    
    async def upload_dataset(
        self,
        name: str,
        content: bytes,
        file_name: str,
        format_type: str = "conversation",
        description: Optional[str] = None,
    ) -> Dataset:
        """Upload and process a dataset file."""
        # Determine file format
        file_ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else "jsonl"
        if file_ext not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported file format: {file_ext}. Supported: {self.SUPPORTED_FORMATS}")
        
        file_size = len(content)
        
        # Create dataset record first
        dataset = await self.create_dataset(
            name=name,
            file_path="",  # Will be updated after save
            file_name=file_name,
            file_size=file_size,
            file_format=file_ext,
            format_type=format_type,
            description=description,
        )
        
        # Save file
        storage_name = f"{dataset.id}_{file_name}"
        storage_path = self.upload_dir / storage_name
        storage_path.write_bytes(content)
        
        # Update path in record
        dataset.file_path = str(storage_path)
        await self.db.commit()
        
        # Process and validate
        await self._process_dataset(dataset)
        
        return dataset
    
    async def _process_dataset(self, dataset: Dataset) -> None:
        """Process and validate dataset, calculate statistics."""
        file_path = Path(dataset.file_path)
        
        if dataset.file_format == "jsonl":
            samples = await self._load_jsonl(file_path)
        elif dataset.file_format == "csv":
            samples = await self._load_csv(file_path)
        elif dataset.file_format == "parquet":
            samples = await self._load_parquet(file_path)
        else:
            raise ValueError(f"Unsupported format: {dataset.file_format}")
        
        # Validate format
        errors = await self._validate_samples(samples, dataset.format_type)
        
        if errors:
            dataset.validation_errors = {"errors": errors, "sample_count": len(samples)}
        else:
            dataset.is_validated = True
            dataset.validation_errors = None
        
        # Calculate statistics
        stats = self._calculate_statistics(samples, dataset.format_type)
        dataset.total_samples = stats["total_samples"]
        dataset.total_tokens = stats["total_tokens"]
        dataset.avg_turns = stats["avg_turns"]
        
        await self.db.commit()
        await self.db.refresh(dataset)
    
    async def _load_jsonl(self, path: Path) -> list[dict]:
        """Load JSONL file."""
        samples = []
        async for line in self._read_file_lines(path):
            try:
                samples.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return samples
    
    async def _load_csv(self, path: Path) -> list[dict]:
        """Load CSV file as list of dicts."""
        df = pd.read_csv(path)
        return df.to_dict("records")
    
    async def _load_parquet(self, path: Path) -> list[dict]:
        """Load Parquet file as list of dicts."""
        df = pd.read_parquet(path)
        return df.to_dict("records")
    
    async def _read_file_lines(self, path: Path) -> AsyncIterator[str]:
        """Read file line by line."""
        content = path.read_text()
        for line in content.split("\n"):
            if line.strip():
                yield line
    
    async def _validate_samples(
        self,
        samples: list[dict],
        format_type: str
    ) -> list[str]:
        """Validate samples against format type."""
        errors = []
        
        for i, sample in enumerate(samples[:100]):  # Validate first 100
            if format_type == "conversation":
                if "messages" not in sample and "conversations" not in sample:
                    errors.append(f"Sample {i}: Missing 'messages' or 'conversations' field")
                else:
                    messages = sample.get("messages") or sample.get("conversations", [])
                    if not isinstance(messages, list):
                        errors.append(f"Sample {i}: 'messages' must be a list")
            
            elif format_type == "sharegpt":
                if "conversations" not in sample:
                    errors.append(f"Sample {i}: Missing 'conversations' field")
            
            elif format_type == "alpaca":
                required = ["instruction", "input", "output"]
                missing = [f for f in required if f not in sample]
                if missing:
                    errors.append(f"Sample {i}: Missing fields: {missing}")
        
        return errors
    
    def _calculate_statistics(
        self,
        samples: list[dict],
        format_type: str
    ) -> dict:
        """Calculate dataset statistics."""
        total_tokens = 0
        total_turns = 0
        
        for sample in samples:
            if format_type == "conversation":
                messages = sample.get("messages") or sample.get("conversations", [])
                total_turns += len(messages)
                # Rough token estimation: 4 chars per token
                total_tokens += sum(len(str(m.get("content", ""))) for m in messages) // 4
            
            elif format_type == "sharegpt":
                messages = sample.get("conversations", [])
                total_turns += len(messages)
                total_tokens += sum(len(str(m.get("value", ""))) for m in messages) // 4
            
            elif format_type == "alpaca":
                text = f"{sample.get('instruction', '')} {sample.get('input', '')} {sample.get('output', '')}"
                total_tokens += len(text) // 4
                total_turns += 1
        
        avg_turns = total_turns / len(samples) if samples else 0
        
        return {
            "total_samples": len(samples),
            "total_tokens": int(total_tokens),
            "avg_turns": round(avg_turns, 2),
        }
    
    async def get_dataset(self, dataset_id: str) -> Optional[Dataset]:
        """Get dataset by ID."""
        result = await self.db.execute(
            select(Dataset).where(
                Dataset.id == dataset_id,
                Dataset.user_id == self.user_id
            )
        )
        return result.scalar_one_or_none()
    
    async def list_datasets(
        self,
        skip: int = 0,
        limit: int = 20,
        validated_only: bool = False,
    ) -> tuple[list[Dataset], int]:
        """List datasets with pagination."""
        query = select(Dataset).where(Dataset.user_id == self.user_id)
        
        if validated_only:
            query = query.where(Dataset.is_validated == True)
        
        # Count total
        count_query = select(func.count(Dataset.id)).where(Dataset.user_id == self.user_id)
        if validated_only:
            count_query = count_query.where(Dataset.is_validated == True)
        total = (await self.db.execute(count_query)).scalar()
        
        # Get paginated results
        query = query.order_by(Dataset.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        datasets = result.scalars().all()
        
        return list(datasets), total
    
    async def delete_dataset(self, dataset_id: str) -> bool:
        """Delete a dataset."""
        dataset = await self.get_dataset(dataset_id)
        if not dataset:
            return False
        
        # Delete file
        file_path = Path(dataset.file_path)
        if file_path.exists():
            file_path.unlink()
        
        # Delete record
        await self.db.delete(dataset)
        await self.db.commit()
        
        return True
    
    async def preview_dataset(
        self,
        dataset_id: str,
        limit: int = 5
    ) -> Optional[list[dict]]:
        """Get preview of dataset samples."""
        dataset = await self.get_dataset(dataset_id)
        if not dataset:
            return None
        
        file_path = Path(dataset.file_path)
        samples = []
        
        if dataset.file_format == "jsonl":
            content = file_path.read_text()
            for i, line in enumerate(content.split("\n")):
                if i >= limit:
                    break
                if line.strip():
                    try:
                        samples.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        
        return samples
    
    async def split_dataset(
        self,
        dataset_id: str,
        train_ratio: float = 0.9,
        validation_ratio: float = 0.1
    ) -> Optional[dict]:
        """Split dataset into train/validation sets."""
        dataset = await self.get_dataset(dataset_id)
        if not dataset:
            return None
        
        if train_ratio + validation_ratio != 1.0:
            raise ValueError("Train and validation ratios must sum to 1.0")
        
        dataset.train_ratio = train_ratio
        dataset.validation_ratio = validation_ratio
        
        await self.db.commit()
        await self.db.refresh(dataset)
        
        return {
            "dataset_id": dataset.id,
            "train_ratio": train_ratio,
            "validation_ratio": validation_ratio,
            "estimated_train_samples": int(dataset.total_samples * train_ratio),
            "estimated_validation_samples": int(dataset.total_samples * validation_ratio),
        }
