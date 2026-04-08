from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, func, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector  # The AI Component
from app.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    
    # Identity
    product_id = Column(String, unique=True, index=True)  # ASIN or similar ID
    platform = Column(String, index=True)       # 'amazon', 'flipkart', 'generic'
    title = Column(String)
    
    # AI Intelligence
    specs = Column(JSON, default={})            # Cleaned specs: {"watts": 750, "color": "black"}
    ai_analysis = Column(JSON, default={})      # AI generated insights (Jargon Buster, Eco Meter)
    images = Column(JSON, default=[])           # ["url1.jpg", "url2.jpg"]
    
    # 🧠 THE TWIN FINDER KEY
    # 768 dimensions matches Gemini's text-embedding-004 model
    fingerprint = Column(Vector(768), nullable=True)
    
    # Metadata
    source_url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    price_history = relationship("PriceHistory", back_populates="product")


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), index=True)
    
    # Price Data
    price = Column(Float)
    currency = Column(String, default="INR")
    
    # Product Info (snapshot at time of price recording)
    title = Column(String, nullable=True)  # Product title at time of recording
    
    # Cold Start Data (Solution to your doubt earlier!)
    list_price = Column(Float, nullable=True)  # MRP / Strike-through price
    
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    product = relationship("Product", back_populates="price_history")


class PriceAlert(Base):
    __tablename__ = "price_alerts"

    id = Column(Integer, primary_key=True, index=True)
    product_url = Column(String, index=True)
    target_price = Column(Float)
    email = Column(String)
    is_active = Column(Boolean, default=True)
    last_checked = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
