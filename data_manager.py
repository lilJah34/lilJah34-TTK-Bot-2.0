# TTK Bot 2.0 - Advanced Data Management System
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from utils import get_current_time, parse_mute_duration, clean_expired_mutes, generate_combo_id
from config import REGIONS, NOTIFICATION_CATEGORIES, MAX_SAVED_ADDRESSES

logger = logging.getLogger(__name__)

class DataManager:
    """Centralized data management for TTK Bot 2.0."""
    
    def __init__(self):
        # Core user data
        self.user_regions: Dict[int, str] = {}
        self.user_cart: Dict[int, List[Dict]] = {}
        self.user_orders: Dict[int, List[Dict]] = {}
        self.user_addresses: Dict[int, List[Dict]] = {}
        
        # Product data - organized by category
        self.fallback_products: Dict[str, Dict[str, Dict]] = {}
        
        # Advanced features
        self.combo_deals: Dict[str, Dict] = {}
        self.hidden_unlocked: Dict[int, bool] = {}  # user_id -> has_access
        
        # Notification system with advanced mute timers
        self.user_notification_settings: Dict[int, Dict] = {}
        
        # Order management
        self.pending_orders: List[Dict] = []
        self.completed_orders: List[Dict] = []
        
        # Fire sale system
        self.fire_sale_active: bool = False
        self.fire_sale_data: Dict = {}
        
        # Admin tools
        self.admin_sessions: Dict[int, Dict] = {}
        
        # Driver tracking
        self.driver_locations: Dict[int, Dict] = {}
        
        # Analytics and metrics
        self.user_metrics: Dict[int, Dict] = {}
        
        # Initialize default data
        self._initialize_default_data()
    
    def _initialize_default_data(self):
        """Initialize default products and settings."""
        # Initialize empty categories
        from config import PRODUCT_CATEGORIES
        for category in PRODUCT_CATEGORIES:
            if category not in self.fallback_products:
                self.fallback_products[category] = {}
    
    # ========================
    # USER REGION MANAGEMENT
    # ========================
    
    def get_user_region(self, user_id: int) -> Optional[str]:
        """Get user's selected region."""
        return self.user_regions.get(user_id)
    
    def set_user_region(self, user_id: int, region_id: str) -> bool:
        """Set user's region."""
        if region_id in REGIONS:
            self.user_regions[user_id] = region_id
            logger.info(f"User {user_id} set region to {region_id}")
            return True
        return False
    
    def get_users_by_region(self, region_id: str) -> List[int]:
        """Get all users in a specific region."""
        return [user_id for user_id, region in self.user_regions.items() if region == region_id]
    
    # ========================
    # CART MANAGEMENT
    # ========================
    
    def get_user_cart(self, user_id: int) -> List[Dict]:
        """Get user's cart items."""
        return self.user_cart.get(user_id, [])
    
    def add_to_cart(self, user_id: int, item: Dict) -> bool:
        """Add item to user's cart."""
        if user_id not in self.user_cart:
            self.user_cart[user_id] = []
        
        # Check if item already exists in cart
        for existing_item in self.user_cart[user_id]:
            if (existing_item.get('product_id') == item.get('product_id') and 
                existing_item.get('size') == item.get('size')):
                # Update quantity
                existing_item['quantity'] = existing_item.get('quantity', 1) + item.get('quantity', 1)
                return True
        
        # Add new item
        self.user_cart[user_id].append(item)
        return True
    
    def remove_from_cart(self, user_id: int, cart_index: int) -> bool:
        """Remove item from cart by index."""
        cart = self.user_cart.get(user_id, [])
        if 0 <= cart_index < len(cart):
            removed_item = cart.pop(cart_index)
            logger.info(f"User {user_id} removed {removed_item.get('name')} from cart")
            return True
        return False
    
    def clear_cart(self, user_id: int) -> bool:
        """Clear user's cart."""
        if user_id in self.user_cart:
            del self.user_cart[user_id]
            logger.info(f"User {user_id} cleared cart")
            return True
        return False
    
    def update_cart_item_quantity(self, user_id: int, cart_index: int, new_quantity: int) -> bool:
        """Update quantity of cart item."""
        cart = self.user_cart.get(user_id, [])
        if 0 <= cart_index < len(cart):
            if new_quantity <= 0:
                return self.remove_from_cart(user_id, cart_index)
            cart[cart_index]['quantity'] = new_quantity
            return True
        return False
    
    # ========================
    # ADDRESS MANAGEMENT
    # ========================
    
    def get_user_addresses(self, user_id: int) -> List[Dict]:
        """Get user's saved addresses."""
        return self.user_addresses.get(user_id, [])
    
    def add_user_address(self, user_id: int, address: Dict) -> bool:
        """Add address to user's saved addresses."""
        if user_id not in self.user_addresses:
            self.user_addresses[user_id] = []
        
        # Limit to max addresses
        if len(self.user_addresses[user_id]) >= MAX_SAVED_ADDRESSES:
            return False
        
        address['added_at'] = get_current_time().isoformat()
        self.user_addresses[user_id].append(address)
        return True
    
    def remove_user_address(self, user_id: int, address_index: int) -> bool:
        """Remove address by index."""
        addresses = self.user_addresses.get(user_id, [])
        if 0 <= address_index < len(addresses):
            addresses.pop(address_index)
            return True
        return False
    
    def update_user_address(self, user_id: int, address_index: int, updated_address: Dict) -> bool:
        """Update existing address."""
        addresses = self.user_addresses.get(user_id, [])
        if 0 <= address_index < len(addresses):
            updated_address['updated_at'] = get_current_time().isoformat()
            addresses[address_index].update(updated_address)
            return True
        return False
    
    # ========================
    # PRODUCT MANAGEMENT
    # ========================
    
    def get_products_by_category(self, category: str) -> Dict[str, Dict]:
        """Get all products in a category."""
        return self.fallback_products.get(category, {})
    
    def get_product(self, category: str, product_id: str) -> Optional[Dict]:
        """Get specific product by ID."""
        return self.fallback_products.get(category, {}).get(product_id)
    
    def add_product(self, category: str, product_id: str, product_data: Dict) -> bool:
        """Add new product."""
        if category not in self.fallback_products:
            self.fallback_products[category] = {}
        
        product_data['created_at'] = get_current_time().isoformat()
        self.fallback_products[category][product_id] = product_data
        logger.info(f"Added product {product_id} to category {category}")
        return True
    
    def update_product(self, category: str, product_id: str, updates: Dict) -> bool:
        """Update existing product."""
        if category in self.fallback_products and product_id in self.fallback_products[category]:
            updates['updated_at'] = get_current_time().isoformat()
            self.fallback_products[category][product_id].update(updates)
            return True
        return False
    
    def update_product_visibility(self, category: str, product_id: str, visible: bool) -> bool:
        """Toggle product visibility."""
        return self.update_product(category, product_id, {'visible': visible})
    
    def delete_product(self, category: str, product_id: str) -> bool:
        """Delete product."""
        if category in self.fallback_products and product_id in self.fallback_products[category]:
            del self.fallback_products[category][product_id]
            logger.info(f"Deleted product {product_id} from category {category}")
            return True
        return False
    
    def search_products(self, query: str, category: str = None) -> List[Tuple[str, str, Dict]]:
        """Search products by name with performance optimization."""
        results = []
        query_lower = query.lower()  # Cache lowered query
        categories_to_search = [category] if category else self.fallback_products.keys()
        
        for cat in categories_to_search:
            category_products = self.fallback_products.get(cat, {})
            # Use dict comprehension for better performance
            for product_id, product in category_products.items():
                if product.get('visible', True):  # Only search visible products
                    product_name = product.get('name', '').lower()
                    if query_lower in product_name:
                        results.append((cat, product_id, product))
        
        # Sort by relevance (exact matches first, then partial)
        results.sort(key=lambda x: (
            x[2].get('name', '').lower().startswith(query_lower) is False,
            x[2].get('name', '')
        ))
        
        return results
    
    # ========================
    # COMBO DEALS SYSTEM
    # ========================
    
    def create_combo_deal(self, combo_data: Dict) -> str:
        """Create new combo deal."""
        combo_id = generate_combo_id()
        combo_data['combo_id'] = combo_id
        combo_data['created_at'] = get_current_time().isoformat()
        combo_data['active'] = True
        
        self.combo_deals[combo_id] = combo_data
        logger.info(f"Created combo deal {combo_id}")
        return combo_id
    
    def get_active_combo_deals(self) -> Dict[str, Dict]:
        """Get all active combo deals."""
        return {cid: combo for cid, combo in self.combo_deals.items() if combo.get('active', True)}
    
    def get_combo_deal(self, combo_id: str) -> Optional[Dict]:
        """Get specific combo deal."""
        return self.combo_deals.get(combo_id)
    
    def update_combo_deal(self, combo_id: str, updates: Dict) -> bool:
        """Update combo deal."""
        if combo_id in self.combo_deals:
            updates['updated_at'] = get_current_time().isoformat()
            self.combo_deals[combo_id].update(updates)
            return True
        return False
    
    def deactivate_combo_deal(self, combo_id: str) -> bool:
        """Deactivate combo deal."""
        return self.update_combo_deal(combo_id, {'active': False})
    
    # ========================
    # HIDDEN MENU ACCESS
    # ========================
    
    def has_hidden_access(self, user_id: int) -> bool:
        """Check if user has hidden menu access."""
        return self.hidden_unlocked.get(user_id, False)
    
    def grant_hidden_access(self, user_id: int) -> bool:
        """Grant hidden menu access to user."""
        self.hidden_unlocked[user_id] = True
        logger.info(f"Granted hidden access to user {user_id}")
        return True
    
    def revoke_hidden_access(self, user_id: int) -> bool:
        """Revoke hidden menu access."""
        if user_id in self.hidden_unlocked:
            del self.hidden_unlocked[user_id]
            logger.info(f"Revoked hidden access from user {user_id}")
            return True
        return False
    
    def get_hidden_access_users(self) -> List[int]:
        """Get all users with hidden access."""
        return list(self.hidden_unlocked.keys())
    
    # ========================
    # NOTIFICATION SYSTEM
    # ========================
    
    def get_user_notification_settings(self, user_id: int) -> Dict:
        """Get user's notification settings."""
        if user_id not in self.user_notification_settings:
            # Initialize default settings
            self.user_notification_settings[user_id] = {
                'muted_categories': {},
                'preferences': {cat: True for cat in NOTIFICATION_CATEGORIES},
                'last_updated': get_current_time().isoformat()
            }
        
        # Clean expired mutes
        settings = self.user_notification_settings[user_id]
        settings['muted_categories'] = clean_expired_mutes(settings.get('muted_categories', {}))
        
        return settings
    
    def mute_notifications(self, user_id: int, category: str, days: int) -> bool:
        """Mute notifications for a category."""
        settings = self.get_user_notification_settings(user_id)
        
        expiry = parse_mute_duration(days)
        settings['muted_categories'][category] = {
            'expires_at': expiry.isoformat(),
            'days': days,
            'muted_at': get_current_time().isoformat()
        }
        
        settings['last_updated'] = get_current_time().isoformat()
        logger.info(f"User {user_id} muted {category} for {days} days")
        return True
    
    def unmute_notifications(self, user_id: int, category: str = None) -> bool:
        """Unmute notifications (specific category or all)."""
        settings = self.get_user_notification_settings(user_id)
        
        if category:
            if category in settings['muted_categories']:
                del settings['muted_categories'][category]
                logger.info(f"User {user_id} unmuted {category}")
        else:
            settings['muted_categories'] = {}
            logger.info(f"User {user_id} unmuted all notifications")
        
        settings['last_updated'] = get_current_time().isoformat()
        return True
    
    def is_category_muted(self, user_id: int, category: str) -> bool:
        """Check if notification category is muted for user."""
        settings = self.get_user_notification_settings(user_id)
        mute_data = settings.get('muted_categories', {}).get(category)
        
        if not mute_data:
            return False
        
        # Check if mute has expired
        from utils import is_muted
        return is_muted(mute_data)
    
    def get_notification_recipients(self, category: str, region: str = None) -> List[int]:
        """Get users who should receive notifications for a category."""
        recipients = []
        
        for user_id in self.user_regions.keys():
            # Check region filter
            if region and self.get_user_region(user_id) != region:
                continue
            
            # Check if category is muted
            if not self.is_category_muted(user_id, category):
                recipients.append(user_id)
        
        return recipients
    
    def add_notification_request(self, user_id: int, category: str) -> bool:
        """Add user to notification list for a category."""
        settings = self.get_user_notification_settings(user_id)
        
        if 'category_requests' not in settings:
            settings['category_requests'] = {}
        
        settings['category_requests'][category] = {
            'requested_at': get_current_time().isoformat(),
            'active': True
        }
        
        settings['last_updated'] = get_current_time().isoformat()
        logger.info(f"User {user_id} requested notifications for {category}")
        return True
    
    # ========================
    # ORDER MANAGEMENT
    # ========================
    
    def add_order(self, user_id: int, order: Dict) -> bool:
        """Add new order."""
        if user_id not in self.user_orders:
            self.user_orders[user_id] = []
        
        self.user_orders[user_id].append(order)
        
        # Add to pending orders
        self.pending_orders.append(order)
        
        logger.info(f"Added order {order.get('order_id')} for user {user_id}")
        return True
    
    def get_user_orders(self, user_id: int) -> List[Dict]:
        """Get user's order history."""
        return self.user_orders.get(user_id, [])
    
    def get_pending_orders(self) -> List[Dict]:
        """Get all pending orders."""
        return [order for order in self.pending_orders if order.get('status') == 'pending']
    
    def update_order_status(self, order_id: str, new_status: str, admin_id: int = None) -> bool:
        """Update order status."""
        # Find and update order in user orders
        for user_id, orders in self.user_orders.items():
            for order in orders:
                if order.get('order_id') == order_id:
                    order['status'] = new_status
                    order['status_updated_at'] = get_current_time().isoformat()
                    if admin_id:
                        order['admin_id'] = admin_id
                    
                    # If approved, mark as paid
                    if new_status == 'approved':
                        order['payment_status'] = 'paid'
                        order['approved_at'] = get_current_time().isoformat()
                    
                    # Move to completed if finished
                    if new_status in ['completed', 'delivered']:
                        self.completed_orders.append(order)
                        if order in self.pending_orders:
                            self.pending_orders.remove(order)
                    
                    logger.info(f"Order {order_id} status updated to {new_status}")
                    return True
        
        return False
    
    def get_order_by_id(self, order_id: str) -> Optional[Dict]:
        """Get order by ID."""
        for orders in self.user_orders.values():
            for order in orders:
                if order.get('order_id') == order_id:
                    return order
        return None
    
    # ========================
    # FIRE SALE SYSTEM
    # ========================
    
    def start_fire_sale(self, products: List[Dict], discount_percent: int, duration_hours: int, admin_id: int) -> bool:
        """Start fire sale."""
        self.fire_sale_active = True
        self.fire_sale_data = {
            'products': products,
            'discount_percent': discount_percent,
            'duration_hours': duration_hours,
            'started_at': get_current_time().isoformat(),
            'expires_at': (get_current_time() + timedelta(hours=duration_hours)).isoformat(),
            'started_by': admin_id
        }
        
        logger.info(f"Fire sale started by admin {admin_id} for {duration_hours} hours")
        return True
    
    def end_fire_sale(self, admin_id: int) -> bool:
        """End fire sale."""
        if self.fire_sale_active:
            self.fire_sale_active = False
            self.fire_sale_data['ended_at'] = get_current_time().isoformat()
            self.fire_sale_data['ended_by'] = admin_id
            logger.info(f"Fire sale ended by admin {admin_id}")
            return True
        return False
    
    def is_fire_sale_active(self) -> bool:
        """Check if fire sale is currently active."""
        if not self.fire_sale_active:
            return False
        
        # Check expiration
        expires_at_str = self.fire_sale_data.get('expires_at')
        if expires_at_str:
            try:
                expires_at = datetime.fromisoformat(expires_at_str)
                if get_current_time() > expires_at:
                    self.fire_sale_active = False
                    return False
            except ValueError:
                pass
        
        return True
    
    def get_fire_sale_data(self) -> Dict:
        """Get current fire sale data."""
        return self.fire_sale_data if self.is_fire_sale_active() else {}
    
    # ========================
    # USER METRICS & ANALYTICS
    # ========================
    
    def track_user_action(self, user_id: int, action: str, data: Dict = None):
        """Track user action for analytics."""
        if user_id not in self.user_metrics:
            self.user_metrics[user_id] = {
                'first_seen': get_current_time().isoformat(),
                'actions': [],
                'total_orders': 0,
                'total_spent': 0.0
            }
        
        action_record = {
            'action': action,
            'timestamp': get_current_time().isoformat(),
            'data': data or {}
        }
        
        self.user_metrics[user_id]['actions'].append(action_record)
        
        # Update specific metrics
        if action == 'order_completed':
            self.user_metrics[user_id]['total_orders'] += 1
            if data and 'total_price' in data:
                self.user_metrics[user_id]['total_spent'] += data['total_price']
    
    def get_user_metrics(self, user_id: int) -> Dict:
        """Get user metrics."""
        return self.user_metrics.get(user_id, {})
    
    def get_platform_metrics(self) -> Dict:
        """Get overall platform metrics."""
        total_users = len(self.user_regions)
        total_orders = sum(len(orders) for orders in self.user_orders.values())
        total_revenue = sum(
            sum(order.get('total_price', 0) for order in orders)
            for orders in self.user_orders.values()
        )
        
        active_users_7d = len([
            uid for uid, metrics in self.user_metrics.items()
            if any(
                (get_current_time() - datetime.fromisoformat(action['timestamp'])).days <= 7
                for action in metrics.get('actions', [])
            )
        ])
        
        return {
            'total_users': total_users,
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'active_users_7d': active_users_7d,
            'pending_orders': len(self.get_pending_orders()),
            'total_products': sum(len(products) for products in self.fallback_products.values()),
            'regions': list(REGIONS.keys()),
            'last_updated': get_current_time().isoformat()
        }
    
    # ========================
    # DATA PERSISTENCE (BASIC)
    # ========================
    
    def save_to_file(self, filename: str = 'ttk_bot_data.json'):
        """Save all data to JSON file with performance optimization."""
        import tempfile
        import shutil
        
        data = {
            'user_regions': self.user_regions,
            'user_cart': self.user_cart,
            'user_orders': self.user_orders,
            'user_addresses': self.user_addresses,
            'fallback_products': self.fallback_products,
            'combo_deals': self.combo_deals,
            'hidden_unlocked': self.hidden_unlocked,
            'user_notification_settings': self.user_notification_settings,
            'fire_sale_data': self.fire_sale_data,
            'fire_sale_active': self.fire_sale_active,
            'user_metrics': self.user_metrics,
            'last_saved': get_current_time().isoformat()
        }
        
        try:
            # Use atomic write operation for data safety
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.tmp') as temp_file:
                json.dump(data, temp_file, indent=2, separators=(',', ':'))  # Compact JSON
                temp_filename = temp_file.name
            
            # Atomic move to final location
            shutil.move(temp_filename, filename)
            logger.info(f"Data saved to {filename} (atomic write)")
            return True
        except Exception as e:
            logger.error(f"Failed to save data: {e}")
            # Clean up temp file if it exists
            try:
                if 'temp_filename' in locals():
                    import os
                    os.unlink(temp_filename)
            except:
                pass
            return False
    
    def load_from_file(self, filename: str = 'ttk_bot_data.json'):
        """Load data from JSON file."""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            # Convert string keys back to int where needed
            self.user_regions = {int(k): v for k, v in data.get('user_regions', {}).items()}
            self.user_cart = {int(k): v for k, v in data.get('user_cart', {}).items()}
            self.user_orders = {int(k): v for k, v in data.get('user_orders', {}).items()}
            self.user_addresses = {int(k): v for k, v in data.get('user_addresses', {}).items()}
            self.fallback_products = data.get('fallback_products', {})
            self.combo_deals = data.get('combo_deals', {})
            self.hidden_unlocked = {int(k): v for k, v in data.get('hidden_unlocked', {}).items()}
            self.user_notification_settings = {int(k): v for k, v in data.get('user_notification_settings', {}).items()}
            self.fire_sale_data = data.get('fire_sale_data', {})
            self.fire_sale_active = data.get('fire_sale_active', False)
            self.user_metrics = {int(k): v for k, v in data.get('user_metrics', {}).items()}
            
            logger.info(f"Data loaded from {filename}")
            return True
        except FileNotFoundError:
            logger.info(f"No existing data file found: {filename}")
            return False
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            return False

# Global data manager instance
data_manager = DataManager()