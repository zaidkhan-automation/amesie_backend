from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
import os
import uuid
from datetime import datetime
import logging

import sys
# import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_db
from db import models
from schemas import schemas
from services.auth import get_current_user
from core.logging_config import get_logger

router = APIRouter()
seller_logger = get_logger('seller')

# Allowed image extensions
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
UPLOAD_DIR = "../frontend/static/uploads"

# Ensure upload directory exists
os.makedirs(f"{UPLOAD_DIR}/profile_pictures", exist_ok=True)
os.makedirs(f"{UPLOAD_DIR}/product_images", exist_ok=True)

async def save_upload_file(file: UploadFile, upload_type: str = "profile_pictures") -> str:
    """Save uploaded file and return the file path"""
    # Validate file size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large. Maximum size is 5MB."
        )
    
    # Validate file extension
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided."
        )
    
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only JPG, JPEG, PNG, GIF, and WebP are allowed."
        )
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = f"{UPLOAD_DIR}/{upload_type}/{unique_filename}"
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(contents)
    
    return f"/{file_path}"  # Return web-accessible path

def get_current_seller(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Ensure current user is a seller and return their seller profile"""
    # if current_user.role != models.UserRole.SELLER:
    if current_user.role.value != models.UserRole.SELLER.value:
        seller_logger.warning(f"Non-seller user attempted to access seller resource: {current_user.email} (Role: {current_user.role.value})")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Seller role required."
        )
    
    seller = db.query(models.Seller).filter(models.Seller.user_id == current_user.id).first()
    if not seller:
        seller_logger.error(f"Seller profile not found for user: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seller profile not found"
        )
    
    seller_logger.info(f"Seller access granted: {current_user.email} (Store: {seller.store_name})")
    return seller

@router.get("/profile", response_model=schemas.Seller)
def get_seller_profile(seller: models.Seller = Depends(get_current_seller)):
    """Get current seller's profile"""
    seller_logger.info(f"Profile accessed by seller: {seller.store_name}")
    return seller

@router.put("/profile", response_model=schemas.Seller)
def update_seller_profile(
    seller_update: schemas.SellerUpdate,
    seller: models.Seller = Depends(get_current_seller),
    db: Session = Depends(get_db)
):
    """Update seller profile"""
    seller_logger.info(f"Profile update initiated by seller: {seller.store_name}")
    update_data = seller_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(seller, field, value)
    
    db.commit()
    db.refresh(seller)
    seller_logger.info(f"Profile updated successfully for seller: {seller.store_name}")
    return seller

@router.get("/products", response_model=List[schemas.Product])
def get_seller_products(
    skip: int = 0,
    limit: int = 20,
    include_deleted: bool = False,
    seller: models.Seller = Depends(get_current_seller),
    db: Session = Depends(get_db)
):
    """Get all products for current seller"""
    query = db.query(models.Product).filter(models.Product.seller_id == seller.id)
    
    # Filter out deleted products unless specifically requested
    if not include_deleted:
        query = query.filter(models.Product.is_deleted == False)
    
    products = query.offset(skip).limit(limit).all()
    return products

@router.post("/products", response_model=schemas.Product)
def create_product(
    product: schemas.ProductCreate,
    seller: models.Seller = Depends(get_current_seller),
    db: Session = Depends(get_db)
):
    """Create a new product for the seller"""
    # Verify category exists
    category = db.query(models.Category).filter(models.Category.id == product.category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Check if SKU already exists
    existing_product = db.query(models.Product).filter(models.Product.sku == product.sku).first()
    if existing_product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product with this SKU already exists"
        )
    
    db_product = models.Product(
        name=product.name,
        description=product.description,
        price=product.price,
        sku=product.sku,
        image_url=product.image_url,
        stock_quantity=product.stock_quantity,
        weight=product.weight,
        length=product.length,
        width=product.width,
        height=product.height,
        shipping_info=product.shipping_info,
        category_id=product.category_id,
        seller_id=seller.id
    )
    
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    # Add product images if provided
    if product.images:
        for i, image_data in enumerate(product.images):
            product_image = models.ProductImage(
                product_id=db_product.id,
                image_url=image_data.image_url,
                alt_text=image_data.alt_text or f"{product.name} image {i + 1}",
                display_order=image_data.display_order or i
            )
            db.add(product_image)
        
        # Set main image if not provided and images exist
        if not db_product.image_url and product.images:
            db_product.image_url = product.images[0].image_url
    
    db.commit()
    db.refresh(db_product)
    
    # Create notification for admin about new product
    notification = models.Notification(
        user_id=1,  # Admin user ID
        title="New Product Added",
        message=f"Seller '{seller.store_name}' added a new product: {product.name}",
        notification_type=models.NotificationType.ORDER_PLACED  # Reusing enum for now
    )
    db.add(notification)
    db.commit()
    
    return db_product

@router.put("/products/{product_id}", response_model=schemas.Product)
def update_product(
    product_id: int,
    product_update: schemas.ProductUpdate,
    seller: models.Seller = Depends(get_current_seller),
    db: Session = Depends(get_db)
):
    """Update a product owned by the seller"""
    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.seller_id == seller.id,
        models.Product.is_deleted == False
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or access denied"
        )
    
    # Check if new SKU conflicts with existing products
    if product_update.sku and product_update.sku != product.sku:
        existing_product = db.query(models.Product).filter(
            models.Product.sku == product_update.sku,
            models.Product.id != product_id
        ).first()
        if existing_product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product with this SKU already exists"
            )
    
    update_data = product_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    db.commit()
    db.refresh(product)
    return product

