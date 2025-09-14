import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from data_manager import data_manager
from utils import (
    is_admin, generate_product_id, get_current_time, 
    validate_coordinates, generate_order_id
)
from config import PRODUCT_CATEGORIES, STAR_RATINGS, DEFAULT_PRICES

logger = logging.getLogger(__name__)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text, photo, and video messages."""
    user_id = update.effective_user.id
    message = update.message
    
    # Handle different types of user input based on context
    user_data = context.user_data
    
    # SPECIFIC STATES FIRST (before general creating_product check)
    
    # Product name input (highest priority during product creation)
    if user_data.get('awaiting_product_name'):
        await handle_product_name_input(update, context)
        return
    
    # Price override input
    if user_data.get('awaiting_price_override'):
        await handle_price_override(update, context)
        return
    
    # Address input for checkout
    if user_data.get('awaiting_address'):
        await handle_address_input(update, context)
        return
    
    # GENERAL STATES LAST
    
    # Product creation flow (only for media uploads, not text input)
    if user_data.get('creating_product'):
        await handle_product_creation_flow(update, context)
        return
    
    # Default response for unhandled messages
    await message.reply_text(
        "🤔 I'm not sure what you're looking for.\n\n"
        "Try using /menu to browse products or /help for available commands."
    )

async def handle_product_creation_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the product creation workflow for admins."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Access denied.")
        return
    
    user_data = context.user_data
    product_data = user_data.get('product_data', {})
    message = update.message
    
    # Step 1: Handle media upload (photo or video)
    if not product_data.get('media_uploaded'):
        if message.photo:
            # Get the highest resolution photo
            photo = message.photo[-1]
            product_data['photo_id'] = photo.file_id
            product_data['media_type'] = 'photo'
            product_data['media_uploaded'] = True
            
            await message.reply_text(
                "📷 Photo received! Now please enter the product name:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ Cancel", callback_data="cancel_product_creation")
                ]])
            )
            
            user_data['awaiting_product_name'] = True
            user_data['product_data'] = product_data
            return
            
        elif message.video:
            product_data['video_id'] = message.video.file_id
            product_data['media_type'] = 'video'
            product_data['media_uploaded'] = True
            
            await message.reply_text(
                "🎥 Video received! Now please enter the product name:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ Cancel", callback_data="cancel_product_creation")
                ]])
            )
            
            user_data['awaiting_product_name'] = True
            user_data['product_data'] = product_data
            return
            
        elif message.animation:  # This handles GIFs
            product_data['animation_id'] = message.animation.file_id
            product_data['media_type'] = 'animation'
            product_data['media_uploaded'] = True
            
            await message.reply_text(
                "🎬 GIF received! Now please enter the product name:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ Cancel", callback_data="cancel_product_creation")
                ]])
            )
            
            user_data['awaiting_product_name'] = True
            user_data['product_data'] = product_data
            return
        
        else:
            await message.reply_text(
                "📷 Please send a photo, video, or GIF of the product first."
            )
            return
    
    # This shouldn't happen as we handle specific steps with flags
    await message.reply_text("❌ Unexpected input in product creation flow.")

async def handle_product_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle product name input during creation."""
    user_data = context.user_data
    product_data = user_data.get('product_data', {})
    
    product_name = update.message.text.strip()
    
    if len(product_name) < 2:
        await update.message.reply_text("❌ Product name must be at least 2 characters long.")
        return
    
    product_data['name'] = product_name
    product_data['original_name'] = product_name
    
    # Show category selection
    text = f"✅ Product name: **{product_name}**\n\nSelect category:"
    
    keyboard = []
    for category in PRODUCT_CATEGORIES:
        if category not in ['🔥 Combos/Deals', '👻 Hidden Menu']:  # Don't allow direct creation in these
            keyboard.append([InlineKeyboardButton(category, callback_data=f"prodcat_{category}")])
    
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_product_creation")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    # Clear the awaiting name flag
    user_data['awaiting_product_name'] = False
    user_data['product_data'] = product_data

async def handle_price_override(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle price override input."""
    user_data = context.user_data
    product_data = user_data.get('product_data', {})
    
    try:
        # Parse price input - expecting format like "eighth:30,quarter:55,half:105,oz:200"
        price_input = update.message.text.strip()
        
        # Try to parse as simple number first (for single-size products)
        if price_input.isdigit():
            price = int(price_input)
            size = product_data.get('default_size', 'unit')
            product_data['prices'] = {size: price}
        else:
            # Parse complex price format
            prices = {}
            for price_pair in price_input.split(','):
                if ':' in price_pair:
                    size, price_str = price_pair.strip().split(':', 1)
                    price = int(price_str.strip())
                    prices[size.strip()] = price
            
            if not prices:
                raise ValueError("No valid prices found")
            
            product_data['prices'] = prices
        
        # Finalize product creation
        await finalize_product_creation(update, context, product_data)
        
    except (ValueError, AttributeError) as e:
        await update.message.reply_text(
            "❌ Invalid price format. Please enter prices like:\n"
            "• Single price: `30`\n"
            "• Multiple sizes: `eighth:30,quarter:55,half:105,oz:200`"
        )

async def handle_address_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle address input during checkout or address management."""
    user_id = update.effective_user.id
    address_text = update.message.text.strip()
    
    if len(address_text) < 10:
        await update.message.reply_text(
            "❌ Please provide a complete address with street, city, and any special instructions."
        )
        return
    
    # Check if this is an address edit operation
    if context.user_data.get('editing_address') is not None:
        address_index = context.user_data['editing_address']
        addresses = data_manager.get_user_addresses(user_id)
        
        if 0 <= address_index < len(addresses):
            # Update existing address
            updated_address = {
                'address': address_text,
                'label': addresses[address_index].get('label', f"Address {address_index + 1}"),
                'created_at': addresses[address_index].get('created_at', get_current_time().isoformat()),
                'updated_at': get_current_time().isoformat()
            }
            
            # Remove old address and add updated one
            data_manager.remove_user_address(user_id, address_index)
            # Insert at same position
            addresses = data_manager.get_user_addresses(user_id)
            addresses.insert(address_index, updated_address)
            
            await update.message.reply_text(
                "✅ **Address Updated Successfully**\n\nYour address has been saved to your account.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📍 View Addresses", callback_data="saved_addresses")],
                    [InlineKeyboardButton("🏠 Back to Menu", callback_data="menu")]
                ])
            )
            
            # Clear editing state
            context.user_data['editing_address'] = None
            context.user_data['awaiting_address'] = False
            return
    
    # Create new address object
    address = {
        'address': address_text,
        'label': f"Address {len(data_manager.get_user_addresses(user_id)) + 1}",
        'created_at': get_current_time().isoformat()
    }
    
    # Try to add address (max 2 addresses per user)
    if data_manager.add_user_address(user_id, address):
        context.user_data['awaiting_address'] = False
        
        # Check if this was for checkout or just saving an address
        if context.user_data.get('in_checkout_flow'):
            # Proceed with checkout using this address
            await create_order_with_address(update, context, address)
        else:
            # Just saving an address
            await update.message.reply_text(
                "✅ **Address Saved Successfully**\n\nYour new address has been added to your account.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📍 View All Addresses", callback_data="saved_addresses")],
                    [InlineKeyboardButton("🏠 Back to Menu", callback_data="menu")]
                ])
            )
    else:
        await update.message.reply_text(
            "❌ Maximum of 2 saved addresses allowed. Please delete an existing address first.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📍 Manage Addresses", callback_data="saved_addresses")]
            ])
        )