@router.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    permanent: bool = False,
    seller: models.Seller = Depends(get_current_seller),
    db: Session = Depends(get_db)
):
    """Soft delete or permanently delete a product owned by the seller"""
    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.seller_id == seller.id
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or access denied"
        )
    
    if permanent:
        # Permanent delete - remove from database completely
        db.delete(product)
        message = "Product permanently deleted"
    else:
        # Soft delete - mark as deleted
        product.is_deleted = True
        product.deleted_at = datetime.utcnow()
        product.is_active = False
        message = "Product deleted successfully"
    
    db.commit()
    return {"message": message}

@router.post("/products/{product_id}/restore")
def restore_product(
    product_id: int,
    seller: models.Seller = Depends(get_current_seller),
    db: Session = Depends(get_db)
):
    """Restore a soft-deleted product"""
    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.seller_id == seller.id,
        models.Product.is_deleted == True
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deleted product not found or access denied"
        )
    
    product.is_deleted = False
    product.deleted_at = None
    product.is_active = True
    
    db.commit()
    db.refresh(product)
    
    return {"message": "Product restored successfully", "product": product}

@router.get("/orders", response_model=List[schemas.Order])
def get_seller_orders(
    seller: models.Seller = Depends(get_current_seller),
    db: Session = Depends(get_db)
):
    """Get all orders containing seller's products"""
    orders = db.query(models.Order).join(models.OrderItem).join(models.Product).filter(
        models.Product.seller_id == seller.id
    ).distinct().all()
    
    return orders

@router.put("/orders/{order_id}/status")
def update_order_status(
    order_id: int,
    status_update: dict,
    seller: models.Seller = Depends(get_current_seller),
    db: Session = Depends(get_db)
):
    """Update order status for orders containing seller's products"""
    order = db.query(models.Order).join(models.OrderItem).join(models.Product).filter(
        models.Order.id == order_id,
        models.Product.seller_id == seller.id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found or access denied"
        )
    
    new_status = status_update.get("status")
    if new_status not in ["confirmed", "shipped", "delivered"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status. Allowed: confirmed, shipped, delivered"
        )
    
    # Update order status
    db.query(models.Order).filter(models.Order.id == order_id).update({"order_status": new_status})
    db.commit()
    
    # Create notification for customer
    if new_status == "shipped":
        notification_message = f"Your order #{order_id} has been shipped by {seller.store_name}"
        notification_type = models.NotificationType.ORDER_SHIPPED
    elif new_status == "delivered":
        notification_message = f"Your order #{order_id} has been delivered!"
        notification_type = models.NotificationType.ORDER_DELIVERED
    else:
        notification_message = f"Your order #{order_id} has been confirmed by {seller.store_name}"
        notification_type = models.NotificationType.ORDER_CONFIRMED
    
    notification = models.Notification(
        user_id=order.user_id,
        title="Order Status Update",
        message=notification_message,
        notification_type=notification_type,
        order_id=order_id
    )
    db.add(notification)
    db.commit()
    
    return {"message": f"Order status updated to {new_status}"}