async def create_order_with_address(update: Update, context: ContextTypes.DEFAULT_TYPE, address: dict):
    """Create order with the provided address."""
    user_id = update.effective_user.id
    cart_items = data_manager.get_user_cart(user_id)
    
    if not cart_items:
        await update.message.reply_text("❌ Cart is empty!")
        return
    
    # Calculate total
    total_price = sum(item.get('price', 0) * item.get('quantity', 1) for item in cart_items)
    
    # Create order
    order = {
        'order_id': generate_order_id(),
        'user_id': user_id,
        'items': cart_items.copy(),
        'delivery_address': address,
        'total_price': total_price,
        'status': 'pending',
        'created_at': get_current_time().isoformat(),
        'user_info': {
            'first_name': update.effective_user.first_name,
            'username': update.effective_user.username
        }
    }
    
    # Save order and clear cart
    data_manager.add_order(user_id, order)
    data_manager.clear_cart(user_id)
    
    # Send confirmation to user
    order_text = f"""
✅ **Order Confirmed!**

**Order ID:** {order['order_id']}
**Total:** ${total_price}
**Delivery Address:** {address['address']}

**Items:**
"""
    
    for item in cart_items:
        order_text += f"• {item.get('name')} ({item.get('size')}) x{item.get('quantity')} - ${item.get('price')}\n"
    
    order_text += "\n⏳ Waiting for admin confirmation...\n\nYou'll be notified when your order is approved!"
    
    await update.message.reply_text(
        order_text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🛍️ Continue Shopping", callback_data="menu")
        ]])
    )
    
    # Send notification to admins
    await notify_admins_new_order(context, order)
    
    # Ask user about mute preferences
    await show_post_order_mute_options(update, context)

async def notify_admins_new_order(context: ContextTypes.DEFAULT_TYPE, order: dict):
    """Notify all admins about a new order."""
    from config import ADMIN_USER_IDS
    
    admin_text = f"""
🔔 **New Order Received!**

**Order ID:** {order['order_id']}
**Customer:** {order['user_info'].get('first_name')} (@{order['user_info'].get('username', 'N/A')})
**Total:** ${order['total_price']}
**Address:** {order['delivery_address']['address']}

**Items:**
"""
    
    for item in order['items']:
        admin_text += f"• {item.get('name')} ({item.get('size')}) x{item.get('quantity')}\n"
    
    keyboard = [
        [InlineKeyboardButton("✅ Accept Order", callback_data=f"accept_order_{order['order_id']}")],
        [InlineKeyboardButton("❌ Reject Order", callback_data=f"reject_order_{order['order_id']}")],
        [InlineKeyboardButton("📋 View All Orders", callback_data="admin_orders")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    for admin_id in ADMIN_USER_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=admin_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")

async def show_post_order_mute_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show mute options after order placement."""
    text = """
🔇 **Notification Settings**

Would you like to mute alerts for a few days? This helps avoid unnecessary notifications until you're running low again.
"""
    
    keyboard = [
        [InlineKeyboardButton("Mute for 3 days", callback_data="mute_post_order_3")],
        [InlineKeyboardButton("Mute for 7 days", callback_data="mute_post_order_7")],
        [InlineKeyboardButton("Mute for 10 days", callback_data="mute_post_order_10")],
        [InlineKeyboardButton("No thanks, keep alerts on", callback_data="no_mute")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def finalize_product_creation(update: Update, context: ContextTypes.DEFAULT_TYPE, product_data: dict):
    """Finalize the product creation process."""
    try:
        # Generate product ID
        product_id = generate_product_id()
        
        # Set visibility and timestamps
        product_data['visible'] = True
        product_data['created_at'] = get_current_time().isoformat()
        product_data['product_id'] = product_id
        
        # Add to database
        category = product_data['category']
        data_manager.add_product(category, product_id, product_data)
        
        # Success message
        success_text = f"""
✅ **Product Created Successfully!**

**Name:** {product_data['name']}
**Category:** {category}
**Grade:** {product_data['grade']}
**Prices:** {', '.join(f"{k}: ${v}" for k, v in product_data['prices'].items())}

The product is now visible to customers!
"""
        
        await update.message.reply_text(
            success_text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add Another Product", callback_data="admin_add_another")],
                [InlineKeyboardButton("🏠 Back to Admin", callback_data="admin")]
            ])
        )
        
        # Clear user state
        context.user_data.clear()
        
        logger.info(f"Product {product_id} created successfully by admin {update.effective_user.id}")
        
    except Exception as e:
        logger.error(f"Error finalizing product creation: {e}")
        await update.message.reply_text(
            "❌ Error creating product. Please try again.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Back to Admin", callback_data="admin")
            ]])
        )