@router.get("/dashboard/stats")
def get_seller_dashboard_stats(
    seller: models.Seller = Depends(get_current_seller),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics for seller"""
    # Total products
    total_products = db.query(models.Product).filter(models.Product.seller_id == seller.id).count()
    
    # Total orders
    total_orders = db.query(models.Order).join(models.OrderItem).join(models.Product).filter(
        models.Product.seller_id == seller.id
    ).distinct().count()
    
    # Pending orders
    pending_orders = db.query(models.Order).join(models.OrderItem).join(models.Product).filter(
        models.Product.seller_id == seller.id,
        models.Order.order_status == "pending"
    ).distinct().count()
    
    # Low stock products (less than 10 items)
    low_stock_products = db.query(models.Product).filter(
        models.Product.seller_id == seller.id,
        models.Product.stock_quantity < 10
    ).count()
    
    return {
        "total_products": total_products,
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "low_stock_products": low_stock_products,
        "total_sales": seller.total_sales,
        "store_rating": seller.rating
    }

# Add missing API endpoints that the frontend expects
@router.get("/me/dashboard-stats")
def get_my_dashboard_stats(seller: models.Seller = Depends(get_current_seller), db: Session = Depends(get_db)):
    """Get dashboard stats for current seller (alternative endpoint for frontend)"""
    return get_seller_dashboard_stats(seller, db)

@router.post("/upload-profile-picture", response_model=schemas.ImageUploadResponse)
async def upload_profile_picture(
    file: UploadFile = File(...),
    seller: models.Seller = Depends(get_current_seller),
    db: Session = Depends(get_db)
):
    """Upload seller profile picture"""
    try:
        # Save the uploaded file
        file_path = await save_upload_file(file, "profile_pictures")
        
        # Update seller profile with new picture URL
        seller.profile_picture_url = file_path
        db.commit()
        db.refresh(seller)
        
        return schemas.ImageUploadResponse(
            image_url=file_path,
            message="Profile picture uploaded successfully"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload profile picture: {str(e)}"
        )

@router.post("/upload-store-logo", response_model=schemas.ImageUploadResponse)
async def upload_store_logo(
    file: UploadFile = File(...),
    seller: models.Seller = Depends(get_current_seller),
    db: Session = Depends(get_db)
):
    """Upload seller store logo"""
    try:
        # Save the uploaded file
        file_path = await save_upload_file(file, "profile_pictures")
        
        # Update seller profile with new logo URL
        seller.store_logo_url = file_path
        db.commit()
        db.refresh(seller)
        
        return schemas.ImageUploadResponse(
            image_url=file_path,
            message="Store logo uploaded successfully"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload store logo: {str(e)}"
        )

@router.post("/products/{product_id}/upload-images", response_model=List[schemas.ImageUploadResponse])
async def upload_product_images(
    product_id: int,
    files: List[UploadFile] = File(...),
    seller: models.Seller = Depends(get_current_seller),
    db: Session = Depends(get_db)
):
    """Upload multiple images for a product (max 10)"""
    # Verify product belongs to seller
    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.seller_id == seller.id,
        models.Product.is_deleted == False
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or access denied"
        )
    
    # Check current image count
    current_images = db.query(models.ProductImage).filter(
        models.ProductImage.product_id == product_id
    ).count()
    
    if current_images + len(files) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum 10 images allowed per product. Current: {current_images}"
        )
    
    uploaded_images = []
    
    try:
        for i, file in enumerate(files):
            # Save the uploaded file
            file_path = await save_upload_file(file, "product_images")
            
            # Create product image record
            product_image = models.ProductImage(
                product_id=product_id,
                image_url=file_path,
                alt_text=f"{product.name} image {current_images + i + 1}",
                display_order=current_images + i
            )
            
            db.add(product_image)
            
            uploaded_images.append(schemas.ImageUploadResponse(
                image_url=file_path,
                message=f"Image {i + 1} uploaded successfully"
            ))
        
        # If this is the first image and product has no main image, set it
        if not product.image_url and uploaded_images:
            product.image_url = uploaded_images[0].image_url
        
        db.commit()
        
        return uploaded_images
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload product images: {str(e)}"
        )

@router.delete("/products/{product_id}/images/{image_id}")
async def delete_product_image(
    product_id: int,
    image_id: int,
    seller: models.Seller = Depends(get_current_seller),
    db: Session = Depends(get_db)
):
    """Delete a specific product image"""
    # Verify product belongs to seller
    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.seller_id == seller.id
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or access denied"
        )
    
    # Find and delete the image
    image = db.query(models.ProductImage).filter(
        models.ProductImage.id == image_id,
        models.ProductImage.product_id == product_id
    ).first()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    # Delete the file from filesystem
    try:
        file_path = image.image_url.lstrip('/')
        if os.path.exists(file_path):
            os.remove(file_path)
    except:
        pass  # Continue even if file deletion fails
    
    db.delete(image)
    db.commit()
    
    return {"message": "Image deleted successfully"}